# Professional pilot acceptance

**Ready-to-run kit (29 October 2026, rebuilt and checked as 0.2.12):** `pler demo` provides invented data for every task below, including the subsequent-edit observation. The [current kit evidence](../../reports/reedit-v1/REPORT.md) covers Windows portable and Python 3.9 wheel startup, counts and clean shutdown. The kit bundles both packages and participant guides and task sheets in Turkish and English. The facilitator guide with its measured answer key and the record template stay outside the participant kit. This check is not a completed professional pilot.

This is a proposed pilot protocol. It contains no completed interviews, customer endorsements or measured savings. Run it only after the release candidate passes local correctness/privacy/install acceptance, using participants who agree to the scope and how results are recorded.

## Question and participants

The question is whether a professional repeatedly makes a useful decision faster or more reliably with PLER than with their current method. More screens, token counts or a passing test suite do not answer it.

Recruit at least five professionals across individual development, a technical team lead and an operations/engineering manager. Include both Claude Code and Codex users and at least one participant who uses both. Each keeps private transcripts and credentials on their own machine. A team pilot uses personal installations; PLER does not provide team-wide dashboards or shared access.

## Tasks and evidence

| Task | Independent acceptance |
|---|---|
| Install and open the candidate without coaching | Record time, steps, failed attempts, intervention and whether the documented platform/runtime was available |
| Explain a session's token mix and quality warning | Participant distinguishes cache reads from new input, uncertainty from zero, and retained totals from account/billing totals |
| Find a named known session/project | Record success, time and mistaken filter/search assumptions; corroborate against a participant-approved local reference |
| Compare period and project selections | Participant explains that periods include full active-session totals, and search does not change the exported summary |
| Inspect a quota observation | Participant identifies its timestamp, reset/staleness and account-wide scope; does not mistake it for an an instant provider lookup |
| Investigate a suspected usage increase | Participant forms a specific, supportable next step; counts alone are not evidence of waste or model quality |
| Export a relevant summary | Participant checks selection, file save and private fields before sharing; can describe the export's limitations |
| Close, update and remove the candidate | No agent logs are changed; integration changes only with the participant's intended approval |

Use the participant's current tool/process as the comparison for the same tasks. Counterbalance task order across participants so practice does not always favor PLER. Do not require a paid model run just to create evaluation data; invented logs can establish the task before a participant optionally uses their existing history locally.

## Proposed pass/fail criteria

These are targets chosen before the pilot, not observed results:

- Every participant completes the privacy-critical tasks correctly: startup-link handling, quality uncertainty, account-versus-retained scope and export review. Any misleading critical interpretation requires a product correction and a fresh run.
- At least four of five complete session finding, filtering and export tasks without facilitator intervention.
- At least three of five choose to use PLER again for a specific recurring task during the following working week, with a reason tied to their own workflow. A polite positive comment is not repeated-use evidence.
- Record median task time and individual failures against the current method. Do not claim a time-saving percentage from this small pilot or hide participants who were slower.
- Any data loss, unintended settings change, private-data disclosure or unsupported confident total is a fail requiring investigation before broader distribution.

The pilot may show that PLER is not useful enough. Report that result and the failed tasks. Do not silently change the success criteria after seeing outcomes.

## Result record

For each pseudonymous participant record the candidate version/hash, environment, permitted data scope, comparison method, task outcomes/times, misunderstandings, interventions, actual repeat-use observation and withdrawal request. Keep transcripts, credentials, project names and complete exports out of the shared report. Set retention and access with the participants before collecting results.

No support service, enterprise certification, billing accuracy or guaranteed savings is promised by completing this small pilot. Its output informs the decision to improve, narrow the supported scope or proceed to a larger evaluation.
