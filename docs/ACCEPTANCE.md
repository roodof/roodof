# Installation and browser acceptance

Run these checks on the exact candidate artifact. Use invented logs and an isolated temporary user/cache folder first. Do not point a general release test at a customer's real home folder, alter their Claude settings or run a provider/model experiment. Tests of the optional status-line installer require an explicitly disposable settings file.

## Source/wheel smoke check

From `product/`, with Python and build tools already installed:

```text
python -m unittest discover -s tests
node --test tests/test_access.cjs tests/test_quota_view.cjs tests/test_usage_actions.cjs
python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
python -m venv .qa-venv
```

The Python tests need the product's `src` directory on the import path. For the source run use `PYTHONPATH=src` in your shell, or run the source-test command from the CI workflow. The installed run below must remove that override.

Use `.qa-venv\Scripts\python.exe` on Windows or `.qa-venv/bin/python` on macOS/Linux as `<qa-python>`. Substitute the actual wheel filename for `<candidate.whl>`:

```text
<qa-python> -m pip install --no-index --no-deps <candidate.whl>
<qa-python> -m pler --version
<qa-python> -c "import pathlib,sys,pler; assert pathlib.Path(pler.__file__).resolve().is_relative_to(pathlib.Path(sys.prefix).resolve())"
<qa-python> -m unittest discover -s tests
<qa-python> -m pip uninstall --yes pler
<qa-python> -c "import importlib.util; assert importlib.util.find_spec('pler') is None"
```

Do not put the source tree on the installed run's `PYTHONPATH`. A passing import from `src/` does not validate the installed wheel.

## Clean machine and update/remove

| Check | Expected result |
|---|---|
| New local account; no developer checkout, Python, `pip` or package manager on PATH | The Python-free artifact starts using its bundled runtime without an install/download prompt |
| Path includes spaces and non-ASCII letters | Start, cache, export and close work; no guessed short path required |
| Standard user without administrator rights | Installation/start succeeds in the documented user location, or gives an actionable error without partial setup |
| First run with no agent logs | The empty state explains the scope; no invented zero balance, model call or account request |
| Run twice / occupied default port | Each startup gives its actual usable address; one process cannot close an unrelated listener |
| Candidate update over previous candidate | Old process is closed, new version/link is used; unchanged logs produce the same supported accounting result unless a documented parser correction applies |
| Roll back using retained previous artifact | Previous version starts; original agent records remain unchanged |
| Uninstall/remove | Executables and optional integration are removed as documented; user logs are untouched; retained cache/backup policy is stated |
| Signature and artifact hash | The final artifact hash and approved publisher signature verify on the target machine; unsigned candidates remain labelled unsigned |

A venv on a developer's computer is a useful package check, not a clean Windows/macOS/Linux or Python-free test. Disconnecting the network during the clean-machine test is useful when checking that the artifact does not download a missing runtime. Do not disable endpoint protection or bypass a browser/OS trust warning as a test shortcut.

## Browser and accessibility matrix

Run all tasks with the same invented fixture and record the browser/OS version. Required release combinations are chosen by the owner; suggested coverage is Edge and Chrome on Windows, Firefox on Windows/Linux, Safari on macOS, and an actual narrow touch device. Browser names in this plan are proposed coverage, not verified support.

1. Open from the complete startup address. A plain root page must not disclose the access token or grant private report access. Refresh/reopen the authorized tab, restart the application, and confirm only the new startup link reconnects.
2. Choose period, agent and project; confirm totals and downloaded JSON follow these filters. Search affects only the session list. An empty project or disappeared project recovers without leaving old totals labelled as the new selection.
3. Start an export, immediately change a filter or refresh, then export again. The prepared file must match its selection. Retry stays available when automatic download is blocked; the app must not claim that a file was saved merely because it was prepared.
4. Navigate using Tab/Shift+Tab and Enter/Space. Open and close session details with keyboard and Escape; focus remains visible and returns to the initiating control. Show more moves focus to newly shown rows. Refresh/export must not steal focus after the user moves elsewhere.
5. At 200% zoom and an actual narrow viewport, read all labels and values. The table may scroll in its named keyboard-focusable region; the page itself should not require sideways scrolling for primary controls. Check 400% zoom separately on the selected release browser.
6. With Windows NVDA and macOS VoiceOver, read the title, language, filter labels, loading/status changes, quality warnings, quota state, table headers, row actions, download result and dialog. Confirm no unreachable controls or focus trap. Automated DOM checks do not substitute for this run.
7. With reduced motion, forced colors/high contrast and dark/light OS settings, confirm visible focus, legible values, identifiable warnings and usable buttons. Check that no meaning depends on color alone.
8. Close PLER; controls become inactive and explain how to reopen. No provider API/model request or real Claude configuration change should occur during these tasks.

Record each task as **pass**, **fail** or **not run** with actual evidence. Screen-reader conformance and every-browser download support remain unverified until those runs occur.
