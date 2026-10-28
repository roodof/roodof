# Changes

## 0.2.10 — 2026-10-28

- Read explicitly selected WSL log roots on Windows through either standard WSL host spelling. A per-scan capability covers only that subtree and requires a fresh running-distribution status before discovery and reader access. Ordinary UNC/device paths remain refused before probing; Git/project/cache paths stay strict.
- Use only the fixed, bounded System32 WSL status command, with no shell or distribution launch. Explain stopped/unavailable distributions in both languages. No automatic WSL discovery is performed.
- Preserve case-sensitive WSL file identities during discovery and reconciliation. Resolve a selected local link before its following parent-directory component instead of choosing another folder by early normalization.
- Keep root-owned operating-system links such as macOS `/var` → `/private/var` in their original spelling unless a later `..` needs the real parent. The first 0.2.10 commit resolved them always, which changed every reported macOS temporary path and failed five tests on macOS CI.

Real invented WSL records changed from zero sessions in 0.2.9 to two sessions and 350 tokens; both host spellings and both selection methods matched. Windows-from-Linux mount reading and case-only file names were verified separately. See [evidence and limits](../reports/wsl-roots-v1/REPORT.md).

## 0.2.9 — 2026-10-28 (local candidate)

- Follow the user's own link or junction to a log folder: `~/.claude`, `~/.codex`, their `projects`/`sessions` folders, `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `--claude-dir` and `--codex-dir`. Someone who moved these folders to another disk and left a link behind previously saw no records and an "UnsafePath" skip. Each link is read without being followed, so a target with network, volume or device syntax is refused before anything there is touched; loops stop after 32 links. Links inside a log folder, other Windows reparse points, project paths read from logs, Git metadata and the cache folder keep the previous rules.

## 0.2.8 — 2026-10-28 (local candidate)

- `pler demo` opens the page with invented Claude Code and Codex logs and an invented Git repository. The data is written into a `demo` folder inside PLER's cache folder; the agents' own folders and quota samples are never read. A banner on the page says the data is invented. The demo has two agents, four projects, a Codex quota forecast, an older-format Codex log with a data-quality warning, a session started in a parent folder, and commits on and off a branch. Each read recreates it relative to the current time. A folder that is not a PLER demo is never replaced.
- The Windows portable package adds `PLER-Demo.cmd`.
- The Git observations read "No longer on any branch: n" and "Could not be checked: n" in English, so a single commit reads correctly.

The demo is what the [pilot kit](../reports/pilot-kit-v1/REPORT.md) uses, so that participants can do every pilot task before deciding whether to look at their own records.

## 0.2.7 — 2026-10-28 (local candidate)

- For commits recorded during a session, show whether each is still on a local or remote-tracking branch, or was amended, rebased, reset or left on a deleted branch. Commit objects are read directly: loose files and version-2 packs, including offset and reference deltas, SHA-1 and SHA-256. Only parent ids and committer time are used; names, email addresses, messages, trees and files are never kept or opened. Missing or shallow history, borrowed objects, refused links and the 20,000-commit bound give `unknown`, never a guess.
- The period summary adds an observation: how many sessions recorded how many commits, each counted once, and how many are still on a branch. The token share of those sessions is shown only when usage is complete.
- Session JSON adds `commits` counts and a per-event `on_branch`. The view adds `git_outcome`. Accounting and export schema 2 are unchanged.

The branch answers matched git's own on invented repositories with amend, reset, rebase and a deleted branch, for loose objects, a pack and an aggressive delta pack, in SHA-1 and SHA-256. On a 30,000-commit pack, a recent commit was found in 0.07 s; a dropped one was confirmed in 0.56 s; the worst case stopped at the bound after 3.3 s. On this computer's logs, 4 sessions recorded 68 commits and all 68 are still on a branch. Tests: 248 on Windows with Python 3.9 and 3.12, 257 with Python 3.14 on Windows and Linux, plus 18 browser-logic tests. See the [evidence](../reports/git-outcome-v1/REPORT.md).

## 0.2.6 — 2026-10-28 (local candidate)

- Link each session to the Git repositories holding the files it edited, not only to its working folder. An agent started in a parent folder, or a session whose project is unknown, now shows the commits recorded in the repository it changed. Events of several linked repositories are merged. The page names how many repositories were checked, never their paths.
- Read the target files of Codex patches (`*** Add/Update/Delete File`, `*** Move to`), also when the patch sits inside a code or JSON string. Only paths are kept, never the patch body. Codex sessions now report edited files like Claude Code sessions.
- Advance the parser version to `accounting-2026-10-28.4`; token and call totals are unchanged and export schema 2 is unchanged. The Codex metadata cache rebuilds once.

On this computer's real logs, sessions with readable Git history went from 1 to 6 and sessions with Git events during their time from 0 to 4. Those 4 sessions hold 69% of the tokens. This session's view shows exactly the 4 commits made in the product repository during it. The source passes 237 tests on Windows with Python 3.9 and 3.12, 246 with Python 3.14 on Windows and Linux, plus 18 browser-logic tests. See the [Git link evidence](../reports/git-links-v1/REPORT.md).

## 0.2.5 — 2026-10-28 (local candidate)

- Disable the metadata and Claude quota caches when `PLER_CACHE_DIR` or the default cache base names a network location, or a user link or junction leads to it, instead of reading or writing there. Revalidate the cache and quota file paths before every write, and remove failed temporary files only at a validated location.
- Mark retained Codex parent/child cumulative histories, cumulative children with a missing parent, contradictory, self-referential or cyclic outside parents and compaction-only files as incomplete or unknown instead of complete. Keep sessions whose only activity is an abort, tool call, quota sample or completion. Subagent threads inside one merged session are not parent evidence, so ordinary multi-agent sessions are not flagged.
- On macOS and Linux, follow root-owned operating-system links such as macOS `/var` → `/private/var`; user-owned links and every Windows link or junction remain refused. Treat two leading slashes or backslashes in any mix as a network path on every platform.
- Advance the parser version to `accounting-2026-10-28.3`; export schema 2 is unchanged. Affected metadata caches rebuild once.
- The Windows candidate builder also accepts the official CPython embeddable package and bundles the 3.14 zstd module. It checks for an existing archive before building, and names a versioned folder's ZIP correctly. With CPython 3.14.10 the Python-free candidate's first read on the test computer fell from 23.1 to 7.2 seconds, with identical totals.
- Add a prepared, manually dispatched CI workflow for Windows, macOS and Linux on Python 3.9, 3.12 and 3.14, release/acceptance/pilot/support procedures, and an offline builder for a private, unsigned Windows x64 candidate that bundles an existing CPython 3.12 runtime.

The source passes 227 tests on Windows with Python 3.9 and 3.12 (the nine Python 3.14 decoder tests are skipped there), 236 on Linux (WSL2 Ubuntu, Python 3.14.4, standard-library zstd decoder), including a macOS-style system-link temporary folder, plus 18 browser-logic tests. The installed wheel passes 227 tests. On 128 fixed real Codex files sessions, tokens and calls are unchanged from 0.2.4. The portable candidate ran without any Python on `PATH`; it is unsigned and has not been tried on a clean machine. In the CI workflow all 12 jobs pass: source and installed-wheel suites on Windows Server 2025, Ubuntu 24.04 and macOS 26 arm64 with Python 3.9, 3.12, 3.14 and the optional `zstandard` reader. See the [completion evidence](../reports/completion-v1/REPORT.md).

## 0.2.4 — 2026-10-28 (local candidate)

- Collect all valid nonempty Codex session/context working folders before deciding project attribution. Conflicting projects remain unknown with incomplete attribution instead of the first file choosing a project. Empty metadata folders cannot hide valid context evidence.
- Compare safely observed Git roots and host-equivalent path spellings as project evidence; do not use the UI's shared temporary-folder bucket as proof of common ownership. Preserve one count for repeated response usage and reapply the rule to cached metadata.
- Generalize the existing attribution explanation to cover context conflicts as well as copied records. Advance the parser version to `accounting-2026-10-28.2`; export schema 2 is unchanged. Affected metadata caches rebuild once.

The source passes 188 tests on each of Python 3.9 and 3.12, plus 18 browser-logic tests. Package and local runtime checks are recorded separately in the [project attribution evidence](../reports/project-attribution-v1/REPORT.md). Arbitrary history reconciliation, first-read performance, native distribution and professional acceptance remain open. A separately observed explicitly configured network cache target remains an open follow-up.

## 0.2.3 — 2026-10-28 (local candidate)

- Select a real dominating usage snapshot with a linear verification pass instead of comparing every pair of unique checkpoints. Crossing snapshots remain unresolved; duplicate and iterable behavior is preserved.
- Use the standard JSON encoder's fast whole-document path for metadata cache writes, followed by the same temporary-file replacement. A serialization memory failure preserves the previous cache and extracted metadata.
- Bound the batched Huffman literal lookup at 12 bits instead of 14. The largest auxiliary table has one quarter as many entries; stream, frame-size and checksum validation remain enabled. All 128 fixed compressed archives decoded to identical bytes in a paired comparison.

Accounting schema and interpretation are unchanged. Affected caches rebuild once. Large dependency-free first reads remain slow; measured gains are specific to the recorded datasets, not a universal startup guarantee. See [performance evidence](../reports/cold-start-v1/REPORT.md).

## 0.2.2 — 2026-10-28 (local candidate)

- Reconcile a narrow Claude zeroed-copy shape only with an exact witness in the selected valid usage snapshot of the same reply and model. Count the verified reply once and retain a fixed explanation. Unmatched candidates and unrelated corruption remain incomplete; cached candidates are checked again against the current source set.
- Validate only the Codex identity fields actually consumed by each record type. Unused identity-shaped fields cannot reject otherwise valid usage; consumed invalid identities and broken JSON still warn.
- Advance the parser version to `accounting-2026-10-28.1`. Schema 2 is unchanged; `reconciled_copies` is an additional quality explanation, and unresolved zeroed copies have a specific source reason.

The diagnosed local file's calls and tokens remain identical; its repeated copies are now reconciled instead of marking the whole file unreadable. This does not resolve arbitrary fork/compaction history or establish account-wide completeness. Affected metadata caches rebuild once; no original log is changed.

## 0.2.1 — 2026-10-28 (local candidate)

- Show download preparation, prevent duplicate pending exports and retain a visible retry link to the prepared JSON. Clear outdated links when filters change or logs are explicitly refreshed; discard a pending result if its selection changed. Do not label a prepared download as saved to disk.
- Keep keyboard focus on newly revealed sessions after Show more, and restore action focus after refresh/export when the user has not moved elsewhere. Return focus to a persistent control when a project/empty-filter action replaces its origin.
- Make the session table a named keyboard-focusable scroll region with instructions. Use a single filter column on the narrowest screens and larger mobile form text.
- Reload when a valid startup access fragment is opened in an already loaded tab, so a restarted process's new credential is consumed.

Accounting schema and parser rules are unchanged from 0.2.0. These are local usage-flow corrections; real-device accessibility certification and professional acceptance are not established.

## 0.2.0 — 2026-10-27 (local candidate)

- Merge files with the same Codex session ID and reconcile compatible cumulative checkpoints with per-response usage. Retain the largest compatible actual response snapshot for both agents. Never assign legacy cumulative usage to the last model.
- Deduplicate identified Codex turns and tool calls alongside responses. Conflicting copied ownership uses explicit uncertainty and unknown project attribution. Validate numeric usage types, ranges and cache/reasoning relationships; invalid rows produce coverage warnings.
- Show data-quality warnings in both languages; export the app, parser and schema versions. Suppress comparisons with incomplete usage/ownership and remove the invalid error/abort percentage. Describe session-length differences as uncontrolled observations.
- Require the per-process startup access link for report reads and JSON exports, as well as mutations. Remove its fragment from the visible address; retain it in tab session storage. Public HTML no longer supplies the credential.
- Discover regular local logs without following network paths, symlinks or junctions. Report unsupported locations instead of probing them.

**Data contract change:** schema 2 can change session counts, model/project buckets and totals relative to older reports. See [ACCOUNTING.md](ACCOUNTING.md). Ambiguous fork/compaction history remains explicitly incomplete. This candidate is not a public release or proof of professional acceptance.

## 0.1.2 — 2026-10-26

- Cache Claude Code metadata as well as Codex metadata. Unchanged conversations are not parsed again; copied response deduplication and partial-file warnings persist. Prompt, reply, command and tool output text are discarded before caching.
- Require complete compressed frames and matching declared content sizes; verify optional zstd content checksums in the built-in decoder. Reject truncated checksum/skippable data and invalid frame flags. The optional zstandard adapter requires each frame's end and reads subsequent frames too.
- Use larger literal decoding lookups only when a block is large enough to amortize their construction. The first read of a large archive remains slow; improved warm reads do not establish a fast cold start.
- Invalidate caches when decoding/validation helpers change. Do not save a growing log under an old signature or cache a temporary access failure. Remove failed cache-write temporary files when allowed.
- Reject UNC project paths before filesystem probes and refuse symlink/junction ancestors or Git markers during project grouping.

No new dependencies or product controls. The update rebuilds affected caches once. The native installer, other operating systems, desktop Claude quota and professional usefulness remain unverified.

## 0.1.1 — 2026-10-26

Reliability and privacy corrections for local pilot use. This release does not establish company-wide readiness.

- Rebuild damaged or legacy Codex cache entries from the original logs. A checksum detects accidental changes to cached numbers; it is not an authentication mechanism.
- Retain valid records from partially read files and count each affected file once. Broken JSON, truncated rows and invalid response identities are reported instead of crashing or silently omitting the warning. Codex cache hits retain that warning.
- Deduplicate Claude prompts and tool calls that have stable IDs across copied logs; assign tool metadata to the same owner as its response. Records without stable IDs retain their previous counting behavior.
- Accept sessions with unknown dates alongside dated sessions without inventing visible dates.
- Keep a running server's HTML, JavaScript and CSS fixed until restart, so editing the installation does not mix a new page with an old backend.
- Keep the desktop local-only label readable; its text no longer receives the status dot's dimensions.
- Distinguish displayed rows from different source logs even when copied provider session IDs match. Opaque row codes include the source identity in their hash, without exporting the source path; moving a log can change its code.

### Terminal JSON compatibility

`pler report --json --sessions` now uses the page's explicit session projection. Source paths, raw session IDs, parent IDs, branch names, edited file paths, tool names and arbitrary notes are no longer exposed. Session and project IDs are opaque hashes; edited files and tools are counts. The source list contains failure reasons without local file paths. Project names are shortened, not anonymized.

The top-level `days` array was removed because its whole-session buckets could be mistaken for daily spending. `period.mode` is `active_sessions_full_totals`. Adapt scripts that consumed the removed fields. Existing period, agent, project and session totals continue to cover the selected whole sessions. As in 0.1.0, partial running dollar figures are excluded.

### Update

Close PLER, reinstall from the checkout with `pip install --upgrade ./product`, then reopen it. Check `pler --version`. No remote distribution was published as part of this release.
