---
version: alpha
name: Roodof Workbench
description: A dense local record browser for Claude Code and Codex work. Monochrome surfaces, explicit provenance and keyboard-first navigation.
colors:
  canvas: "#101012"
  sidebar: "#141416"
  surface: "#18181b"
  raised: "#202023"
  hover: "#27272b"
  selected: "#2c2c31"
  text: "#f4f4f5"
  secondary: "#b0b0bb"
  muted: "#9797a1"
  border: "rgba(255,255,255,0.08)"
  border-strong: "rgba(255,255,255,0.16)"
  highlight: "rgba(255,255,255,0.05)"
  focus: "#a1a1aa"
  success: "#85c49a"
  warning: "#dfb96f"
  danger: "#eb998d"
  primary-bg: "#eeeeef"
  primary-fg: "#18181b"
  accent: "#e07a55"
  agent-claude: "#e07a55"
  agent-codex: "#e4e4e7"
  heat-1: "#302a27"
  heat-2: "#493e3a"
  heat-3: "#6f5f58"
  heat-4: "#a18072"
  heat-5: "#d4b3a5"
  calls-claude: "#4fa8bd"
  calls-codex: "#cfe3e8"
  calls-heat-1: "#1d2b30"
  calls-heat-2: "#27424b"
  calls-heat-3: "#356774"
  calls-heat-4: "#5097a8"
  calls-heat-5: "#a6d3de"
typography:
  heading:
    fontFamily: Manrope
    fontSize: 20px
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: -0.03em
  body:
    fontFamily: Segoe UI
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
  metadata:
    fontFamily: Segoe UI
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.5
  numeric:
    fontFamily: Consolas
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
rounded:
  control: 5px
  panel: 7px
  overlay: 10px
spacing:
  unit: 4px
  compact: 8px
  control: 12px
  panel: 16px
components:
  button:
    height: 32px
    padding: 0 10px
    radius: 5px
  input:
    height: 32px
    padding: 0 10px
  sidebar:
    width: 188px
  drawer:
    width: 420px
  session-row:
    height: 64px
  spring:
    type: spring
    stiffness: 400
    damping: 30
---

# Product and visual direction

Roodof is a Windows desktop tool for finding an agent session, inspecting its recorded use,
and connecting it to a named piece of work. Its signature is the record row: a recognizable
work/project name, agent and time, aligned token count, factual record status, recorded model and known/unknown call count. Real user
work takes precedence over promotional copy. A test result describes a recorded test, never overall code quality.

The user selected Linear/Vercel/Raycast craft: compact controls, precise alignment, shallow
surface layers and physical selection feedback. These are Roodof decisions inspired by those
products, not claims to reproduce their official internal design tokens.

## Data colors

Charts may tell the two agents apart: Claude Code uses the clay of the Roodof mark (`agent-claude`),
Codex a light neutral (`agent-codex`). These appear only in data marks and agent legends, never in
navigation or status. Intensity maps (when you work) use a single warm ramp, `heat-1` to `heat-5`,
taken from the Radix Colors bronze dark scale (steps 4, 6, 8, 9, 11; github.com/radix-ui/colors, MIT),
so each step is perceptually even on the dark canvas. When the chart counts model calls instead of tokens it
switches to a cool set (`calls-claude`, `calls-codex`, `calls-heat-1` to `calls-heat-5`; Roodof's own values), so the
two views cannot be mistaken for each other; agent order and legend stay the same. Status colors keep their meaning.

## Surface hierarchy and density

Canvas < sidebar < panel < popover/selected surface. Separation uses the documented 1px
borders and a single inset top highlight. Drop shadows do not carry ordinary panel hierarchy.
Standard panels use 12–16px padding; main gutters are 20px. Avoid wrapper cards around every
piece of data. Session rows and field groups carry the structure. Semantic colors are reserved
for recorded success, error, warning and data limits. One accent, the clay of the mark (`accent`), marks
the current place, a checked box and keyboard focus; everything else in navigation stays monochrome.
Body text uses the system variable face (Segoe UI Variable Text, then Segoe UI). Figures use the same face
with tabular digits; the monospace face is kept for commands, paths and model names.

## Primitives and feedback

Buttons have default, hover, pressed, keyboard-focus, disabled and busy states. Primary action
is light on dark. Secondary controls use a crisp border and top highlight. Numeric UI uses
`font-variant-numeric: tabular-nums`. Focus is a visible 1px neutral ring, never removed.
Navigation and filter segments use actual Motion `layoutId` indicators in small React islands.
The existing controller continues to own filters, authenticated writes and session identities.
No clickable-looking surface is added unless it performs a real action.

## Motion

Selection uses a spring with stiffness400/damping30. Row entry is short and staggered40ms,
limited to the first eight newly displayed rows. Drawers/dialogs enter with short spring
translation; decorative looping animation is excluded. Pointer feedback starts immediately.
Reduced-motion bypasses translation, spring and staggering. Focus and action success never
wait for an animation. Loading distinguishes the initial skeleton from refreshing an existing
snapshot. Old data stays visible during refresh, and empty-state actions use existing handlers.

## Hard exclusions

First use has one next-step button, selected from completed record-read state. Reading stays locked;
ready sessions, missing records and read issues lead to sessions, sources and diagnostics respectively.
Retry/help/skip stay in a disclosure, with readable sessions retained as an explicit error alternative.

An empty search shows its actual period/agent/project scope and a relevant next action. Broadening
changes one constraint and keeps the user's text and other choices. Empty virtual table space is
removed; two visible actions lead to optional alternatives. Missing sources, unreadable records,
unusable files and failed reads have distinct copy. Never imply an unverified source is missing.

Settings use three task tabs: record sources, usage alerts, backup/support. Existing form nodes
stay mounted across tabs; operational tools open independently and shortcuts reveal their target.
Session work linking starts collapsed, keeps linked names visible, and shows only the selected
existing/new-work form. Native disclosure semantics, keyboard tabs, preserved drafts and truthful
saved state take precedence over decorative motion. These controls keep the existing token palette.

The session task is **find → understand recorded usage → set an alert**. Search keeps a visible
label and `/` keyboard access. New views start with session, token total and record status;
explicitly saved columns remain authoritative. The inspector leads with recorded tokens,
API price coverage and a three-part input/cache/output strip. Missing and partial values are
labelled rather than estimated. Alert editing opens on request; saved alert status stays visible.
Methods, model breakdown and full record fields follow the primary actions. Small operational
copy uses at least 12px in this flow. Virtual row selection must touch rendered rows only.

No purple/indigo/pink gradients, neon blobs, hero cards, giant metrics without a decision,
32–40px standard card padding, thick borders, heavy card shadows, static selected-state jumps,
fake prompts/log contents, invented session names, invented savings or dead demonstration controls.

## Sources and their application

- [anti-slop](https://github.com/miqdadbadjuber/anti-slop): purposeful visual treatments and real interactions. README saved as `.anti-slop-rules.md`; the filter is archived under docs/design-references.
- [Google DESIGN.md format](https://github.com/google-labs-code/design.md/blob/main/docs/spec.md): YAML tokens plus rationale. The requested root `/main/DESIGN.md` is absent; this file is authored for Roodof using its actual format specification.
- [oh-my-design](https://github.com/kwakseongjae/oh-my-design): sourced values and role separation; archived Vercel/Raycast references are inspiration, not Roodof defaults.
- [coss ui / Origin UI](https://github.com/cosscom/ui/tree/main/apps/ui/registry/default/ui): compact native controls, inset highlights, visible focus/pressed/busy states. The supplied cosscom/coss now contains a wider platform; cosscom/ui has the directly relevant UI sources.
- [OpenDesign](https://github.com/nexu-io/open-design): reusable design-system roles and Raycast surface reference, adapted to a local record tool.
- [Motion Primitives](https://github.com/ibelick/motion-primitives/blob/main/components/core/animated-background.tsx): shared-layout selection pattern. Roodof implements its own small navigation/filter components using installed Motion; it does not claim the complete React component kit is installed.

Source URLs and SHA256s are saved in docs/design-references/sources.json and patterns.json.
`frontend/tokens.json` emits CSS variables at build time. `frontend/workspace.css` and
`frontend/sessions-grid.css` consume those variables. This replaces the old stacked overrides.

## UX5/6 — terminology and supporting-screen type

Account limits / Hesap kotaları are provider-set limits from the latest local samples, not a live account query. Usage alert / Kullanım uyarısı is a user-set per-session token or USD threshold; it does not change provider limits or stop an agent. API price equivalent / API fiyat karşılığı is priced recorded usage, not a bill or subscription spend. Use the app dictionary for shared frontend names; keep CLI, native notifications and offline help aligned. Actual unit API prices and monthly plan prices retain their separate meanings.

Supporting surfaces inherit `--ui-body-size:13px`, `--ui-label-size:12px`, `--ui-section-size:15px`, `--ui-copy-line:1.6`, `--ui-section-gap:16px` and `--ui-control-gap:8px` from the workspace. No 10/11 px explanation, path or metadata labels. Large data values, icons and page headings keep their distinct roles. Source folders, saved alerts, inspector, recovery, history, diagnostics, reconnection, updates and offline help share these roles. Paths wrap; quota status badges may wrap rather than squeeze headings. Help has no sidebar and retains local assets only. Keep the current 25 color tokens unchanged.
