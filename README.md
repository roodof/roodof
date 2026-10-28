# PLER

**English** · [Türkçe](README.tr.md)

See what Claude Code and Codex used, from their own logs on your computer: tokens by project and model, where your subscription quota is heading, and where usage builds up.

- **Calls no model.** Measuring costs zero tokens.
- **Sends nothing.** No network access; the page opens on this computer only (`127.0.0.1`).
- **Agent logs stay unchanged.** PLER keeps a metadata cache; prompts, replies, commands and tool output never reach the page or the cache. The optional status line changes Claude Code settings only after confirmation and keeps a backup.
- **Any programming language.** It reads agent logs and local Git activity metadata, not source code.

## Install

Python 3.9 or newer; no other dependencies.

From the outer project folder:

```
pipx install ./product
```

`pip install ./product` works too. (Once published on PyPI: `pipx install pler`.)
If you are already inside `product/`, use `pipx install .` instead.

## Use

```
pler
```

Opens the **My usage** page in your browser. Stop it with the page's **Close** button or Ctrl+C in the terminal.

For a manually opened tab, use the complete address printed at startup. It grants access to that running report and changes after restart; do not share it. The page removes the access fragment from the visible address. Direct report/API reads and downloads require the same credential. This is a personal local application; team accounts and shared-server deployment are not supported.

```
pler report             # sessions active in the last 30 days
pler report --days 0    # all records
pler report --json      # machine-readable
```

**Language:** the page follows your browser and has an English / Türkçe switch at the top. The terminal speaks Turkish on a Turkish system and English elsewhere; choose with `PLER_LANG=en` or `PLER_LANG=tr`.

## What it shows

- **Your situation:** observations from your logs, each with the numbers behind it. For example, how many times more tokens each model call uses in long sessions than in short ones, or that most of the usage sits in a single session.
- **Quota:** where the 5-hour and weekly quotas of Codex and Claude Code were last, and whether they fill before they reset at the current pace. Claude Code needs the [status line](#claude-code-quota) turned on once.
- **Totals:** the token mix: new input, read from cache, written to cache, and output. Tokens outside the cache are shown separately, because most agent tokens are the same context read again.
- **Projects, models, sessions:** sessions are grouped by git repository; sessions in temporary folders form one group.
- **Find your sessions:** search by project, model or short session code; sort by last activity, start, tokens, or errors and interruptions. Each row has its own code, start and last activity.
- **Git alongside the session:** open a session to see local commit, amend, checkout, reset, merge and rebase events recorded during its time span. No Git program runs. Events can overlap several sessions and do not identify who made a change or prove it was kept.

![Session search and sorting, with invented sample data](docs/sessions.jpg)

Search narrows only the session list. The summary at the top and the downloaded JSON follow the period / agent / project selection.

While preparing a summary, the download button shows its progress. A **Download again** link remains available for that prepared file. Check your browser downloads to confirm it was saved. Changing the main filters or explicitly reading logs again clears the old link. On a narrow screen, focus the session table and use the left/right arrow keys to reach the other columns.

A session's **record span** is the time between its first and last event, waiting included. **Working time** is shown only when the agent logged it. The number of edited files does not prove that changes were kept in git or that the work was finished.

**Data quality:** copied responses are reconciled before totals are assigned. Missing or conflicting model/project attribution is shown as unknown. Invalid records and unresolved cumulative/fork/compaction history are flagged; the displayed total may be incomplete. A known total does not prove complete account usage. JSON includes app/parser/schema versions and quality flags. See the [accounting contract](ACCOUNTING.md) before using an export for a decision. Session-length comparisons do not establish waste or savings.

## Local Git activity

On **Read logs again**, PLER also checks `.git/logs/HEAD` in projects already named by the agent logs. Linked worktrees and submodules with a `gitdir` file are supported. This is a snapshot: changing filters does not re-read Git files.

Only event time, a fixed action category and the first eight characters of the destination commit are sent to the page and JSON. Author names, email addresses, commit messages, branch names, source files and Git configuration are not included. No Git metadata is added to the persistent cache.

Local reflogs can expire, be disabled or be absent in a copied checkout. At most the last 1 MiB of each project's HEAD log is read; the newest 20 matching events are listed and the count covers all matching events in that read. Missing dates, unavailable history and partial coverage are shown explicitly. A zero count means no matching event was found in the available local log, not that no work was done. Network paths, symlinks, Windows junctions and home-folder repositories are skipped. Bare repositories and activity from other worktrees are not included.

## Claude Code quota

Claude Code does not write its quota percentage to its logs, but on Pro and Max plans it passes it to its status line. Run once:

```
pler statusline --install
```

- **What happens:** you see the line that will be added to Claude Code's `settings.json` and are asked to confirm. A backup of the file is made first.
- **If you already have a status line:** it is left alone, and you are shown how your own script can pass the data to PLER.
- **Afterwards:** Claude Code's status line shows something like `ctx 37% · 5h 24% · week 41%`. PLER keeps only the quota percentages and reset times, when they change, in its cache folder; no conversation, folder or session information.
- **On the page:** the Claude Code quota appears with the same "when does it fill" forecast as Codex.
- **To undo:** `pler statusline --remove`

Only the exact, unmodified line generated by the current PLER installation is removed. A custom wrapper, an edited line or a command pointing to another installation is left alone. Settings changed while confirmation is pending are not overwritten; retry after checking them.

## What it reads

| Agent | Folder | To change |
|---|---|---|
| Claude Code | `~/.claude/projects`, `~/.config/claude/projects` | `CLAUDE_CONFIG_DIR` |
| Codex | `~/.codex/sessions`, `~/.codex/archived_sessions` (compressed ones included) | `CODEX_HOME` |

Codex's compressed logs are read without installing anything. On Python 3.14 or newer the standard library decompresses them quickly. On older Python, `pip install "pler[fast]"` gives the same speed. Without either, the built-in decoder works but is slower: on one test computer the first read took 23 seconds instead of 7. Later reads use the cache.

The dependency-free reader avoids repeated checkpoint comparisons and writes metadata caches in one encoded document. Large cold reads still take time; the [recorded performance checks](../reports/cold-start-v1/REPORT.md) distinguish an empty PLER cache from later cached reads.

Metadata extracted from unchanged Claude Code and Codex logs is kept in a cache, so later reads do not reparse the original conversations. The cache holds counts, timestamps, identifiers, project paths and tool metadata; no prompt, reply, command or tool output text. It is private local metadata, not an anonymous file. Location:
- Windows: `%LOCALAPPDATA%\pler`
- macOS: `~/Library/Caches/pler`
- Linux: `~/.cache/pler`

`PLER_CACHE_DIR` moves it. If deleted, it is rebuilt on the next start.
Damaged or older cache entries are re-read from the original log. The checksum detects accidental changes; it is not protection against someone who can edit both the cache and checksum.
An update that changes a reader or its validation helpers rebuilds the affected cache on its next read. Logs that grow during reading or fail partway through access are retried on the next read. A failed cache replacement leaves the previous cache intact and removes the temporary file when permitted.

## Trust and data quality

The page shows a dated snapshot. PLER withholds forecasts from samples older than 30 minutes for short windows and 24 hours for day-long or weekly windows. These are PLER's conservative freshness limits, not provider rules. An elapsed reset or a forecast deadline that has already passed makes the current level unknown. An open page updates those labels from its clock without fetching an account or reading logs again.

Claude Code and Codex files that cannot be fully read are counted. Valid rows are retained when a file contains broken JSON, invalid record identities or an unfinished last line; the totals are marked as potentially incomplete. The warning persists when either agent's file is served from cache. A directory with no records is distinguished from an incomplete read. Malformed quota numbers are discarded. A file count is discovery coverage; it is not proof that every transcript line was valid or that every agent version is supported.

Compressed Codex files must have complete frames and matching declared sizes. Present zstd content checksums are verified by the built-in decoder. A damaged compressed file is excluded and reported, because its decoded bytes cannot be trusted. Files without checksums cannot detect every data change. UNC project paths and symlink/junction ancestors are not followed while grouping projects or reading Git metadata.

Repeated Claude prompts and tool calls are counted once when the logs supply stable IDs. Without those IDs, separate records cannot reliably be identified as copies.

Token use is not a price or a measured saving. Neither the page export nor `pler report --json --sessions` includes source file paths, raw session IDs, branch names, edited file paths or arbitrary log notes. They still contain shortened project names, times, model names and counts; they are not anonymous sharing files. Detailed terminal JSON now uses the page's session allowlist. It no longer has a `days` series: periods select active sessions and include each selected session's full totals, not daily spending.

For an update from this checkout, close PLER, run `pip install --upgrade ./product` from the outer folder, then reopen it. `pler --version` identifies the installed release. A running page keeps the assets it started with; restart PLER to use updated code. Release and JSON changes are listed in the [changelog](CHANGELOG.md).

The [quality register](QUALITY.md) separates fixed defects from unresolved reasons to reject the product. Automated tests pass on Windows, Linux and macOS with Python 3.9 to 3.14. A signed Python-free installation, real-browser acceptance on each system and proven usefulness in professionals' daily work remain open.

## Limits

- Claude Code does not log its quota percentage. Without the status line, only the number of limit refusals is shown. With it, the quota is the value at the moments Claude Code runs; using Claude elsewhere (web, desktop) uses the same quota and shows up at the next Claude Code reply.
- The status line is a feature of Claude Code in the terminal. It is not confirmed that the Claude desktop app runs it; in a test, no sample arrived from it within 15 minutes.
- The account quota does not depend on the project and agent filters. No recorded limit event does not mean the remaining quota is known.
- No money amounts are shown; the numbers are the tokens the agents logged.
- The observations under "Your situation" come from your logs; they are not the result of a controlled experiment.

## Checking the promises

[tests/test_trust.py](tests/test_trust.py) checks that:
- the source imports no module that can open a connection or start a program;
- a whole session talks only to `127.0.0.1` and starts no program;
- no log text reaches the page or the cache.

[tests/test_i18n.py](tests/test_i18n.py) checks that English and Turkish have the same entries and placeholders, and that every word the code and the page use exists in both.

```
python -m pytest
```
