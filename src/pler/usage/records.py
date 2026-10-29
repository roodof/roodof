"""One shape for every agent's sessions: who, where, when, which models, and what each model call reported.

Only numbers and metadata are kept. Prompt text, replies, tool output and command lines never leave the
parsers; from tool calls only the tool name and, for file edits, the edited path are kept.

Token fields are disjoint, so they add up to the session total:
- input: input that was neither read from nor written to the prompt cache
- cache_read, cache_write: cached input read / written
- output: generated tokens, reasoning included
- reasoning: the reasoning part of output (already inside output; never added again)
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import math
import json
import re
from .input_limits import MAX_JSON_DEPTH

TOKEN_FIELDS = ('input', 'cache_read', 'cache_write', 'output', 'reasoning')
ADDED = ('input', 'cache_read', 'cache_write', 'output')


def note_file_issue(issues, path, reason):
    """One affected-file count, even when several bad rows or an I/O error occur."""
    if issues is not None and not any(name == str(path) for name, _ in issues):
        issues.append((str(path), reason))


_STRINGS = re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"', re.S)
_BRACKETS = re.compile(r'[\[\]{}]')


def _too_deep(line):
    """Nesting depth outside JSON strings. The regexes skip string bodies in C; only structural brackets
    reach Python, so lines full of quoted code braces stay cheap."""
    depth = 0
    for char in _BRACKETS.findall(_STRINGS.sub('', line)):
        if char in '{[':
            depth += 1
            if depth > MAX_JSON_DEPTH:
                return True
        else:
            depth -= 1
    return False


def json_row(line):
    def invalid(_):
        raise ValueError('invalid JSON constant')
    if line.count('{')+line.count('[')>MAX_JSON_DEPTH and _too_deep(line):
        raise ValueError('over-nested log row')
    try:
        row = json.loads(line, parse_constant=invalid)
    except RecursionError as error:
        raise ValueError('over-nested log row') from error
    if not isinstance(row, dict):
        raise ValueError('log row is not an object')
    return row


def percentage(value):
    """A usable meter percentage; reject booleans, NaN, infinities and out-of-range values."""
    try:
        return float(value) if type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 100 else None
    except OverflowError:
        return None


def empty_tokens():
    return dict.fromkeys(TOKEN_FIELDS, 0)


def total(tokens):
    return sum(tokens[name] for name in ADDED)


def add_tokens(into, tokens):
    for name in TOKEN_FIELDS:
        into[name] += tokens.get(name) or 0


def timestamp(value):
    """ISO-8601 (with Z or offset) or epoch seconds/milliseconds -> aware UTC datetime; None if unreadable."""
    try:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return datetime.fromtimestamp(value / 1000 if value > 1e11 else value, timezone.utc)
        if isinstance(value, str) and value:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None
    return None


@dataclass
class Session:
    agent: str                      # 'claude-code' or 'codex'
    session_id: str
    source: str                     # log file it was read from
    project: str = None             # working directory as logged
    branch: str = None
    parent_id: str = None           # a subagent's parent session
    started: datetime = None
    ended: datetime = None
    client_version: str = None
    calls: int = 0                  # model calls with reported usage
    prompts: int = 0                # user turns
    active_ms: int = None           # agent-reported working time, when logged
    tokens: dict = field(default_factory=empty_tokens)
    models: dict = field(default_factory=dict)      # model -> calls
    model_tokens: dict = field(default_factory=dict)  # model -> total tokens of its calls
    efforts: dict = field(default_factory=dict)     # reasoning effort -> turns or calls
    tools: dict = field(default_factory=dict)       # tool name -> calls
    files_edited: set = field(default_factory=set)
    errors: int = 0                 # failed model calls or turns
    aborted: int = 0                # interrupted turns
    reported_cost_usd: float = None # the agent's own figure, when it logs one
    quota: list = field(default_factory=list)       # (time, window_minutes, used_percent[, resets_at]) samples
    quota_plan: str = None
    quota_events: dict = field(default_factory=dict)  # limit status -> count, when no percent is logged
    limit_hits: list = field(default_factory=list)  # times a request was refused at the limit (Claude Code)
    notes: list = field(default_factory=list)       # how the numbers were obtained
    tokens_complete: bool = True
    calls_complete: bool = True
    counts_complete: bool = True
    attribution_complete: bool = True
    models_complete: bool = True
    issues: set = field(default_factory=set)       # fixed reason codes, never excerpts or private paths
    source_state: str = 'live'
    source_deleted: bool = False
    archive_files: int = 0
    archive_old_parser: bool = False
    archive_unverified: bool = False

    def source_evidence(self,source,state='live',deleted=False,old=False,unverified=False):
        """Computed scan provenance. Never persisted as a Session snapshot."""
        evidence=getattr(self,'_sources',{})
        value=dict(state=state,deleted=deleted,old=old,unverified=unverified)
        if evidence.get(source)==value: return  # repeated for every reply/owner merge; keep it linear
        evidence[source]=value
        self._sources=evidence
        states={value['state'] for value in evidence.values()}
        self.source_state='mixed' if len(states)>1 else next(iter(states))
        self.source_deleted=any(value['deleted'] for value in evidence.values())
        self.archive_files=sum(value['state']=='archive' for value in evidence.values())
        self.archive_old_parser=any(value['old'] for value in evidence.values())
        self.archive_unverified=any(value['unverified'] for value in evidence.values())
        if self.archive_old_parser:
            self.issues.add('archive_old_parser');self.tokens_complete=False
        if self.archive_unverified:
            self.issues.add('archive_unverified');self.tokens_complete=False

    def count(self, table, key, step=1):
        if key:
            table[key] = table.get(key, 0) + step

    def seen(self, moment):
        if moment is None:
            return
        if self.started is None or moment < self.started:
            self.started = moment
        if self.ended is None or moment > self.ended:
            self.ended = moment

    def note(self, text):
        if text not in self.notes:
            self.notes.append(text)

    def as_dict(self):
        value = asdict(self)
        value['files_edited'] = sorted(self.files_edited)
        value['issues'] = sorted(self.issues)
        value['total_tokens'] = total(self.tokens)
        for name in ('started', 'ended'):
            value[name] = value[name].isoformat() if value[name] else None
        value['quota'] = [[sample[0].isoformat(), sample[1], sample[2]] + ([sample[3].isoformat() if sample[3] else None]
                                                                          if len(sample) > 3 else []) for sample in self.quota]
        value['limit_hits'] = [moment.isoformat() for moment in self.limit_hits]
        return value
