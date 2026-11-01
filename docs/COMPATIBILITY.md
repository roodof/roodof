# Reader and price compatibility review

Run the maintainer release gate from the product checkout:

```text
python tools/check_compatibility.py
```

Success is exit 0 with `ok: true`; drift or an expired review is exit 1 with fixed reason codes. The tool reads this checkout and the imported package. It never discovers agent logs, reads credentials, queries a provider, calls a model or updates prices. `--as-of YYYY-MM-DD` is for reproducible audits/tests; the release workflow uses today's UTC date. Runtime pricing continues showing its bundled date; this gate is not a runtime expiry rule.

## Reviewed contracts

[`compatibility.json`](compatibility.json) records the parser/schema, a normalized executable AST fingerprint, independently reviewed API/plan facts, official URLs, a fixture checksum and named regression controls. Comments/docstrings/formatting do not change the fingerprint; executable reader/accounting/cache/archive/pricing/plan changes require review. Fingerprints normalize supported Python AST versions. This catches accidental drift; it is not a signature or protection from a maintainer rewriting both code and review.

[`cases.json`](../tests/fixtures/compatibility/cases.json) contains **22 invented cases with independent expected counts and price coverage**. Every case runs cold, from a warm metadata cache and from verified deleted-source archive evidence. The matrix includes stable/duplicate Codex responses, cumulative-only formats labelled 0.152/0.155, per-response format labelled 0.163, malformed usage, unknown models/metadata, unlisted dated IDs, unknown write lifetime, Claude content-block copies, invalid split/modifiers and conflicting price witnesses in both orders. Version strings are fixture evidence, not executed client binaries or a guarantee for every event in those releases. Claude fixtures establish field contracts without claiming a client version. Ignoring unknown metadata does not establish future usage-schema or complete account coverage.

The Python suite executes the cases and named accounting/pricing/cache/period regressions. Installed acceptance checks the imported installed package against the reviewed evidence. The workflow discovers every `tests/test_*.cjs` suite, including later coverage/work/plan controls.

## Price scope and freshness

Official API and plan facts were checked on **2026-11-01**; URLs are in the registry. All 26 listed model IDs, aliases and approved prompt tiers are reviewed. New/missing models, changed rates/limits, changed plans and nonfinite/negative/boolean rates fail the gate. Public global standard-tier USD equivalents are not bills, credits, tax, actual payments or switching savings. Codex Pro's unlogged tier has no invented price/capacity ratio.

- Claude uses consistent logged 5m/1h writes. Only absent split evidence uses the API's default 5m behavior. An invalid split preserves valid token totals but withholds the response price. Invalid/unsupported speed, region or service-tier evidence cannot disappear during sanitization and become standard pricing. Region `not_available`, which Claude Code logged for every response before it reported regions (until 2026-10-08 on the review machine), is priced like an absent region; only US-only `us` has a published 1.1x price. All copies carrying selected usage must agree on their computed price, regardless of row/file order.
- GPT-6 writes have 30m/12h rates. Current retained Codex counts have no lifetime split: a positive write count leaves the whole response unpriced. Zero-write responses retain ordinary input/cache-read/output pricing. GPT-5.3's earlier no-extra-write-charge behavior remains covered. Codex uses exact reviewed IDs; arbitrary dated suffixes do not inherit a rate. Claude's existing dated-family policy remains explicit.
- Unpriced responses remain in token/call totals and reduce token-weighted price coverage; zero coverage is unknown, not free. Codex standard-tier pricing is an assumption because that tier is not in the retained contract.
- A price review older than **30 UTC days** blocks release. A reader review older than 90 days also needs renewal. These are PLER maintenance policies, not proof that prices stayed unchanged between reviews.

## Intentional changes

1. Reproduce the change with invented or explicitly permitted anonymized records. Keep expected totals independent of the reader. Include malformed/unknown cases, cache/archive replay and privacy canaries.
2. Manually fetch official documentation. Verify model IDs/aliases, prompt boundaries, lifetimes, modifiers and plan assumptions. Keep unestablished prices/formats unpriced or limited.
3. Review and update facts, source dates/URLs, fixture checksum, regressions and executable-code fingerprint. There is deliberately no automatic approval command.
4. Change `PARSER_VERSION` when interpretation or price-confidence meaning changes. Reader keys independently rebuild affected caches and label older archive projections. Never promote old-reader evidence into certainty; old exports retain provenance and cross-parser follow-ups remain unresolved. Date pure table revisions separately.
5. Run this gate and relevant Python/Node acceptance on the exact candidate, then the release procedure. Passing does not publish, sign or prove clean-machine/platform/pilot acceptance.

Current correction: `accounting-2026-11-01.1`, usage schema 2. Work component 3 and backup envelope are unchanged. Workflow dispatch remains manual; this task does not retry account-blocked CI.
