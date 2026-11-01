# Retained-log accounting contract — schema 2

PLER describes the local agent records it can read. It does not reconcile a provider bill, prove complete account coverage or measure task quality. Periods select sessions by last activity and include their full retained totals.

## Plan check (0.2.27; local Y04 safeguards, not yet released)

The plan check compares published prices with dated recorded responses in the last 30 days, per agent. It uses all selected source folders and all projects, whatever the page/report filters select, including unknown projects. This scope does not establish one account or complete account coverage. Exact inclusive `since`/`until` bounds are exported; `history_complete` is false and `actual_payment_usd` is null. The date of the oldest retained session is not proof of a complete billing month.

- **Plan:** Codex logs its plan word with its meter (`plus`, `go`, `pro`); the latest one in the period is used. Claude Code logs no plan, so its plan is what the user chose (Pro, Max, Ultra or an API key), stored only on this computer in `plan-choice.json` format 1 (`{"format":1,"claude":...}`). A file PLER cannot read is reported and never overwritten. The demo keeps its choice in memory.
- **Prices and ratios:** published US-dollar list prices before tax of 31 October 2026: Claude Pro $20 ($17 a month with annual billing), Max $100, Ultra $200; ChatGPT Go $8, Plus $20, Pro $100/$200/$500 (the Pro tier is not logged, so no Pro price is assumed). Anthropic's Max has 5x Pro's usage every 5 hours and every week, Ultra 10x Pro's weekly usage. Ultra's five-hour exemption requires account verification, which a plan choice does not establish; no uniform five-hour ratio is assumed for it. PLER has no verified Plus/Pro limit ratio. List prices, tax, regional terms, credits, add-ons and actual payment are separate.
- **API equivalent:** sum of accepted responses' own recorded list-price amounts inside the interval. Missing, naive, reversed, future or boundary-straddling response times are not allocated. Incomplete/old/unchecked sessions, uncertain histories, call-count or token mismatches, read failures and archive loss mark coverage limited. Unknown project attribution alone does not remove otherwise known response usage. An unpriced response is unknown, not free; no priced responses means an unknown display, not zero dollars. This is a standard-price equivalent of retained responses, not a quote for reproducing a task, subscription value or a provider bill.
- **Limits:** account-wide observations (Codex logs; Claude Code terminal status line). Valid samples are grouped by window and reset time; 100% means that value was observed, not that every peak was captured. Refused-request events are also evidence. A contradictory episode's window period is left out of the counts, even after a later clean reset; clean periods before and after it still count, and any contradiction blocks a lower-plan comparison. Unusable dates/resets and several source groups block lower-plan conclusions; compatible samples do not prove account identity.
- **Findings:** `limits_reached`, with `larger_ratio_unpublished` for Codex Go/Plus or `larger_need_unseen` for Claude Pro/Max, never establish a sufficient upgrade. Legacy `api_cheaper`, `smaller_fits`, `smaller_fits_weekly` and `smaller` are no longer emitted. `api_below_list_price` is only a numeric observation, not a switching saving; it requires positive fully priced dated usage, no known source/usage/pricing/account-scope/plan-change or contradictory/unusable-meter limitation, retained history spanning at least 28 days and no observed reached limit. This still does not prove a full month of account activity. Meter freshness/density restrictions below apply to the lower-plan comparison; a dated numeric price observation alone does not rely on a current quota level.
- **Observed lower-plan comparison:** `lower_observed` / `lower_weekly_observed`, under `lower_plan_comparison`, remain conditional on the assumed sample-time plan (`assumed_plan`, `observed_only: true`). Each comparable required meter needs at least 14 days of span, 14 distinct UTC dates and no gap over two days, fresh last samples (30 minutes short / 24 hours long) and an unelapsed last reset. These are PLER observation thresholds, not provider guarantees. Known usage/source/pricing/meter/plan-change limitations or observed reached limits withhold this result. Max-to-Pro and Ultra-to-Max weekly threshold headroom remains 80% of the published ratio (16% / 40% of the current meter). Weekly-only observations do not establish five-hour or overall fit. `expires_at` is the earliest required sample freshness/reset deadline; the open page ages the result on its existing clock without rebuilding the plan selector.
- **Limitations:** fixed path-free codes: `source_incomplete`, `usage_incomplete`, `unpriced_usage`, `multiple_source_groups`, `plan_changed`, `meter_conflicting`, `meter_incomplete`, `meter_stale`, `meter_sparse`. Terminal, browser and JSON retain the same boundaries. No payment entry, billing lookup, account identifier or external query is added.

Prices, ratios and plans change; each is dated and replaced only with a new published source. The check is not a bill, a forecast of future need or a recommendation to buy.

## User-named work (0.2.26)

Work items are explicit local user annotations, not inferred task identities. Each has a title and a set of the existing full opaque session codes. Selected work subtotals include each linked selected session's full recorded usage. A session may belong to several items; their subtotals are not additive. The linked union includes each selected session once and never changes the report's general totals. API equivalents sum original recorded amounts before display rounding; price coverage is token-weighted, and unpriced usage is not presented as free. Existing token, call, model and attribution uncertainty remains visible.

Known sessions outside the main filters and links missing from the entire snapshot are reported separately. Missing links contribute no invented usage or completeness; they are never rebound by title or provider-native ID after a source move or identity change. Rename, unlink and delete affect annotations only, leaving agent logs, archive history and session verdicts intact. Deletion does not erase copies in earlier backups. Work is not an allocation of a session's usage between tasks and does not prove task cost, completion or quality.

The bounded `work-items.json` format 3 permits at most 200 items, 2,000 links per item, 20,000 memberships and 2 MiB. Titles remain trimmed Unicode strings of 1–120 characters without control characters. Legacy formats 1 and 2 are read into defaults without rewriting; the first actual user edit writes format 3. A no-op does not migrate bytes. Older PLER builds cannot read format 3; keep a checked compatible backup for rollback. This component format is independent of usage schema 2 and the unchanged backup envelope format 1.

Work follow-ups (method 1) are private annotations in that same atomic document: at most 10 per work, 100 total, and one open record per work, subject to the 2 MiB limit. They record the user's trigger/observation/change, a frozen baseline and an optional explicit weekly review or cancellation. Text fields have the same 1,000-character rules. Deleting a work also deletes its follow-ups; earlier private backups retain their copies. Ordinary reports omit all follow-up records. Summaries expose counts only. No provider, model, transcript or Git query is made by a follow-up action.

The lazy authenticated GET `/api/usage/work/followups?work=<opaque-id>` measures only when opened. POST `/api/usage/work/followup` has an exact action/field allowlist and 16 KiB UTF-8 bound; clients cannot supply numerical snapshots. Starting/reviewing requires a source observation no more than five minutes old, with no future clock skew. The baseline anchor is the source observation time; before is `[anchor-7d, anchor)` and after is `[anchor, anchor+7d)`, UTC, with equal nonoverlapping windows. The after window must finish in a fresh reading before the user can save a review. There is no scheduled review or notification.

Only dated, reconciled responses wholly inside each window contribute. Whole active-session totals are never reassigned to a calendar week. Missing linked sessions, source/archive loss, unreconciled or undated usage, boundary-crossing evidence, unknown or multiple models and measurement bounds are explicit limitations. Each response must reconcile with the complete session's token/call evidence. Bounds are 100,000 inspected response events, 64 groups, 2,000 included sessions and JavaScript-safe integer totals per measurement; exceeding a bound prevents a numeric comparison. Source transcripts/paths are not persisted in these snapshots. Project identity is an opaque digest.

Comparison uses the median of per-session average tokens per response within each exact agent/project/model group, with at least three contributing sessions in each window. Group sets must match, the saved baseline must reproduce from current linked sources, parser versions must match and the user must explicitly assess tasks/conditions as similar. Otherwise the review remains recorded with fixed reasons and no numeric delta. New later sessions can be linked without moving the baseline; changed or missing historical evidence blocks comparison. A content revision binds the preview, source observation, membership and record before the atomic write; stale windows cannot overwrite a saved review. Reviewed/cancelled records are immutable except explicit deletion. Drafts survive failed requests, selection and language changes. These are descriptive observations, not causal effects, quota savings, billed cost, quality or completion claims; source coverage may represent only part of either week.

Each work optionally records `goal` and `result_note` (up to 1,000 Unicode characters each; normalized line endings, trimmed, no other control/surrogate/line-separator characters), plus user-declared `outcome`: `not_recorded`, `partial`, `completed`, `not_completed`. `outcome_at` is null when unassessed; otherwise it is the local entry time, not measured completion time. Goal-only edits do not retimestamp the outcome. These fields describe the whole work and remain visible outside the main filters or with missing session references. They are never inferred from tests, Git, usage or session verdicts and never produce a quality score.

`observations` summarizes only selected linked sessions: each session's latest visible test/build result, and the number of sessions with readable/coincident/limited Git history. It does not add overlapping commit events or count individual test cases. A passing check does not turn partial work into completed work; a failed check does not override a completed user entry. No additional source or Git read is required.

Writers validate under the shared archive lock before atomic publication. Goal/outcome changes use a content-based `details_revision`/`expected_revision` check, independent of second-resolution timestamps and title/link edits. A stale editor gets a fixed conflict response; data is not overwritten. The browser keeps its draft, shows the latest saved values, and requires review before a later explicit save; discarding a draft writes nothing. Network-uncertain saves require a read-only metadata reload before another write. Drafts survive filter changes, work selection and language reloads (temporarily in this browser tab's session storage).

The authenticated local `/api/usage/work/details` action has an exact allowlist and a 16 KiB bound for UTF-8 details; existing work actions retain their 1 KiB admission bound. Corrupt/newer documents are reported and never replaced with empty records. An error after publication does not guarantee rollback. Demo work stays in memory. Ordinary JSON reports omit the entire work projection, including private titles, goals, notes and memberships, even without masking. Private backups include them; summaries expose counts only. Deleting work removes these annotations and links, preserving source logs, verdicts and older backups. Work changes reload metadata, not agent sources.

## Private backup and recovery (0.2.25)

Backup format 1 contains a fixed manifest and only the existing saved metadata archive, retention preference, session verdicts, Claude quota journal and, since 0.2.26, work names and links. Missing optional files preserve their normal absent/default meaning; 0.2.25 backups without work remain readable. Creation holds the archive and quota writers' locks, validates the bounded snapshots and reads no original agent source. Reader/code caches, generation/lock files, demo data, agent settings and access tokens are excluded. Backup is the saved local history, not the currently filtered report or a promise of complete account coverage.

The ZIP uses stored, uncompressed entries with fixed file/count/byte limits. Manifest application/parser/schema versions, fixed members, checksums and each payload's allowlist/types are verified before recovery. SHA-256 detects accidental damage; an attacker able to rewrite metadata and checksums is outside this boundary. Backup files contain private paths and retained identities and are unencrypted; they must not be treated as anonymous JSON or a support attachment. Web checks retain the uploaded file in memory only, require the same origin/access credential, and admit one backup/check operation at a time. Demo snapshots cannot access these operations.

Recovery stages only fixed files and publishes a new local directory. Existing destinations are refused; current data is neither merged nor overwritten. A failure before publication leaves the current data intact; after a directory-sync failure the complete new folder may already exist, so an error does not imply rollback. No power-loss guarantee for hardware or network filesystems is established. Open the recovered folder explicitly with `--data-dir` on each launch; no persistent profile selection is written.

Original paths, timestamps, retention choice and archive reader keys are preserved. Replay still requires the same selected roots on the same computer; source relocation and another computer are not automatically remapped. Retention bounds remain applicable. Older-reader or unavailable-source metadata retains its uncertainty, stale quota observations remain stale and never-read deleted history cannot be recovered. This backup feature changes no token/pricing accounting rule, parser version or schema version.

## Snapshot and file verification (0.2.24)

An unchanged page refresh preserves the previous reader/decompression/budget issues together with its figures. A snapshot with reader or archive errors is reused for at most five seconds before another read is attempted; a healthy snapshot still has the one-hour maximum. Quota samples are refreshed on reuse.

An exact reader-cache hit requires the same device/file identity, size and modification time. Old entries or filesystems without a usable identity require a full read. Plain-log continuation hashes every byte of the old prefix in bounded, cancellable chunks; this replaces the earlier first/last 4 KiB sample. The newly opened reading handle must match the verified identity, size and modification time before seeking. Rotation between verification and opening falls back to a full read. The reader source-version key includes this cache implementation. A normal unchanged hit still trusts filesystem metadata; it is not cryptographic proof against a writer deliberately preserving all metadata during an in-place rewrite.

Prefix verification adds I/O (also counted in the scan's source-byte budget) without retaining transcript text. The original parser-only speed guard remains; a separate whole-pipeline comparison includes cache loading, prefix hashing, tail parsing and cache persistence. No previous timing is claimed to include work it excluded.

Explicit help, version, collection/listing, dry-run and compile-only test modes are not counted as executed checks. If a command exceeds the inspected word budget, it cannot claim a known pass/fail outcome. A successful process exit still does not prove that a nonzero number of tests ran; no test-output text is collected to prove that.

## Tests and builds the agents ran (0.2.18)

PLER reads each shell command an agent ran, in memory only, to decide whether it ran a test or a build. The command text is then dropped: the cache and archive keep only the kind (`test` or `build`), whether its exit code is the check's own, the call's identity and whether the call failed.

- **Recognised:** common test and build tools of many languages, for example pytest, unittest, tox, npm/pnpm/yarn test and build scripts, node --test, jest, vitest, go test/build, cargo test/build, dotnet test/build, Maven, Gradle, make, CMake/ctest, gcc/clang, rspec, phpunit, mix and swift. A test script named like `test_*.py` counts as a test. Quoted text and here-document bodies are not commands.
- **Outcome:** Claude Code marks a failed call; Codex logs the exit code of each finished command. A run passed when its exit code is 0 and failed otherwise.
- **Not visible:** the exit code is the check's own only when the check is the last step of the command line. When its output is passed on (`| tail`), another step follows (`; echo`, `&& next`), it is an alternative (`||`) or it runs in the background, the run is counted with no visible result. Codex logs that do not record finished commands show no checks.
- **Per session:** runs, passed, failed, and how the last run with a visible result ended. The observation says how the selected sessions' last visible test ended and how many tokens the sessions that ended on a failing test used. It describes the agents' own checks; it is not a quality measure, and a passing run does not prove the work is right.

## Your verdicts (0.2.17)

A verdict is your own one-click judgement of a session: **useful** or **wasted**. PLER never guesses one.

- **Stored:** only on this computer, in `session-verdicts.json` in PLER's cache folder. Each entry holds the page's 24-character session code (a hash of agent, log source and provider session ID), the word and the second it was set. No path, project name, prompt or command is written. Cache reset and archive clear keep it. A damaged file, or one written by a newer PLER, is reported and never overwritten.
- **Scope:** only a session in the current snapshot can be judged. The demo keeps verdicts in memory only.
- **Totals:** sessions, tokens and API list-price equivalent are summed per verdict over the selected sessions. The figures show what you judged; they are not a quality measure, and a session's whole total is not the cost of one change in it.
- **Identity:** the code changes if a log is moved to another folder, so its verdict no longer matches. Codes are never matched by similarity.

## API list-price equivalent (0.2.16)

Each accepted response is priced once, with the response's own model and the provider's public standard-tier list price of 1 November 2026 (Anthropic and OpenAI pricing pages; the table is fixed in `pricing.py`). The price is per million tokens for input, cache reads, cache writes and output. Reasoning is already part of output. This price-confidence interpretation is `accounting-2026-11-01.1`; schema 2 is unchanged.

- **Tiers:** a tier is chosen by the response's own prompt (input + cache reads + cache writes). For example, OpenAI's long-context price applies above 272,000 tokens and Claude Haiku 5.5's above 100,000.
- **Claude cache writes:** priced by a consistent logged 1-hour/5-minute split. When the split is absent, the API default of 5 minutes applies. Invalid splits are not clamped: valid token totals stay counted, while a retained false `price_inputs_complete` flag withholds pricing. Invalid private modifiers are reduced to that safe boolean; they cannot disappear during sanitization and become standard pricing. Copies carrying selected usage must agree on their computed price regardless of row/file order.
- **Codex:** logs no service tier in the retained contract, so the standard-tier equivalent is assumed. GPT-6 writes have separate 30-minute/12-hour rates; retained counts have no lifetime split, so any positive write count leaves the whole response unpriced. Zero-write responses retain ordinary pricing. The reviewed GPT-5.3 legacy behavior has no additional write charge. Codex requires exact listed model IDs; arbitrary dated suffixes do not inherit a rate. Claude's dated-family alias policy remains explicit.
- **Unpriced:** a response is left unpriced, but stays in the token totals, when:
  - its model has no published price;
  - its prompt exceeds the largest covered tier;
  - Claude logged a non-standard/unknown speed, a region other than global (an absent region and `not_available`, which Claude Code logged before it reported regions, count as global; only US-only `us` has a published higher price), unsupported service tier, invalid split/modifiers or conflicting copy prices;
  - Codex's write lifetime cannot be established for the selected model;
  - its usage exists only as a cumulative total.

  The page shows the priced share of tokens.
- **Release review:** `docs/compatibility.json` records reviewed code/fixtures, model/tier/plan facts and official URLs/dates. The offline `tools/check_compatibility.py` gate detects drift and blocks release after a 30-day price review interval. It never fetches or replaces prices. This maintenance policy does not establish current billing or expire runtime prices silently.
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

Ambiguous equal-time coverage across different files, conflicting component totals, changed response usage after the checkpoint, decreasing cumulative values and compaction boundaries are flagged as incomplete, except in the compacted and forked threads explained below. Identical residual evidence replayed by related sessions is counted once with uncertain ownership. **Arbitrary fork/compaction histories are not proven to reconcile completely.** Some unresolved cumulative usage is excluded. A known total is not necessarily a guaranteed lower bound when anonymous or inherited records cannot be verified.

### Codex history boundaries

Retained cumulative counters do not prove that related histories are disjoint. When a parent and child session, or sessions sharing response evidence, both carry cumulative checkpoints, their numbers are kept but marked incomplete (`unreconciled_totals`); PLER does not claim the child's total includes or excludes the parent's. A cumulative child whose parent file is not retained is incomplete in the same way.

Subagent threads of one Codex session keep its `session_id`, carry their own thread `id` and name the root or a sibling thread as `parent_thread_id`. That lineage is inside the merged session and is not parent evidence. Only parents outside the merged session count: exactly one becomes the session's parent; several different outside parents, a thread naming itself, or a parent cycle leave the parent unknown, attribution incomplete and totals incomplete. Metadata order never chooses between contradictory parents.

A file with only a compaction marker is an explicit unknown boundary, not a known empty session. Sessions with only aborts, tool calls, quota samples or completions are kept without inventing calls or tokens. Metadata-only and context-only files do not create active sessions. Parser version `accounting-2026-10-28.3` records these rules; schema 2 is unchanged.

### Compacted and forked Codex threads (E01)

A Codex session is counted completely by its response records, without the compaction warning or a cumulative residual, when every one of its files passes this check. Between two cumulative checkpoints with no compaction between them, the file's own records (each response once) and its meter grow by exactly the same amounts in every token field. Across a compaction the records may only gain: Codex's meter omits the compaction request itself. Every compaction follows a checkpoint, except a compaction marker that a thread naming a parent thread carries before its own first record and checkpoint, which is the parent's history copied into the thread. The first checkpoint equals the records so far. Only a thread naming a parent thread, with no records yet, may start from a different counter. That start is inherited when the same file later has records, or when the file has none but its client versions wrote response records in another file of the session (that format records every call). Any anonymous record, changed copy, meter jump, earlier unexplained start or older cumulative-only thread leaves the existing rules and warnings in place. Records after a file's last checkpoint have no meter evidence either way, as in any other session.

On this computer's logs (2 November 2026) every one of 226 compacted thread files followed the pattern: 122 compaction-free stretches moved exactly with their meters, and the 32 forked threads that started from an inherited counter had no records before it. The inherited value matched no checkpoint of the named parent, so PLER does not use it as a total; it counts the records. Codex sessions marked unreconciled fell from 9 (98.8% of Codex tokens) to 3 (0.19%); totals did not change.

### Edited files and Git links

Claude Code edit tools name one target file each. A Codex patch names its targets in `*** Add/Update/Delete File:` and `*** Move to:` headers. The patch may sit inside a code or JSON string, so escapes are undone first. Only the target paths are kept, at most 200 per call, never the patch body; relative targets resolve against the working folder in effect at that moment. Edited-file counts are logged intentions: a failed or later reverted edit still counts. Parser version `accounting-2026-10-28.4` adds Codex targets; token and call accounting is unchanged.

A session is linked to the repository of its working folder and to the nearest repository above each edited file (never at or above the home folder, never through a network path or a user link). Its Git view merges the local HEAD reflog events of every linked repository within the session's time span. The public view reports how many repositories were checked and why, never their paths.

### Commits still on a branch

For every commit, amend or merge event recorded during a linked session, PLER checks whether that commit is still reachable from HEAD, a local branch or a remote-tracking branch. It reads commit objects (loose, or from version-2 packs including deltas) and uses only their parent ids and committer time. Identities and messages are skipped unread, branch names are discarded, and no Git program runs. Only the line count below opens trees and files. The walk starts at the newest commit and stops a day before the oldest checked commit or after 20,000 commits.

The answer is `on_branch`, `off_branch` or `unknown`:
- **on_branch:** reached from a branch tip.
- **off_branch:** not reached, after everything that could reach it was read. Amend, rebase, reset and a deleted branch all leave the original commit off every branch, while a rewritten commit can still carry the same change.
- **unknown:** objects were missing or borrowed through alternates, the history was shallow, a link was refused or the walk bound was hit. An unknown commit is never counted as kept or lost.

The period summary counts each commit once, even when several sessions overlap it. It reports the share of tokens in sessions with such commits only when usage and attribution are complete. Timing does not prove who made a commit.

### Lines still in place (0.2.19)

For a commit found on a branch that is also in the current HEAD's history, PLER counts the lines it added and how many are still in place at HEAD.

- **Added lines:** per file, the lines whose count grew compared with the commit's only parent. Blank lines and lines without a letter or digit (such as a lone `}`) are not counted. Surrounding whitespace is ignored.
- **Still in place:** an added line is looked for, by content, in the same file at HEAD. A line that existed before the commit is assumed to be the copy that remained, so a repeated line counts as kept only when HEAD has more copies than the parent had.
- **Not measured:** merges, a repository's first commit, commits outside HEAD's history and unreadable objects. A traversal/file cutoff leaves the entire commit unknown and is never cached as a complete count. Per repository/read, tree parsing is capped at 4,096 distinct trees and 100,000 entries, traversal at 100,000 visits and 128 path levels; at most 400 changed files are admitted per commit. Binary files, files of 1 MiB or more and file contents beyond the 256 MiB budget are skipped. Every traversal checks cancellation.
- **Approximation:** a line moved within its file counts as kept. A line rewritten in place, or in a file that was renamed or moved, does not. A copy/rename can increase a new path's line counts without newly authored code; this observation does not establish authorship or new work.
- **Privacy:** file names and contents are read only in memory, from loose objects and version-2 packs, never written, cached or shown. Only counts per commit reach the page and JSON. Counts for the same HEAD are reused, also after a restart: the page keeps the four counts in `git-survival.json` under a one-way digest of repository folder, HEAD and commit, with no path, commit id, name or text (0.2.22). A new HEAD or other counting code is measured again; a count cut short by the byte budget is never kept; cache reset removes the file.
- **Meaning:** kept lines show that the change was not undone or rewritten so far. They do not prove that it is correct or that the session's tokens were well spent.

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
