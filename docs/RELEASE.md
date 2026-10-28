# Release and support gates

This is the maintainer's release procedure. It is not a statement that a public release exists. The product is a personal application reading retained logs on the same computer. It has no team identity, access roles, shared server, complete account ledger or billing reconciliation.

## Evidence required for a release

| Gate | Available evidence | What still counts as completion |
|---|---|---|
| Reader correctness and privacy | Synthetic regressions, local package checks and dated reports in `../../reports/` | All tests pass on the exact candidate; unexplained totals and unsupported histories remain labelled incomplete |
| Windows source/wheel | Local Windows Python 3.9/3.12 runs | Fresh environment accepts the candidate; browser, export, restart and uninstall checks pass |
| Windows without Python | 0.2.5 x64 candidate built offline; on the developer machine it ran with no Python on `PATH` (self-check, terminal report, local server) | Run that exact artifact on a clean Windows account/machine with no Python and no developer checkout; record architecture and hash |
| macOS and Linux | Linux: full suite green on WSL2 Ubuntu, Python 3.14.4, including a macOS-style system-link temporary folder. macOS: not run | Actual green runs on native Linux and macOS and a real browser acceptance on each; a Windows or WSL run is not evidence for macOS |
| Fast decoders | Python 3.14 `compression.zstd` exercised by the full suite on WSL2 Linux; optional `zstandard` only through mocked interfaces | Optional `zstandard` and each release platform's 3.14 decoder pass the same valid/corrupt corpus |
| Accessibility and browser downloads | Existing keyboard, narrow-layout and browser-logic checks | Physical browser/screen-reader matrix in [ACCEPTANCE.md](ACCEPTANCE.md) is completed |
| Useful professional work | Proposed tasks and measures | A real professional pilot meets the criteria in [PILOT.md](PILOT.md); no participant results have been invented |
| Distribution rights and identity | No product distribution license or publisher decision recorded | Owner approves the license, public name, publisher identity, channels and support contact |
| Signing and clean update | No claim of a trusted publisher signature | Signed final bytes, signature verification and clean install/update/remove evidence, using the approved publisher |

The quality register remains authoritative about specific known defects. A prepared test procedure or CI file is not a passed gate. Evidence for the rows above: [0.2.5 completion report](../../reports/completion-v1/REPORT.md).

To rebuild the private Windows candidate: `python tools/build_windows_portable.py --runtime <existing CPython 3.12 folder> --compiler <Windows .NET csc.exe> --output <new folder>`. It downloads nothing, refuses to overwrite and writes a manifest of SHA-256 hashes plus a ZIP next to the folder.

## Candidate procedure

1. Stop the running application. Build from `product/` after the full Python and Node suites pass. Record application, parser and schema versions; keep a copy of the exact candidate and its SHA-256.
2. Build without product dependencies: `python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist`. Build tools must already be available for an offline build. This command does not install Python or signing tools.
3. Install only that wheel into a new environment with `python -m pip install --no-index --no-deps <candidate.whl>`. Test the installed package, not an accidental checkout on `PYTHONPATH`. Check `pler --version` and confirm imported files are inside the new environment.
4. Follow [ACCEPTANCE.md](ACCEPTANCE.md) using invented logs before allowing a real pilot. Keep failing checks open; changing a label does not complete a test.
5. Finish the owner's decisions below. Keep test evidence with the artifact. Only publish the tested, approved artifact; this procedure itself performs no upload or publication.
6. Record the channel, version, artifact hash, compatibility, known limits and withdrawal route. Never include real transcripts, startup access links or local source paths in public evidence.

For a local update, stop PLER, install the new wheel in the same environment and restart from the new startup link. If the new version fails, stop it and reinstall the retained previous wheel; the original agent logs are unchanged. Metadata caches can rebuild. Old JSON exports keep their original parser/schema interpretation.

## Platform CI

[The prepared workflow](../.github/workflows/quality.yml) is manual and currently unexecuted. It belongs at `.github/workflows/quality.yml` when `product/` is the Git repository root. The outer workspace is not currently a connected repository. If a larger repository is used instead, adjust the checkout working directory before enabling it.

The main matrix runs Windows, macOS and Linux on Python 3.9, 3.12 and 3.14, plus Node browser-logic tests. Each job builds a wheel, creates a fresh environment, installs offline from that wheel, runs installed tests, checks the version and uninstalls. Three separate Python 3.12 jobs exercise the optional `zstandard` reader. Test inputs are synthetic fixtures; no provider accounts, model calls or credentials are required.

CI setup downloads its runners/runtimes and test build dependencies when dispatched. It does not constitute an offline machine acceptance, browser/screen-reader test, code signing or a professional pilot. This workspace has not dispatched it. Action versions and usage were checked against the official [checkout](https://github.com/actions/checkout), [setup-python](https://github.com/actions/setup-python), [setup-node](https://github.com/actions/setup-node) and [workflow shell](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsshell) documentation on 28 October 2026. Python 3.14's decoder is an optional standard module according to the [Python documentation](https://docs.python.org/3.14/library/compression.zstd.html); the CI job deliberately fails if it is absent instead of silently testing the fallback.

## Owner decisions before distribution

- Choose the distribution license and confirm ownership/redistribution rights for product code, bundled runtime, fonts and optional libraries. No license grant is implied by this repository's current absence of a product license. The unrelated experiment fixture licenses are not PLER's license.
- Confirm a public name/package identifier and its availability in the intended channels. Source install commands do not reserve a PyPI name. Do not tell users to install an unverified public package named `pler`.
- Identify the publisher and signing credentials and designate the public support/security contact. Do not invent an organization, support SLA or trusted signature.
- Decide which exact operating systems, architectures, Python/runtime versions and browsers are supported for that release. Label other combinations experimental until actually tested.

## Evidence record

Use one row per actual check: date, candidate version/hash, OS/architecture/runtime/browser, fixture set, expected result, observed result, pass/fail, evidence link and tester. Leave unexecuted rows as **not run**. Record failures and withdrawn candidates; never replace an observed failure with the planned result.
