# Retained-log accounting contract — schema 2

PLER 0.2.16 describes the local agent records it can read. It does not reconcile a provider bill, prove complete account coverage or measure task quality. Periods select sessions by last activity and include their full retained totals.

## API list-price equivalent (0.2.16)

Each accepted response is priced once, with the response's own model and the provider's public standard-tier list price of 30 October 2026 (Anthropic and OpenAI pricing pages; the table is fixed in `pricing.py`). The price is per million tokens for input, cache reads, cache writes and output. Reasoning is already part of output.

- **Tiers:** a tier is chosen by the response's own prompt (input + cache reads + cache writes). For example, OpenAI's long-context price applies above 272,000 tokens and Claude Haiku 5.5's above 100,000.
- **Claude cache writes:** priced by the logged 1-hour/5-minute split. When the split is absent, the API default of 5 minutes applies.
- **Codex:** logs no service tier, so the standard tier is assumed. Codex cache writes are input tokens at the input price.
- **Unpriced:** a response is left unpriced, but stays in the token totals, when:
  - its model has no published price;
  - its prompt exceeds the largest covered tier;
  - Claude logged a non-standard speed or US-only inference;
  - its usage exists only as a cumulative total.

  The page shows the priced share of tokens.
- **Not a bill:** the figure is not a bill, a saving or a subscription value. Agents also send requests they do not write to their transcripts, such as context compaction or helper calls. On one real computer, Claude Code's own running figure for a session's latest process was 3–4% higher than PLER's for the same session, so the equivalent can be a few percent low.

## Reader resources and lifecycle (0.2.15)

Raw JSONL is read in chunks; a line is limited to 8 MiB and JSON containers to 256 levels (brackets inside strings are not nesting). Each source is limited to 512 MiB input and expanded output; the zstd window is limited to 128 MiB. Native decoders stream bounded chunks and check every frame, including concatenated/skippable frames and truncation. The plain-Python fallback uses bounded whole buffers and checks growth before allocation; it is not a constant-memory streaming decoder.

Per-file projected metadata is limited to 200,000 rows and 64 MiB serialized metadata. One scan admits at most 500,000 projected rows / 256 MiB serialized metadata, 2 GiB source bytes, 4 GiB expanded bytes, 20,000 matching files and 100,000 directories. The rebuildable cache read is capped at 256 MiB per agent. These are explicit input/admission limits, not a hard process RSS or elapsed-time guarantee. A limit excludes records with incomplete coverage and a fixed warning, never an assertion of complete zero usage. Partial root enumeration cannot establish that an archived source was deleted.

One background scan worker coalesces forced refreshes into one latest pending request. Cancellation is checked between filesystem/decoder/metadata/Git phases; a blocked OS call cannot be forcibly interrupted. Closing stops new scans and waits at most one second for the worker and snapshot lock. Local HTTP permits at most eight handlers, with five-second idle and fifteen-second total connection deadlines (plus accept-loop polling granularity); existing origin/access checks still apply.

Quota journal writers share a bounded local OS lock across deduplication, append and pruning. Reads use a bounded 4 MiB tail, rows at most 2 KiB, and at most 8,192 retained sample rows; pruning keeps at most 1 MiB. Status-line stdin is capped at 1 MiB. The journal is sampled local history, not a complete account ledger. Archive writes flush and fsync before atomic replacement; POSIX also syncs directory changes. A post-replacement sync failure is reported as a failure without claiming rollback. No recovery backup or hardware power-loss guarantee is established.

## Identity and copies

### Dated usage and comparable observations (0.2.13)

These rules are fixed before measuring new real-data results. The existing active-session selection and whole-session totals remain available and unchanged in meaning.

- **Dated usage:** count only accepted, stable-ID per-response usage with exactly one unambiguous aware timestamp among copies carrying the selected actual snapshot. Use UTC and the scan's fixed observation time: `since <= response_time <= cutoff`. Missing, naive, contradictory or future timestamps cannot be allocated to a period. Do not split a cumulative residual across dates or use a session's end as the response time.
- **Coverage:** exclude old/unverified archive evidence, uncertain history and incomplete usage/attribution from dated claims, with reason counts. Show the number of sessions with unallocated retained usage. A dated sum describes recorded responses; it never proves complete account coverage. Keep raw paths, native IDs and individual usage events out of this projection.
- **Comparable session-length observations:** compare only the same agent, known project and single known model, with complete token/call/model/attribution evidence. Keep the existing call boundaries (short: under 50, long: at least 100; each session at least 5 calls) and ratio threshold 2, but require at least three sessions on each side. Tasks and settings are still uncontrolled; no causal, savings or quality claim follows.
- **Quota scope:** exact copies of meter samples are deduplicated. Conflicting samples or decreases before a known reset withhold both the current percentage and forecast. This detects inconsistent history, not account identity. Compatible records do not prove a single account.

**Corrected after the first real-data check (29 October 2026).** Two of these rules failed on one user's real logs and were changed before release; the counts below are from that check.

- *Quota:* the real Codex meter is not monotonic. Within one window the 5-hour level fell by 1 point 622 times and by at most 11; the provider also restarted windows early (a later reset with a lower level). The original rule hid both real Codex windows. A contradiction is now a reset moving back to an earlier time while its window is active, a fall of more than 25 points within a window, or different readings at the same instant.
- *Dated usage:* Claude Code writes each content block of a response as its own row with the same usage and its own time; 75% of real responses had such copies, seconds apart (90th percentile 14 s). A response is now dated by its earliest and latest copy: it counts when both fall in the interval, and stays undated when they straddle the start. A copy without an aware time still leaves it undated.
- *Display:* even after this, 23 of 29 real sessions were excluded for incomplete usage or ownership, and the last seven days had no dated tokens beside 1.5 billion whole-session tokens. The page and terminal therefore show dated usage only when every selected session's usage could be dated; the JSON export always carries it with its coverage counts.

### Contributing quota source groups (0.2.14)

Quota history from more than one contributing selected local source group is withheld even when its samples appear compatible. Conventional Codex `sessions` and `archived_sessions` folders under one home count as one source group; Claude `projects` is grouped by its configuration home. Only live or replayed source paths already selected by the reader contribute. Empty selected roots do not count. WSL host aliases are normalized lexically while Linux path case is retained. The exported count/reason contains no local root or provider account identity. A single source group does not prove a single account; account switches inside one group remain outside verified account coverage.

### Preregistered subsequent-edit observation (0.2.12)

These rules are fixed before inspecting any real subsequent-edit result. They describe logged edit intentions, not successful changes, waste, savings, causality or code quality.

- **Window and clock:** exactly 7 × 24 hours (604,800 seconds), in UTC. The gap is `later.started - origin.ended`; a match requires `0 < gap <= 604800`. This is a gap between recorded session boundaries, not the elapsed time between two file edits. Missing, reversed or future spans are excluded. The cutoff is the successful scan's recorded observation time, not a later page-render clock.
- **Same target:** at least one identical normalized absolute target occurs in both sessions' existing edited-target sets. Windows drive-absolute targets use Windows path normalization and case folding on every viewing OS. POSIX absolute targets use POSIX normalization and preserve case. Relative targets resolve against the working directory at that edit record. Unresolved relative, drive-relative, network/device and ambiguous rooted spellings are excluded. No filesystem, Git tree, source content or file-existence query is used for this calculation.
- **Independence:** native-session copies are reconciled first. Parent/child, sibling and response-sharing histories form one internal related group and cannot match each other. Contradictory, cyclic or missing-parent lineage is excluded when independence cannot be established. Separate Claude subagent histories without trustworthy parent evidence are excluded conservatively. A project-attribution conflict alone does not prove two histories related.
- **Archive coverage:** current-reader, verified missing-source archive metadata may contribute. Unverified sources and older-reader archive metadata are excluded from this observation, with coverage counts. No missing edited targets are reconstructed.
- **Selection and follow-up:** the full timeline from the explicitly selected log roots supplies later evidence; period/agent/project filters select origin sessions only. A later session may therefore use another agent. An unmatched origin less than seven days old is follow-up pending. Older unmatched origins mean only that no qualifying later edit was observed in the retained records. No percentage or population-wide repeat-work rate is claimed.
- **Counting and display:** each origin session counts at most once, even when several targets match. Keep its earliest qualifying later session. Display at most five matches, ordered by gap and then deterministic opaque session IDs. Report the source/later agents and whole-session recorded token counts with completeness flags; those counts are not the cost of the repeated edits. Do not derive token ratios or savings from incomplete usage or attribution.
- **File identity limits:** Windows paths, WSL mount aliases, user links and other spellings remain distinct unless lexically equivalent. A move can hide continuity; deleting and recreating the same path can suggest continuity without preserving file identity. Add/delete/move patch headers and failed edit attempts are still logged target intentions. Overlapping or equal-boundary sessions are excluded rather than assigned an invented order.

The real-data comparison will publish only aggregate counts and token/time summaries. It will compare this observation's information with the existing branch-reachability observation without changing these definitions after seeing the results.

### Retained identities and copies

- Codex files with the same native session ID form one accounting group. A response ID is counted once across retained files. Claude replies use the message/request ID pair. Prompt UUIDs, turn IDs and tool-call IDs deduplicate their respective events.
- Repeated usage snapshots are compatible only when one actual logged snapshot is at least as large in every token component as every other snapshot. That actual snapshot is retained. Crossing updates are excluded from the known total and flagged; PLER never manufactures a snapshot from component maxima.
- Conflicting project metadata becomes unknown. A response copied into different sessions has uncertain ownership. A stable native-ID ordering supplies an internal aggregation anchor, with an explicit attribution warning; it does not prove authorship. If the original projects differ, the anchor's project becomes unknown. This can conservatively move other usage in that accounting group into the unknown project bucket.
- Records without stable identities cannot prove deduplication. Anonymous response usage remains visible but is marked incomplete. Codex anonymous event metadata is matched by fingerprint and occurrence within related histories; its counts remain unverified. Unrelated histories are not collapsed by similar text or timestamps.
- File names and input order do not select the original owner. Public row codes are opaque; moving a file may still change the row code.

### Codex project evidence

All valid nonempty `session_meta.cwd` and `turn_context.cwd` values in an accounting group are project evidence. A later context cannot be discarded merely because an earlier file already supplied a working folder. Empty or invalid context folders do not suppress valid evidence.

Paths that resolve to the same safely observed local Git repository root, or equivalent path spellings under the host operating system, can represent one project. The UI's general temporary-folder bucket is not evidence that distinct temporary projects are the same. Existing network and symlink/junction restrictions apply when checking a repository root.

Conflicting project identities leave the session's project unknown and attribution incomplete. A known usage total is retained once; PLER does not allocate that total between conflicting projects without per-usage evidence. This applies when context folders disagree with each other or with session metadata, including cached metadata. Parser version `accounting-2026-10-28.2` records this interpretation; schema 2 is unchanged.

### Zeroed Claude copies

Some locally observed repeated copies contain four explicitly zeroed primary usage fields while retaining a positive thinking breakdown. These are unverified candidates, never zero-usage calls or a basis for estimating output. PLER reconciles a candidate only when its nonempty message/request identities, known model and thinking count match an actually selected, valid largest usage snapshot. That verified reply supplies the counts once; the candidate contributes no extra tokens or model call. A fixed `reconciled_copies` explanation remains visible.

Missing fields, non-integer zeros, unknown identity/model, a different thinking count, conflicting valid snapshots or nonzero malformed usage cannot use this rule. Without a matching witness the affected file and canonical reply remain incomplete. Adding/removing a witness changes the resolution on each scan, including when the metadata is cached. An unrelated malformed row or read failure keeps its warning. No original log is repaired or rewritten.

The inclusive output counter and its thinking decomposition are distinct fields in the [Claude usage definition](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost). This reconciliation describes retained local copies; it does not claim that the provider documents the contradictory zeroed form.

## Mixed Codex formats

Per-response usage and cumulative checkpoints are reconciled before totals are published. At a compatible maximum checkpoint, response records demonstrably covered by file ordering or earlier timestamps are subtracted, and the nonnegative residual is added once. Responses after that checkpoint are additional usage. The residual has unknown model and call count, even if a model appears nearby.

Ambiguous equal-time coverage across different files, conflicting component totals, changed response usage after the checkpoint, decreasing cumulative values and compaction boundaries are flagged as incomplete. Identical residual evidence replayed by related sessions is counted once with uncertain ownership. **Arbitrary fork/compaction histories are not proven to reconcile completely.** Some unresolved cumulative usage is excluded. A known total is not necessarily a guaranteed lower bound when anonymous or inherited records cannot be verified.

### Codex history boundaries

Retained cumulative counters do not prove that related histories are disjoint. When a parent and child session, or sessions sharing response evidence, both carry cumulative checkpoints, their numbers are kept but marked incomplete (`unreconciled_totals`); PLER does not claim the child's total includes or excludes the parent's. A cumulative child whose parent file is not retained is incomplete in the same way.

Subagent threads of one Codex session keep its `session_id`, carry their own thread `id` and name the root or a sibling thread as `parent_thread_id`. That lineage is inside the merged session and is not parent evidence. Only parents outside the merged session count: exactly one becomes the session's parent; several different outside parents, a thread naming itself, or a parent cycle leave the parent unknown, attribution incomplete and totals incomplete. Metadata order never chooses between contradictory parents.

A file with only a compaction marker is an explicit unknown boundary, not a known empty session. Sessions with only aborts, tool calls, quota samples or completions are kept without inventing calls or tokens. Metadata-only and context-only files do not create active sessions. Parser version `accounting-2026-10-28.3` records these rules; schema 2 is unchanged.

### Edited files and Git links

Claude Code edit tools name one target file each. A Codex patch names its targets in `*** Add/Update/Delete File:` and `*** Move to:` headers. The patch may sit inside a code or JSON string, so escapes are undone first. Only the target paths are kept, at most 200 per call, never the patch body; relative targets resolve against the working folder in effect at that moment. Edited-file counts are logged intentions: a failed or later reverted edit still counts. Parser version `accounting-2026-10-28.4` adds Codex targets; token and call accounting is unchanged.

A session is linked to the repository of its working folder and to the nearest repository above each edited file (never at or above the home folder, never through a network path or a user link). Its Git view merges the local HEAD reflog events of every linked repository within the session's time span. The public view reports how many repositories were checked and why, never their paths.

### Commits still on a branch

For every commit, amend or merge event recorded during a linked session, PLER checks whether that commit is still reachable from HEAD, a local branch or a remote-tracking branch. It reads commit objects (loose, or from version-2 packs including deltas) and uses only their parent ids and committer time. Identities and messages are skipped unread, branch names are discarded, trees and files are never opened, and no Git program runs. The walk starts at the newest commit and stops a day before the oldest checked commit or after 20,000 commits.

The answer is `on_branch`, `off_branch` or `unknown`:
- **on_branch:** reached from a branch tip.
- **off_branch:** not reached, after everything that could reach it was read. Amend, rebase, reset and a deleted branch all leave the original commit off every branch, while a rewritten commit can still carry the same change.
- **unknown:** objects were missing or borrowed through alternates, the history was shallow, a link was refused or the walk bound was hit. An unknown commit is never counted as kept or lost.

The period summary counts each commit once, even when several sessions overlap it. It reports the share of tokens in sessions with such commits only when usage and attribution are complete. Timing does not prove who made a commit.

## Numbers, models and events

Usage fields must be exact nonnegative integers representable by JavaScript (at most 2^53−1 per logged field). Required input/output fields cannot be omitted. Codex cache reads and writes cannot exceed total input; reasoning cannot exceed output. Claude cache fields are separate from new input. Reasoning is part of output and never added twice.

An invalid usage row is excluded and the affected source is reported, while valid rows remain. Missing optional cache fields mean zero as defined by the supported log format, not a general rule for missing data. Cumulative or conflicting model attribution uses the `unknown` model bucket. That bucket remains in totals; assigning the entire legacy session to the last model is forbidden.

Only metadata identities consumed by a Codex record type are validated. An unrelated `id` field in a skipped message cannot invalidate a valid usage record. Used response, turn, tool, session and compaction identities remain strict; malformed JSON remains invalid even in an otherwise skipped row.

Errors and aborts are event counts. A request can have several events; they are never presented as a percentage of unique failed requests. Logged work duration, record span and elapsed human working time are different concepts.

## Quality and provenance

Both JSON interfaces include `version`, `schema_version`, `parser_version`, `source_scope` and `quality`. The browser snapshot includes `scanned_at`; terminal JSON includes `generated_at`. Session rows also include quality flags and fixed, localized explanations. Flags describe retained records, not provider-wide completeness.

`tokens_complete`, `calls_complete`, `counts_complete`, `attribution_complete` and `models_complete` distinguish the affected dimensions. Missing/unreadable sources make the selected token total incomplete. Incomplete token or ownership data suppresses concentration and session-length comparisons. Observations do not establish waste, savings or a model's relative quality.

Schema 2 changes session grouping/counts and model attribution. Consumers must check the schema and quality fields. Old exports are not recomputed automatically. Parser-helper changes invalidate affected metadata caches; the next read rebuilds them from logs.

### Archived sources

For default and environment-selected roots, PLER keeps each file's allowlisted metadata projection in a bounded local archive. A file that is no longer present under its selected root is replayed from that projection with the same reader rules as a live file. It is never added on top of a live file with the same path.
- **Provenance:** Each session carries `source_state` (`live`, `archive` or `mixed`) and `source_deleted`. The JSON header reports whether any selected session used archived metadata.
- **Copies:** A live resumed session that shares identities with an archived file keeps one copy of each reply, response, prompt and tool call with a stable identifier. Anonymous archived quantities in an overlapping session cannot be proven disjoint, so they are withheld and the session is marked `archive_unverified` with incomplete tokens, calls and counts.
- **Unverifiable sources:** A source that is present but unreadable, or whose WSL distribution is not running, uses its prior projection without claiming deletion. It is marked `archive_unverified`. Metadata extracted by another reader version is marked `archive_old_parser`. Both make tokens incomplete.
- **Lost coverage:** Eviction by age (365 days unseen), file count or size, and an unreadable archive, add quality issues instead of being presented as zero usage.

## Local access boundary

The startup address carries a random per-process access token in its URL fragment. The page removes the fragment and retains the token in tab session storage; report reads, exports and actions require it. The public root page and health check do not disclose it. Restarting invalidates the previous token; use the new startup address. This is access to one local process, not user accounts, team roles, SSO or OS-level isolation. A process that can read the user's terminal, browser state, memory or local logs is outside this boundary. Do not share the startup link.

User-selected local log roots (home defaults, environment roots and command options) may follow the user's own symlink or Windows junction to a local target. Targets are inspected before following; ordinary network, device and volume targets and links inside the selected root remain refused. The resolver preserves link/.. traversal semantics instead of choosing a different folder by normalizing too early.

On Windows, explicitly selected `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `--claude-dir` and `--codex-dir` may name an ordinary `\\wsl.localhost\<distribution>\...` or `\\wsl$\<distribution>\...` root. This creates a per-scan capability for that subtree only. It does not make WSL paths valid as project, Git, cache or log-supplied paths. No WSL auto-discovery is performed, and a local link cannot silently authorize a WSL target.

Before discovery and again before the readers' file phase, the only allowed status command is the validated absolute Windows System32 `wsl.exe --list --running --quiet`, without a shell or stdin and with a bounded timeout. A stopped or unknown distribution is refused before UNC filesystem access. PLER uses no distribution launch, installation or command-execution option. An external stop between the status query and filesystem access is a concurrency boundary, not an atomic never-start guarantee.

Git/project and cache paths continue to use the strict local validator. On macOS/Linux, root-owned operating-system links can be followed; user links remain refused in these stricter contexts. Unsafe cache locations disable caching without redirecting it. These checks do not isolate against a malicious same-user process racing filesystem changes or prove physical locality of arbitrary OS mounts. PLER has no supported shared-server deployment.
