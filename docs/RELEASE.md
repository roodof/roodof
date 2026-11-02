# Release and support gates

This is the maintainer's release procedure. It is not a statement that a public release exists. The product is a personal application reading retained logs on the same computer. It has no team identity, access roles, shared server, complete account ledger or billing reconciliation.

**Latest local package, 2 November 2026:** 0.2.30 (source `ac263ea`, channel early-beta, unsigned) was built and checked locally but **not published**; see the [0.2.30 package report](../../reports/release-0.2.30-v1/REPORT.md). Windows ZIP SHA-256 `ea27190e4b5bfcc44982efe891939cbee9b9582e6b4b2b68e89cde9f41eaf310`, wheel `5133e5cd9a12926933a0b4f83c2ea4e835e01f7c4bd8feb82594825ab5c86869`. Publishing it is the owner's decision.

**Latest published package, 1 November 2026:** the recorded public early-beta package is 0.2.29, publisher PLER, support plersolutions1st@gmail.com; see the [package report](../../reports/first-use-v1/REPORT.md). Later Y02/Y03/Y04/Y05/E05 changes are in 0.2.30. Current source parser is `accounting-2026-11-01.1`, usage schema 2, work component 3. Old work-component readers cannot read format 3; retain a checked compatible backup before rollback. Source tests and earlier E04 timings do not validate new package bytes. Signing, product license, clean-machine/physical platform acceptance and real pilot remain open. Automatic updating remains deferred by the owner.

**Required offline review gate:** `python tools/check_compatibility.py`, using today's UTC date. [COMPATIBILITY.md](COMPATIBILITY.md) defines source/fixture review, official price-source facts, freshness and interpretation changes. The workflow runs the gate and discovers every browser suite; configuration is not a passed CI execution. The last recorded account-blocked CI is not retried by this work.

**Historical private candidate: 0.2.25, 30 October 2026 — verified private backup and new-folder recovery.** Final tested application source is `a78f0b6` (feature `9a428d6`, followed by module exit-code correction). The [current report](../../reports/backup-v1/REPORT.md) records exact hashes, deleted-source recovery through both packages, installed acceptance and actual browser download/check. Platform CI has not run for 0.2.25; the last known 0.2.24 [12-job run](https://github.com/OguzayYildiz/pler/actions/runs/41056121858) ran zero steps because GitHub reported account payment/spending limits. This is not a passed check for the new candidate. The user deferred advertising and participant recruitment until satisfied with the product; approximately $3/month is a tentative target, not a completed pricing or demand validation. No professional pilot, clean-machine acceptance, trusted application signature or public release has been recorded.

## Historical package evidence (0.2.25; not current source acceptance)

| Gate | Available evidence | What still counts as completion |
|---|---|---|
| Reader correctness and privacy | Synthetic regressions, local package checks and dated reports in `../../reports/` | All tests pass on the exact candidate; unexplained totals and unsupported histories remain labelled incomplete |
| Windows source/wheel | 0.2.25 feature source: 3.9 pytest 667 passed/13 skipped; 3.12 671 run/5 skipped; 3.14 680 run/4 skipped, no failures. Final module fix: 22 CLI/help checks on both 3.9 and 3.14. Final installed wheel: 672 run/5 skipped; all 51 source files byte-identical | Exact-candidate platform CI and remaining selected desktop combinations |
| Windows without Python | Final 0.2.25 bundled runtime with no Python on PATH: backup/check/new-folder restore, deleted-source totals/quality, verdict/quota times, actual local server, EN/TR help, private backup API roundtrip and clean exit | These exact bytes on a clean Windows account/machine without a developer checkout |
| macOS and Linux | Final 0.2.25 WSL2 Ubuntu Python 3.14.4: 681/681. No new macOS CI. Last successful matrix was 0.2.22, a different candidate | Exact-candidate CI plus physical macOS/Linux browser acceptance |
| Fast decoders | Local feature-source native-decoder tests passed where available; older-runtime skips recorded. Final Linux native decoder suite passed. No new optional-decoder CI | Optional `zstandard` and standard-library matrix on the exact candidate |
| Accessibility and browser downloads | Final installed 0.2.25: actual private backup saved and rechecked in browser, private scope, EN/TR and clean close; Node 47/47. Earlier full navigation/mobile evidence is historical | Full selected browser/download/mobile and physical screen-reader matrix in [ACCEPTANCE.md](ACCEPTANCE.md) |
| Retained history recovery | Final wheel and portable recover deleted-source totals/quality, verdicts and quota times into a new folder; existing target and damaged input refused; current data preserved | Same-machine/same-selected-roots recovery only; source relocation and in-place merging are not supported |
| Useful professional work | Proposed tasks and measures | A real professional pilot meets the criteria in [PILOT.md](PILOT.md); no participant results have been invented |
| Distribution rights and identity | Publisher PLER and support address recorded; product distribution license remains open | PLER and support are selected; owner still approves the license, distribution rights, channels and signing identity |
| Signing and clean update | No claim of a trusted publisher signature | Signed final bytes, signature verification and clean install/update/remove evidence, using the approved publisher |

The [active work register](REMAINING.md) and quality register remain authoritative. The table above is historical. Latest recorded package evidence is the [0.2.29 report](../../reports/first-use-v1/REPORT.md); later source evidence has its own candidate identity and does not replace installed acceptance. A prepared, queued or account-blocked workflow is not a passed gate. Installed help is bundled locally.

To rebuild the private Windows candidate: `python tools/build_windows_portable.py --runtime <CPython folder> --compiler <Windows .NET csc.exe> --output <new folder>`. Use the extracted official Windows embeddable package of CPython 3.14 or newer: verify its SHA-256 against the python.org release page and its Authenticode signatures first. The 3.14 standard-library zstd decoder makes the first read about three times faster than an installed 3.12 folder, which the tool still accepts. The tool downloads nothing, refuses to overwrite and writes a manifest of SHA-256 hashes plus a ZIP next to the folder.

## Candidate procedure

1. Stop the running application. Build from this repository's root (where `pyproject.toml` is) after the full Python and Node suites pass. In the enclosing workspace that root is named `product/`. Record application, parser and schema versions; keep a copy of the exact candidate and its SHA-256.
2. Build without fetching dependencies: `python -m pip wheel . --no-index --no-deps --no-build-isolation --wheel-dir dist`. Build tools must already be available. This command does not install Python or signing tools.
3. Install only that wheel into a new environment with `python -m pip install --no-index --no-deps <candidate.whl>`. Test the installed package, not an accidental checkout on `PYTHONPATH`. Check `pler --version` and confirm imported files are inside the new environment.
4. Follow [ACCEPTANCE.md](ACCEPTANCE.md) using invented logs before allowing a real pilot. Keep failing checks open; changing a label does not complete a test.
5. Finish the owner's decisions below. Keep test evidence with the artifact. Only publish the tested, approved artifact; this procedure itself performs no upload or publication.
6. Record the channel, version, artifact hash, compatibility, known limits and withdrawal route. Never include real transcripts, startup access links or local source paths in public evidence.

For a local update, stop PLER, install the new wheel in the same environment and restart from the new startup link. If the new version fails, stop it and reinstall the retained previous wheel; the original agent logs are unchanged. Rebuildable reader caches can be reset with `pler cache reset`, which preserves retained history. Do not delete the whole cache/data folder: metadata of already-deleted sources can exist only in its archive. Preserve a private archive backup when needed before update/rollback. Old JSON exports keep their original parser/schema interpretation.

## Platform CI

[The workflow](../.github/workflows/quality.yml) is manual (`workflow_dispatch`). Since 28 October 2026 `product/` is the root of a private GitHub repository and the workflow has run there; see the release gate table above for results. If a larger repository is used instead, adjust the checkout working directory before enabling it.

The main matrix runs Windows, macOS and Linux on Python 3.9, 3.12 and 3.14, plus Node browser-logic tests. Each job builds a wheel, creates a fresh environment, installs offline from that wheel, runs installed tests, checks the version and uninstalls. Three separate Python 3.12 jobs exercise the optional `zstandard` reader. Test inputs are synthetic fixtures; no provider accounts, model calls or credentials are required.

CI setup downloads its runners/runtimes and test build dependencies when dispatched. It does not constitute an offline machine acceptance, browser/screen-reader test, code signing or a professional pilot. It was first dispatched on 28 October 2026. Action versions and usage were checked against the official [checkout](https://github.com/actions/checkout), [setup-python](https://github.com/actions/setup-python), [setup-node](https://github.com/actions/setup-node) and [workflow shell](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsshell) documentation on 28 October 2026. Python 3.14's decoder is an optional standard module according to the [Python documentation](https://docs.python.org/3.14/library/compression.zstd.html); the CI job deliberately fails if it is absent instead of silently testing the fallback.

## Owner decisions before distribution

- Choose the distribution license and confirm ownership/redistribution rights for product code, bundled runtime, fonts and optional libraries. No license grant is implied by this repository's current absence of a product license. The unrelated experiment fixture licenses are not PLER's license.
- Confirm a public name/package identifier and its availability in the intended channels. Source install commands do not reserve a PyPI name. Do not tell users to install an unverified public package named `pler`.
- Identify the publisher and signing credentials and designate the public support/security contact. Do not invent an organization, support SLA or trusted signature.
- Decide which exact operating systems, architectures, Python/runtime versions and browsers are supported for that release. Label other combinations experimental until actually tested.

## Evidence record

Use one row per actual check: date, candidate version/hash, OS/architecture/runtime/browser, fixture set, expected result, observed result, pass/fail, evidence link and tester. Leave unexecuted rows as **not run**. Record failures and withdrawn candidates; never replace an observed failure with the planned result.
