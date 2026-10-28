# Support and problem reports

PLER currently describes retained Claude Code/Codex records on one computer. It is not an account bill, team service or complete history guarantee. A quota may be unknown or stale; an unknown project/model is preferable to an invented allocation. Start with the quality warning and [accounting contract](../ACCOUNTING.md) when a number looks wrong.

## First checks

- Confirm the running version with `pler --version`. Stop and restart after an update; use the new complete startup address in a manually opened tab.
- Check the last read time and found/unreadable source counts. `Read logs again` rereads retained files; it does not contact the provider to update an account meter.
- Check period/agent/project filters. The period selects sessions by their last activity, then includes their full retained totals. Search narrows only the session list.
- If no records appear, confirm the agent has written supported local logs and the configured log root is local. A network/junction path may be intentionally skipped. The app should retain readable data and report affected files when reading is incomplete.
- For a prepared export that did not save, use **Download again** and inspect browser downloads. The JSON still contains short project names, times and model names; review it before sharing.
- For a cache problem, prefer an isolated temporary `PLER_CACHE_DIR` for diagnosis. Deleting only PLER's cache rebuilds metadata later; never delete Claude/Codex log directories to troubleshoot PLER. Do not share the private cache file.

## Privacy-conscious issue template

Copy this text into the support channel chosen by the maintainer. No public contact or response-time guarantee has been established yet.

```text
Application version:
Parser/schema version (from the JSON header, if available):
Operating system and architecture:
Python/runtime version; source, wheel or portable installation:
Browser/version, if the problem is on the page:
Agent and agent client version, if known:

What I was trying to do:
Steps using invented data, if possible:
Expected result:
Observed result:
Does it repeat after closing and reopening PLER?
Quality warning code/text (remove any private names):
Approximate file/session count and first/cached read duration, if relevant:
Relevant filters:
Sanitized screenshot or minimal invented fixture:
```

Do not include a startup address with `#access=`, access headers, browser session storage, actual prompts/replies/commands/tool output, agent credentials, complete log/cache files, raw local paths, or private repository names. Prefer an invented record that reproduces the issue. Review screenshots and JSON yourself; PLER exports are reduced, not anonymous.

## Triage and compatibility

Maintainers should first reproduce a report with synthetic data and the stated application/parser version. Treat wrong totals, privacy boundary failures, broken updates or a crash as release blockers. Preserve observed and expected results, the exact artifact hash and an independent regression. When the retained evidence cannot prove a number or attribution, keep the uncertainty visible instead of inventing a repair.

Back up any exported reports needed for audit. An export records the parser/schema used at that time; later updates do not rewrite it. Retain the previous installer/wheel for rollback until the new candidate has passed the acceptance procedure.

Shared computers, multiple provider accounts in one log root, SSO/roles, shared-server hosting, untested operating systems and Claude desktop quota capture are outside the currently demonstrated personal-local scope. Do not ask users for provider credentials or imply that granting them would close a retained-log gap.
