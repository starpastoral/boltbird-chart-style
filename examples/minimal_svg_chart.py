#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from font_runtime import build_svg_style_block, font_report_lines
from runtime import chart_plan, load_runtime, series_palette
from svg_chrome import draw_text, render_metadata_block, render_metadata_footer_row, render_watermark


WIDTH = 1600
HEIGHT = 900


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal Boltbird SVG chart example.")
    parser.add_argument(
        "--output",
        default=str(SKILL_DIR / "examples" / "minimal_svg_chart.svg"),
        help="Output SVG path.",
    )
    parser.add_argument(
        "--mode",
        choices=["consulting_safe", "editorial"],
        default=None,
        help="Optional explicit Boltbird mode override.",
    )
    parser.add_argument(
        "--no-png",
        action="store_true",
        help="Skip PNG preview export.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rt = load_runtime(SKILL_DIR, requested_mode=args.mode)
    tokens = rt["tokens"]
    mode = rt["mode"]
    palette = tokens["palette"]
    layout = tokens["layout"]
    metadata = tokens["metadata"]
    footer_baseline_y = metadata["footer_baseline_y_px"]
    footer_rule_y = metadata["footer_rule_y_px"]

    data = [
        ("Category A", 34.0),
        ("Category B", 27.0),
        ("Category C", 18.0),
        ("Category D", 12.0),
        ("Category E", 9.0),
    ]

    plan = chart_plan(
        chart_kind="bar",
        series_count=1,
        category_count=len(data),
        tokens=tokens,
        requested_mode=mode,
    )
    colors = series_palette(
        chart_kind=plan["resolved_form"],
        count=len(data),
        tokens=tokens,
        requested_mode=mode,
    )

    left = layout["padding_px"]["left"]
    right = layout["padding_px"]["right"]
    top = layout["padding_px"]["top"]
    bottom = layout["padding_px"]["bottom"]
    meta_h = layout["metadata_band_height_px"]

    plot_x0 = left + 220
    plot_x1 = WIDTH - right - 42
    plot_y0 = top + meta_h + 34
    plot_y1 = HEIGHT - bottom

    ink_strong = palette["ink_strong"]
    ink_base = palette["ink_base"]
    ink_soft = palette["ink_soft"]
    grid_major = palette["grid_major"]

    max_val = max(value for _, value in data)
    row_h = 74
    bar_h = 34

    svg: list[str] = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" fill="none">'
    )
    svg.append(
        build_svg_style_block(rt["font_plan"])
    )
    svg.extend(
        render_metadata_block(
            width=WIDTH,
            plot_x0=left,
            plot_x1=plot_x1,
            title="Minimal Boltbird SVG Example",
            subtitle=f"Default mode: {mode} | Resolved form: {plan['resolved_form']}",
            source="",
            title_fill=ink_strong,
            body_fill=ink_soft,
            title_size=38,
            subtitle_size=20,
            meta_size=16,
            metadata_tokens=metadata,
        )
    )
    svg.extend(
        render_metadata_footer_row(
            plot_x0=left,
            plot_x1=plot_x1,
            baseline_y=footer_baseline_y,
            rule_y=None,
            source="Source: synthetic demo data",
            source_fill=ink_soft,
            source_size=16,
            watermark_parts=render_watermark(
                right_edge=plot_x1,
                baseline_y=footer_baseline_y,
                watermark_tokens=rt["watermark_tokens"],
                fill=ink_base,
                watermark_asset=rt["watermark_lockup_svg"],
            ),
        )
    )

    for tick in range(0, 41, 5):
        x = plot_x0 + (plot_x1 - plot_x0) * tick / max_val
        svg.append(
            f'<line x1="{x:.2f}" y1="{plot_y0:.2f}" x2="{x:.2f}" y2="{plot_y1:.2f}" '
            f'stroke="{grid_major}" stroke-width="1.0"/>'
        )
        svg.append(
            draw_text(
                x,
                plot_y1 + 28,
                f"{tick}%",
                klass="gscode",
                size=14,
                weight=500,
                fill=ink_soft,
                anchor="middle",
            )
        )

    for idx, ((label, value), color) in enumerate(zip(data, colors)):
        y = plot_y0 + idx * row_h + 12
        bar_w = (plot_x1 - plot_x0) * value / max_val
        svg.append(draw_text(plot_x0 - 18, y + 21, label, klass="geist", size=18, weight=500, fill=ink_base, anchor="end"))
        svg.append(f'<rect x="{plot_x0:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{bar_h:.2f}" rx="6" fill="{color}"/>')
        svg.append(draw_text(plot_x0 + bar_w + 12, y + 23, f"{value:.1f}%", klass="gscode", size=16, weight=500, fill=ink_base))

    svg.append(draw_text(plot_x0, plot_y0 - 18, "Share", klass="geist", size=15, weight=500, fill=ink_soft))
    svg.append("</svg>")

    out_path = Path(args.output)
    out_path.write_text("".join(svg), encoding="utf-8")
    print(out_path)
    for line in font_report_lines(rt["font_plan"]):
        print(line, file=sys.stderr)

    if not args.no_png:
        export_script = SKILL_DIR / "scripts" / "export_preview_png.py"
        subprocess.run(
            [
                sys.executable,
                str(export_script),
                str(out_path),
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
