# Retained-log accounting contract — schema 2

PLER 0.2.6 describes the local agent records it can read. It does not reconcile a provider bill, prove complete account coverage or measure task quality. Periods select sessions by last activity and include their full retained totals.

## Identity and copies

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

## Numbers, models and events

Usage fields must be exact nonnegative integers representable by JavaScript (at most 2^53−1 per logged field). Required input/output fields cannot be omitted. Codex cache reads and writes cannot exceed total input; reasoning cannot exceed output. Claude cache fields are separate from new input. Reasoning is part of output and never added twice.

An invalid usage row is excluded and the affected source is reported, while valid rows remain. Missing optional cache fields mean zero as defined by the supported log format, not a general rule for missing data. Cumulative or conflicting model attribution uses the `unknown` model bucket. That bucket remains in totals; assigning the entire legacy session to the last model is forbidden.

Only metadata identities consumed by a Codex record type are validated. An unrelated `id` field in a skipped message cannot invalidate a valid usage record. Used response, turn, tool, session and compaction identities remain strict; malformed JSON remains invalid even in an otherwise skipped row.

Errors and aborts are event counts. A request can have several events; they are never presented as a percentage of unique failed requests. Logged work duration, record span and elapsed human working time are different concepts.

## Quality and provenance

Both JSON interfaces include `version`, `schema_version`, `parser_version`, `source_scope` and `quality`. The browser snapshot includes `scanned_at`; terminal JSON includes `generated_at`. Session rows also include quality flags and fixed, localized explanations. Flags describe retained records, not provider-wide completeness.

`tokens_complete`, `calls_complete`, `counts_complete`, `attribution_complete` and `models_complete` distinguish the affected dimensions. Missing/unreadable sources make the selected token total incomplete. Incomplete token or ownership data suppresses concentration and session-length comparisons. Observations do not establish waste, savings or a model's relative quality.

Schema 2 changes session grouping/counts and model attribution. Consumers must check the schema and quality fields. Old exports are not recomputed automatically. Parser-helper changes invalidate affected metadata caches; the next read rebuilds them from logs.

## Local access boundary

The startup address carries a random per-process access token in its URL fragment. The page removes the fragment and retains the token in tab session storage; report reads, exports and actions require it. The public root page and health check do not disclose it. Restarting invalidates the previous token; use the new startup address. This is access to one local process, not user accounts, team roles, SSO or OS-level isolation. A process that can read the user's terminal, browser state, memory or local logs is outside this boundary. Do not share the startup link.

Configured log roots and the cache folder must be local. Discovery rejects network spellings (two leading slashes or backslashes in any mix) before filesystem probing and does not follow user symlinks or Windows junctions. On macOS and Linux, links owned by root are followed because the operating system makes them (macOS `/var` and `/tmp`, `/home` on some Linux systems); a user-owned link, such as a dotfiles-managed `~/.claude`, is still refused and reported. Windows never trusts a link by owner. A `PLER_CACHE_DIR` or default cache base on a network or link location disables the metadata and quota caches instead of redirecting them; reading still works, more slowly. Unsupported/unreadable locations are reported. This does not prevent a malicious process racing filesystem changes. PLER has no supported shared-server deployment.
