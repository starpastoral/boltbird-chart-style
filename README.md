# Boltbird Chart Style

`v1.0.0`

Boltbird chart styling skill for Codex. This package standardizes chart presentation across candlestick, line, bar, area, scatter, heatmap, and related analytical visuals.

## Includes

- Codex skill entrypoint: `SKILL.md`
- House style tokens: `assets/style-tokens.json`
- Runtime helpers: `scripts/runtime.py`
- Font runtime and SVG style emission: `scripts/font_runtime.py`
- Matplotlib geometry-only bridge: `scripts/matplotlib_bridge.py`
- Candlestick runtime helper: `scripts/candlestick_runtime.py`
- SVG chrome helpers: `scripts/svg_chrome.py`
- Label placement helpers: `scripts/label_placement.py`
- SVG to PNG preview exporter: `scripts/export_preview_png.py`
- Font preflight checker: `scripts/check_fonts.py`
- Chart QA checker: `scripts/chart_qa.py`
- Watermark asset builder: `scripts/build_watermark_lockup.py`
- Matplotlib post-compose example: `examples/matplotlib_postcompose_chart.py`
- Canonical candlestick example: `examples/candlestick_canonical_svg.py`

## Install

Copy the directory into `~/.codex/skills/boltbird-chart-style`.

## Notes

- Canonical source artifact is `SVG`
- Default user-facing preview artifact is `PNG`
- Default mode is `consulting_safe`
- Font resolution is explicit runtime behavior, not an implicit system-font assumption
