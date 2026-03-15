---
name: "boltbird-chart-style"
description: "Standardize presentation-ready chart styling with the Boltbird house system: transparent background, Geist typography, Google Sans Code for monospaced labels, restrained monochrome palette, disciplined annotation layout, and a non-blocking top-right watermark. Use when Codex needs to create, restyle, or review candlestick/K-line charts, line charts, bar charts, area charts, scatter plots, heatmaps, or similar analytical visuals so they match one consistent visual template."
---

# Boltbird Chart Style

Apply one visual system across financial and analytical charts. Preserve the same typographic hierarchy, neutral palette discipline, annotation density, and watermark behavior regardless of charting library.

## What Another Agent Should Assume

- Default mode is `consulting_safe`.
- If the user does not force a chart form, you may change the chart form for readability.
- If the user forces a weak chart form, keep the form but apply the stress-case rules from the recipes.
- The safest generic default is: transparent export, one accent plus neutral ladder, restrained labels, and a top metadata band.
- Tokens are the shipped source of truth. If prose ranges differ from concrete token values, follow the tokens.
- This skill is SVG-first, but the tokens and decision rules are portable to other chart stacks.
- Font handling is part of the runtime contract. Do not assume a host renderer can discover `Geist`, `Google Sans Code`, or `Source Serif 4` just because they exist on the machine.
- Default chart copy language is English. Unless the user explicitly asks for another language, titles, subtitles, source lines, watermark text, axis labels, legend labels, and annotations must stay English-only to reduce font fallback risk.

## Workflow

1. Read [`references/style-spec.md`](references/style-spec.md) before making or revising any chart.
2. Read [`references/chart-recipes.md`](references/chart-recipes.md) only for the chart types in scope.
3. Start from [`assets/style-tokens.json`](assets/style-tokens.json) when the target stack supports config objects, design tokens, or theme files.
4. Resolve fonts through the shared runtime before emitting text. For SVG output, embed resolved font files into the SVG style block when possible instead of trusting system lookup.
5. Use transparent export by default. Assume the chart may be placed on either a light or dark surface, so use the default mid-gray neutral ink system instead of maintaining separate light-only and dark-only variants.
6. Use the watermark as one SVG lockup asset from [`assets/watermark-lockup.svg`](assets/watermark-lockup.svg). Do not reconstruct it from live text unless you are regenerating the asset itself. Never use a colored emoji glyph.
7. Use `profiles.default_mode` unless the user explicitly asks for another mode. The default mode is `consulting_safe`; supported explicit modes are `consulting_safe` and `editorial`.
8. For candlestick tasks, use the canonical starter and run chart QA before delivery. If there is no fitting canonical pipeline, extend the skill first instead of improvising ad-hoc geometry.

## Quick Invocation

For pure guidance:

- Read [`references/style-spec.md`](references/style-spec.md)
- Read the matching section in [`references/chart-recipes.md`](references/chart-recipes.md)
- Apply the defaults from [`assets/style-tokens.json`](assets/style-tokens.json)
- If you need a fast operational contract, read [`references/agent-quickstart.md`](references/agent-quickstart.md)
- If you need runnable starter code, begin from [`examples/minimal_svg_chart.py`](examples/minimal_svg_chart.py)

For Python-based SVG generation, start from the shared runtime layer instead of loading individual files by hand:

```python
from pathlib import Path
import sys

SKILL_DIR = Path("/path/to/boltbird-chart-style")
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from font_runtime import build_svg_style_block
from runtime import chart_plan, load_runtime, series_palette
from svg_chrome import render_metadata_block, render_legend, render_watermark
from label_placement import choose_latest_label_placement, polyline_obstacles, stack_external_labels

rt = load_runtime(SKILL_DIR)
tokens = rt["tokens"]
mode = rt["mode"]
plan = chart_plan(chart_kind="line", series_count=4, tokens=tokens, requested_mode=mode)
colors = series_palette(chart_kind=plan["resolved_form"], count=4, tokens=tokens, requested_mode=mode)
style_block = build_svg_style_block(rt["font_plan"])
```

Use `chart_plan(...)` before drawing when chart form may need to change under `consulting_safe`.

## Minimal Data Contract

Another agent should be able to call this skill with just:

- chart intent: `line`, `bar`, `pie`, `candlestick`, `scatter`, etc.
- series count or category count
- optional explicit mode: `consulting_safe` or `editorial`
- title, subtitle, and short source text
- target stack, if not SVG

Everything else should come from the tokens and shared helpers unless the user explicitly asks to override it.

## Shared Entry Points

- Runtime facade: [`scripts/runtime.py`](scripts/runtime.py)
- Font resolution and SVG style emission: [`scripts/font_runtime.py`](scripts/font_runtime.py)
- Matplotlib geometry-only bridge: [`scripts/matplotlib_bridge.py`](scripts/matplotlib_bridge.py)
- Candlestick geometry helper: [`scripts/candlestick_runtime.py`](scripts/candlestick_runtime.py)
- QA metadata and checks: [`scripts/qa_runtime.py`](scripts/qa_runtime.py), [`scripts/chart_qa.py`](scripts/chart_qa.py)
- Label placement: [`scripts/label_placement.py`](scripts/label_placement.py)
- SVG metadata, legend, and watermark helpers: [`scripts/svg_chrome.py`](scripts/svg_chrome.py)
- Palette and mode logic: [`scripts/palette_system.py`](scripts/palette_system.py)

## Non-Negotiables

- Use `Geist` for titles, axes, legends, notes, and annotations.
- Use `Google Sans Code` only for dense numeric tags, compact tabular values, or code-like identifiers.
- Do not treat silent font fallback as acceptable. If required fonts are unresolved, either embed them from resolved files or state that the chart is running in fallback mode.
- If Matplotlib is used, keep it geometry-only. Titles, legends, watermark, and final text treatment belong in the SVG compose layer, not in `matplotlib`.
- Do not ship the first candlestick draft without QA. Run `python3 scripts/chart_qa.py path/to/chart.svg` and fail the task if it reports body merging, axis drift, label collision, or watermark intrusion.
- Do not bypass the runtime contract with one-off geometry math unless you are extending the shared candlestick pipeline itself.
- Source text and watermark belong to the metadata footer row. They are peers of the chart chrome, not floating overlays inside the plot body.
- Keep the background transparent unless the user explicitly asks for an opaque panel.
- Default to one accent plus a neutral ladder. If extra semantic separation is required, keep the total hue families restrained and only expand beyond one hue when the recipe requires it.
- Keep the chart data visually primary. Decorative elements, legend chrome, and watermarking must stay subordinate.
- Reserve a top metadata band so the watermark does not collide with titles, legends, or callouts.
- Prefer direct labels, shape changes, line weight, and brightness before adding more colors.
- In `consulting_safe`, change the chart form when readability breaks down instead of forcing a decorative chart type.

## Local Overrides (Charles workspace)

- For **AAPL event-annotated candlestick / K-line charts** in this workspace, use vertical event lines with fixed colors:
  - `WWDC` → `#7E57C2` (purple)
  - `Product Launch` → `#2F80ED` (blue)
  - `Earnings` → `#D64545` (red)
- Keep candle bodies/wicks in neutral grayscale; reserve event colors only for event lines and related labels.

## Delivery Defaults (Charles workspace)

- When generating charts, default deliverables are:
  - primary: `.svg`
  - preview: `.png` (same basename)
- Before rendering text-heavy charts, run `python3 scripts/check_fonts.py` or inspect `rt["font_plan"]` so font failures are explicit.
- For candlestick charts, run the canonical path in [`examples/candlestick_canonical_svg.py`](examples/candlestick_canonical_svg.py) or an equivalent pipeline built on the shared helpers, then run `python3 scripts/chart_qa.py output.svg`.
- After writing SVG, export PNG if tooling exists:
  - prefer: `rsvg-convert -w 1600 -h 900 input.svg -o output.png`
  - fallback: `magick input.svg -resize 1600x900 output.png`
- If PNG export tool is unavailable, state it explicitly and still deliver SVG.

## Output Checklist

- Title, subtitle, source, and legend align to the same visual grid.
- Gridlines, axes, and labels remain legible on the intended composite background.
- Watermark is in the top-right safe zone and does not cover chart text or important marks.
- Annotation count is restrained; labels highlight only meaningful events or extremes.
- Color usage stays within the house limit and does not drift into rainbow palettes.

## Resources

- Core spec: [`references/style-spec.md`](references/style-spec.md)
- Agent quickstart: [`references/agent-quickstart.md`](references/agent-quickstart.md)
- Chart-specific rules: [`references/chart-recipes.md`](references/chart-recipes.md)
- Reusable tokens: [`assets/style-tokens.json`](assets/style-tokens.json)
- Runtime facade for other agents: [`scripts/runtime.py`](scripts/runtime.py)
- Optional Matplotlib bridge: [`scripts/matplotlib_bridge.py`](scripts/matplotlib_bridge.py)
- Runnable starter example: [`examples/minimal_svg_chart.py`](examples/minimal_svg_chart.py)
- Matplotlib post-compose example: [`examples/matplotlib_postcompose_chart.py`](examples/matplotlib_postcompose_chart.py)
- Canonical candlestick starter: [`examples/candlestick_canonical_svg.py`](examples/candlestick_canonical_svg.py)
- Monochrome bird mark: [`assets/boltbird-mark.svg`](assets/boltbird-mark.svg)
- Watermark lockup: [`assets/watermark-lockup.svg`](assets/watermark-lockup.svg)
- Generic latest-label placement helper: [`scripts/label_placement.py`](scripts/label_placement.py)
- Shared SVG chrome helpers: [`scripts/svg_chrome.py`](scripts/svg_chrome.py)
- Single-accent-first palette resolver: [`scripts/palette_system.py`](scripts/palette_system.py)
