# Roodof workspace UI

Run npm ci, then npm run build from this folder. Production uses only bundled local JS/CSS/fonts.
workspace.js is the editable UI source; src/pler/web/workspace.js is generated with esbuild.
Motion/mini, selected ECharts bar/canvas components and selected Lucide icons are bundled.
The existing app.js owns data and mutations. The workspace preserves original IDs and adds
navigation, accessible section search and a chart that uses the existing project filter.
verify.mjs exercises an isolated local demo using headless Edge; its startup address is private
and must never be committed or included in reports. See reports/workspace-v1/REPORT.md.
