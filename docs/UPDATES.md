# Windows portable updates — desktop format 2; historical format 1

Desktop beta 0.9.28 uses updater compatibility 2. Usage/work/backup formats stay
unchanged. Electron requires bounded 256 MiB compressed, 768 MiB expanded and 256 MiB member
limits. The website/feed alignment is recorded in reports/beta-alignment-v1; older release bytes remain unchanged. Transition from 0.2.31 requires manual
extraction into a new folder. Desktop restart keeps --desktop, candidate probes require the
desktop executable, and health is unavailable until the new window reports its document loaded.
Clean Windows update/rollback acceptance is the final pending task.

Below is the original format 1 lifecycle, retained in format 2 unless noted above.

0.2.31 adds a user-triggered update check and **Download and update** inside the Windows x64 portable app. Automatic checking on launch is an explicit choice, initially off; the app installs only after a user click. Versions without this updater need one manual upgrade. Python wheels and other platforms remain outside this installer.

## User data and restart

The updater verifies the release signature, exact size and SHA-256 of the whole ZIP, every package member and per-file hash. It refuses an incompatible usage schema, work component, backup envelope or updater format. It never interprets a newer backup as compatible with an older reader.

A checked private metadata backup is prepared before the app is closed. The stable launcher and baseline runtime remain in place. A verified new version is prepared under `.pler-versions/VERSION`; `.pler-current` selects it through an atomic file replacement. An unfinished `.pler-pending` journal selects the prior known version on the next ordinary launch. Native `PLER.exe` and terminal `PLER.cmd` use this same selection. Private metadata stays in its existing chosen folder, including `--data-dir`.

Only the updater's own child is stopped if startup fails. Other instances are never killed; shared/exclusive installation leases prevent switching while another instance is running. The worker performs a read-only candidate/backup probe and checks the new local health/version endpoint before accepting it. A failed start switches the pointer back and reopens the previous app. It **does not restore the old backup over newer data**. Automatic data-format migrations are not supported by format 1; those releases require a separate manual migration procedure.

Prepared staging directories `.pler-update-*` beside the installation contain the checked backup, worker and result. Windows ACLs restrict them to the current user and SYSTEM before any private data is written. They are intentionally retained for recovery, are not anonymous and must not be sent to support. Old version directories are retained too. They can require substantial disk space. Inspect and privately preserve needed recovery material before manually removing a known completed staging directory; never delete an active update or the current version. Automatic retention cleanup is not part of this release. Removing the extracted app does not remove separately retained private data or recovery staging.

The automatic-check preference is stored locally in `update-choice.json` and survives package updates. It is not included in the existing metadata backup envelope; restoring into a fresh data folder defaults to manual checks. A dead update guard is reclaimed only when neither its parent nor its prepared worker is alive. Unknown/live guard owners remain protected.

## Network and trust

Normal usage analysis and status reads make no external request. Explicit checks, or an opted-in check at launch, read a bounded signed release from the fixed PLER HTTPS origin. A click downloads only the release's matching fixed package URL. No agent log, conversation, project path, report or account secret is sent. As with any HTTPS request, the hosting service sees normal connection information. Requests have bounded sizes/deadlines, system TLS trust and no redirects; offline failure leaves the current app usable.

Release envelopes use RSA-3072/SHA-256 signatures verified by Windows CNG against keys embedded in the installed app. Downloaded metadata cannot supply a replacement trust key. Expiration and locally remembered release versions reject stale/older feeds. A signature on release metadata is **not a Windows Authenticode signature on PLER.exe**; the early-beta executable remains unsigned. Never bypass a system security warning.

## Maintainer release procedure

1. Review the exact source and candidate; run the compatibility gate, meaningful source/UI/installed tests and native update/recovery acceptance. Preserve old immutable download URLs. Use a fresh version and matching filename.
2. Build the portable candidate with `tools/build_windows_portable.py`; it includes TLS and Windows CNG support. Create and test the matching wheel separately. Keep the baseline launcher compatible with updater format 1, or require a manual bootstrap upgrade.
3. `tools/update_release.py sign --private-key OWNER_DPAPI_FILE --package ZIP --version VERSION --output FEED_JSON --notes-en TEXT --notes-tr TEXT` produces a signed envelope. The owner key stays outside application/Site source in a Windows current-user DPAPI file. Never print, publish or bundle it. Preserve a protected owner-key recovery strategy before changing Windows profiles/machines; losing the key can require a manual client bootstrap. Existing clients must trust a key before it signs their next release.
4. Stage the accepted ZIP/wheel, signed `/updates/windows-x64/early-beta.json`, checksum list and EN/TR source in the launch Site. Its `scripts/release-policy.json` pins public keys, expected version/formats and immutable download hashes. Append new artifact pins; never rewrite old ones to make a check pass. Run `node --test scripts/check-release.test.mjs` and `node scripts/build.mjs` there. The ordinary build always invokes the offline consistency gate and fails on signature/expiry, package/wheel/version/format or page mismatches. Use the same checked source for Sites packaging; failed checks must stop publication. Publish the exact ZIP and matching feed together, then verify live bytes, signature and both language pages. No telemetry, outreach or unattended installation is authorized by publishing the feed. A passing consistency gate does not replace native update/recovery or independent platform acceptance.

Tests use invented releases/records and temporary fixture keys. Native recovery acceptance includes successful switches, failed startup, another instance and an interrupted selection journal. These are developer-machine proofs; physical power-loss/storage guarantees, clean-machine acceptance, full CI and Windows code signing remain separate work.
