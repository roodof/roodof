---
version: alpha
name: PLER Workbench
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
  agent-claude: "#e07a55"
  agent-codex: "#e4e4e7"
  heat-1: "#302a27"
  heat-2: "#493e3a"
  heat-3: "#6f5f58"
  heat-4: "#a18072"
  heat-5: "#d4b3a5"
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

PLER is a Windows desktop tool for finding an agent session, inspecting its recorded use,
and connecting it to a named piece of work. Its signature is the record row: a recognizable
work/project name, agent and time, aligned token count, factual record status, recorded model and known/unknown call count. Real user
work takes precedence over promotional copy. A test result describes a recorded test, never overall code quality.

The user selected Linear/Vercel/Raycast craft: compact controls, precise alignment, shallow
surface layers and physical selection feedback. These are PLER decisions inspired by those
products, not claims to reproduce their official internal design tokens.

## Data colors

Charts may tell the two agents apart: Claude Code uses the clay of the PLER mark (`agent-claude`),
Codex a light neutral (`agent-codex`). These appear only in data marks and agent legends, never in
navigation or status. Intensity maps (when you work) use a single warm ramp, `heat-1` to `heat-5`,
taken from the Radix Colors bronze dark scale (steps 4, 6, 8, 9, 11; github.com/radix-ui/colors, MIT),
so each step is perceptually even on the dark canvas. Status colors keep their meaning.

## Surface hierarchy and density

Canvas < sidebar < panel < popover/selected surface. Separation uses the documented 1px
borders and a single inset top highlight. Drop shadows do not carry ordinary panel hierarchy.
Standard panels use 12–16px padding; main gutters are 20px. Avoid wrapper cards around every
piece of data. Session rows and field groups carry the structure. Semantic colors are reserved
for recorded success, error, warning and data limits; navigation remains monochrome.

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

No purple/indigo/pink gradients, neon blobs, hero cards, giant metrics without a decision,
32–40px standard card padding, thick borders, heavy card shadows, static selected-state jumps,
fake prompts/log contents, invented session names, invented savings or dead demonstration controls.

## Sources and their application

- [anti-slop](https://github.com/miqdadbadjuber/anti-slop): purposeful visual treatments and real interactions. README saved as `.anti-slop-rules.md`; the filter is archived under docs/design-references.
- [Google DESIGN.md format](https://github.com/google-labs-code/design.md/blob/main/docs/spec.md): YAML tokens plus rationale. The requested root `/main/DESIGN.md` is absent; this file is authored for PLER using its actual format specification.
- [oh-my-design](https://github.com/kwakseongjae/oh-my-design): sourced values and role separation; archived Vercel/Raycast references are inspiration, not PLER defaults.
- [coss ui / Origin UI](https://github.com/cosscom/ui/tree/main/apps/ui/registry/default/ui): compact native controls, inset highlights, visible focus/pressed/busy states. The supplied cosscom/coss now contains a wider platform; cosscom/ui has the directly relevant UI sources.
- [OpenDesign](https://github.com/nexu-io/open-design): reusable design-system roles and Raycast surface reference, adapted to a local record tool.
- [Motion Primitives](https://github.com/ibelick/motion-primitives/blob/main/components/core/animated-background.tsx): shared-layout selection pattern. PLER implements its own small navigation/filter components using installed Motion; it does not claim the complete React component kit is installed.

Source URLs and SHA256s are saved in docs/design-references/sources.json and patterns.json.
`frontend/tokens.json` emits CSS variables at build time. `frontend/workspace.css` and
`frontend/sessions-grid.css` consume those variables. This replaces the old stacked overrides.
