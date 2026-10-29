# Release and support gates

This is the maintainer's release procedure. It is not a statement that a public release exists. The product is a personal application reading retained logs on the same computer. It has no team identity, access roles, shared server, complete account ledger or billing reconciliation.

**Current private candidate: 0.2.14, 29 October 2026 — source, installed package and kit verified.** Tested implementation commit `6f10365d7221984ac098a95e59f97186b0f39b07` passed the [12-job CI run](https://github.com/OguzayYildiz/pler/actions/runs/40959556534). The [current report](../../reports/lowlevel-v1/REPORT.md) records exact artifact hashes, synthetic before/after checks and browser acceptance. Subsequent documentation edits do not change the tested application bytes. No real professional pilot, clean-machine acceptance, trusted application signature or public release has been recorded.

## Evidence required for a release

| Gate | Available evidence | What still counts as completion |
|---|---|---|
| Reader correctness and privacy | Synthetic regressions, local package checks and dated reports in `../../reports/` | All tests pass on the exact candidate; unexplained totals and unsupported histories remain labelled incomplete |
| Windows source/wheel | 0.2.14: local Python 3.9/3.12/3.14 tests; Windows CI on all three versions passed source and installed-wheel acceptance, version check and uninstall. Installed files match all 43 source files byte for byte | Browser/export/restart checks on all selected supported Windows desktop combinations |
| Windows without Python | 0.2.14 kit with bundled CPython 3.14.10 and no Python on `PATH` opened the invented demo, returned expected counts, served versioned offline help and closed cleanly. Previous performance measurements are historical, not a speed guarantee for this artifact | Run these exact bytes on a clean Windows account/machine with no Python and no developer checkout; record architecture and hash |
| macOS and Linux | 0.2.14 CI source and installed-wheel acceptance passed Python 3.9, 3.12 and 3.14. WSL2 Ubuntu Python 3.14.4 passed 487/487 | Real browser acceptance on macOS and a Linux desktop |
| Fast decoders | 0.2.14 standard-library `compression.zstd` and optional `zstandard` passed the suite on Windows, Linux and macOS CI | Repeat when application bytes change |
| Accessibility and browser downloads | 0.2.14 installed candidate: English/Turkish, quality navigation, outside-filter session, preserved selection, actual masked JSON download, offline help, clean close and 375 px without page overflow. Node 32/32 | Physical browser/screen-reader matrix in [ACCEPTANCE.md](ACCEPTANCE.md) is completed |
| Useful professional work | Proposed tasks and measures | A real professional pilot meets the criteria in [PILOT.md](PILOT.md); no participant results have been invented |
| Distribution rights and identity | No product distribution license or publisher decision recorded | Owner approves the license, public name, publisher identity, channels and support contact |
| Signing and clean update | No claim of a trusted publisher signature | Signed final bytes, signature verification and clean install/update/remove evidence, using the approved publisher |

The quality register remains authoritative about specific known defects. A prepared test procedure or CI file is not a passed gate. Current completed evidence is the [0.2.14 report and artifact checks](../../reports/lowlevel-v1/REPORT.md); the [0.2.12 report](../../reports/reedit-v1/REPORT.md) and [0.2.5 completion report](../../reports/completion-v1/REPORT.md) are historical. User-facing help and the accounting contract are bundled inside the application, so source-relative evidence links are not required for using installed help.

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
