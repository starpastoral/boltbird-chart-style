# Boltbird Agent Quickstart

Use this when another agent needs a minimal, self-sufficient way to call the skill.

If the agent just wants working starter code, start from [`../examples/minimal_svg_chart.py`](../examples/minimal_svg_chart.py).

## Canonical Source of Truth

- Tokens are canonical.
- If prose ranges and token values differ, prefer [`../assets/style-tokens.json`](../assets/style-tokens.json).
- Prose docs explain intent and defaults; tokens define the concrete shipped values.

## Scope Boundary

- Primary implementation target: SVG-first workflows.
- Portable layer: tokens, chart-form rules, color rules, and layout rules can be translated into Matplotlib, Plotly, Vega-Lite, ECharts, or other stacks.
- If another agent is not using SVG, it should still read the tokens and recipes first, then adapt the same hierarchy and role logic into the target library.

## Minimum Inputs

Required:

- `chart_kind`
- data series or category list
- `title`
- `source`

Optional:

- `subtitle`
- `requested_mode`
- explicit watermark suppression if the user asks for no watermark
- explicit chart-form override if the user insists on a weak form

## Default Decisions

- default mode: `consulting_safe`
- default background: transparent
- default palette logic: `one accent + neutral ladder`
- canonical source artifact: `SVG`
- default user-facing preview artifact: `PNG`
- default chart copy language: `English`
- default font stacks:
  - primary: `Geist`, fallback to `Helvetica Neue`, `Arial`, `sans-serif`
  - monospace: `Google Sans Code`, fallback to `Geist Mono`, `SFMono-Regular`, `Menlo`, `monospace`
  - wordmark: `Source Serif 4`, fallback to `Times New Roman`, `serif`
- runtime font rule:
  - resolve fonts before rendering
  - for SVG, emit a style block from `font_runtime.build_svg_style_block(...)` so the chart does not depend on backend font discovery
  - unless the user explicitly asks otherwise, keep all chart text English-only
  - watermark is special: place the canonical SVG asset as one lockup object instead of reconstructing it from live text

## Delivery Rule

- If both `SVG` and `PNG` are available, show the `PNG` in the user-facing response.
- Mention the `SVG` as the editable or vector source.
- Do not reply with only a file path when a previewable `PNG` exists.
- Recommended export pair:
  - source: `chart_name.svg`
  - preview: `chart_name.png`
  - PNG scale: `2x` for a 1600x900 logical canvas

Preferred export command:

```bash
python3 /path/to/boltbird-chart-style/scripts/export_preview_png.py /path/to/chart.svg
```

Recommended preflight:

```bash
python3 /path/to/boltbird-chart-style/scripts/check_fonts.py
```

Candlestick gate:

```bash
python3 /path/to/boltbird-chart-style/examples/candlestick_canonical_svg.py --output /path/to/chart.svg
python3 /path/to/boltbird-chart-style/scripts/chart_qa.py /path/to/chart.svg
```

## Runtime Entry Point

```python
from pathlib import Path
import sys

SKILL_DIR = Path("/path/to/boltbird-chart-style")
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from font_runtime import build_svg_style_block
from runtime import chart_plan, load_runtime, series_palette

rt = load_runtime(SKILL_DIR, requested_mode=None)
tokens = rt["tokens"]
mode = rt["mode"]
plan = chart_plan(
    chart_kind="bar",
    series_count=1,
    category_count=6,
    tokens=tokens,
    requested_mode=mode,
)
colors = series_palette(
    chart_kind=plan["resolved_form"],
    count=6,
    tokens=tokens,
    requested_mode=mode,
)
style_block = build_svg_style_block(rt["font_plan"])
```

Interpretation:

- `chart_plan(...)` decides whether the requested form should change under `consulting_safe`
- `series_palette(...)` returns a default palette for the final form
- `build_svg_style_block(...)` makes the SVG self-describing instead of trusting system font lookup
- `chart_qa.py` is not optional for candlesticks; first-pass delivery should fail closed when QA reports candle merging, axis drift, label collision, or watermark intrusion
- source line and watermark should be emitted in the metadata footer row, not as floating plot overlays

## Non-SVG Mapping Cheat Sheet

If the target stack is not SVG:

- Matplotlib:
  - map `ink_*` to title, axis, tick, and grid colors
  - map `primary_accent` and neutral ladder to series colors
  - keep figure and axes facecolor transparent
  - use Matplotlib for marks and axes only when necessary; final typography and watermarking should still be emitted with explicit font control
  - use [`../scripts/matplotlib_bridge.py`](../scripts/matplotlib_bridge.py) to export a plot-only SVG fragment and compose it into the final Boltbird shell
- Plotly:
  - map fonts from `typography`
  - set `paper_bgcolor` and `plot_bgcolor` to transparent
  - use annotations for metadata and latest labels
- ECharts / Vega-Lite:
  - use token colors and font stacks directly
  - preserve the same legend rule and watermark safe zone

## Label Placement Example

Use `choose_latest_label_placement()` for one latest-value label inside the plot.

```python
from label_placement import choose_latest_label_placement, polyline_obstacles

obstacles = polyline_obstacles(
    points=series_points,
    segment_window=tokens["chart_recipes"]["line"]["obstacle_segment_window"],
    stroke_pad_px=tokens["chart_recipes"]["line"]["obstacle_stroke_pad_px"],
)

placement = choose_latest_label_placement(
    point_x=last_x,
    point_y=last_y,
    text=label_text,
    font_size=14,
    plot_x0=plot_x0,
    plot_y0=plot_y0,
    plot_x1=plot_x1,
    plot_y1=plot_y1,
    obstacles=obstacles,
    gap_px=tokens["layout"]["latest_label_gap_px"],
    vertical_offset_px=tokens["layout"]["latest_label_vertical_offset_px"],
    min_line_length_px=tokens["layout"]["latest_label_line_min_length_px"],
    single_label_use_line=tokens["layout"]["latest_label_single_use_line"],
)
```

Use `stack_external_labels()` when multiple line endpoints would collide and the recipes require an outside stack.

For candlesticks, prefer `candlestick_obstacles(...)` over hand-built rectangles. Feed it the recent candle window around the latest point, not just the final candle body.

## Expected Output Shape

A completed Boltbird chart should include:

- title
- optional subtitle
- short source line
- consistent grid and axis styling
- watermark unless the user opts out
- labels or legend according to the recipe rules

It should not include:

- opaque background by default
- ornamental border
- rainbow categorical palette
- crowded in-wedge pie labels
- outline-heavy text hacks
