#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from font_runtime import build_svg_style_block, font_report_lines
from label_placement import choose_latest_label_placement, polyline_obstacles
from matplotlib_bridge import (
    configure_matplotlib_env,
    figure_to_svg_fragment,
    prepare_axes_for_geometry_only,
    require_matplotlib,
    wrap_svg_fragment,
)
from runtime import chart_plan, load_runtime, series_palette
from svg_chrome import draw_text, render_metadata_block, render_metadata_footer_row, render_watermark


WIDTH = 1600
HEIGHT = 900


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Matplotlib geometry-only chart composed into Boltbird SVG chrome.")
    parser.add_argument(
        "--output",
        default=str(SKILL_DIR / "examples" / "matplotlib_postcompose_chart.svg"),
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


def nice_ticks(min_value: float, max_value: float, count: int = 5) -> list[float]:
    if count < 2:
        return [min_value, max_value]
    span = max_value - min_value
    if span <= 0:
        return [min_value] * count
    raw_step = span / (count - 1)
    magnitude = 10 ** int(f"{raw_step:e}".split("e")[1])
    normalized = raw_step / magnitude
    if normalized <= 1:
        nice = 1
    elif normalized <= 2:
        nice = 2
    elif normalized <= 5:
        nice = 5
    else:
        nice = 10
    step = nice * magnitude
    start = step * int(min_value // step)
    if start > min_value:
        start -= step
    ticks: list[float] = []
    value = start
    while value <= max_value + step:
        if value >= min_value - step * 0.5:
            ticks.append(value)
        value += step
    return ticks[: count + 1]


def main() -> None:
    args = parse_args()
    configure_matplotlib_env(SKILL_DIR / ".runtime")
    rt = load_runtime(SKILL_DIR, requested_mode=args.mode)
    tokens = rt["tokens"]
    mode = rt["mode"]
    palette = tokens["palette"]
    layout = tokens["layout"]
    metadata = tokens["metadata"]
    footer_baseline_y = metadata["footer_baseline_y_px"]
    footer_rule_y = metadata["footer_rule_y_px"]
    recipe = tokens["chart_recipes"]["line"]
    plt = require_matplotlib()

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
    values = [112.0, 118.4, 121.3, 128.7, 133.1, 137.9, 142.4, 145.2]

    plan = chart_plan(
        chart_kind="line",
        series_count=1,
        category_count=len(values),
        tokens=tokens,
        requested_mode=mode,
    )
    line_color = series_palette(
        chart_kind=plan["resolved_form"],
        count=1,
        tokens=tokens,
        requested_mode=mode,
    )[0]

    left = layout["padding_px"]["left"]
    right = layout["padding_px"]["right"]
    top = layout["padding_px"]["top"]
    bottom = layout["padding_px"]["bottom"]
    meta_h = layout["metadata_band_height_px"]

    plot_x0 = left + 64
    plot_x1 = WIDTH - right - 48
    plot_y0 = top + meta_h + 16
    plot_y1 = HEIGHT - bottom - 18
    plot_width = plot_x1 - plot_x0
    plot_height = plot_y1 - plot_y0

    min_value = min(values)
    max_value = max(values)
    y_pad = (max_value - min_value) * 0.12
    y_min = min_value - y_pad
    y_max = max_value + y_pad
    y_ticks = nice_ticks(y_min, y_max, count=5)

    fig, ax = plt.subplots(figsize=(plot_width / 100.0, plot_height / 100.0), dpi=100)
    prepare_axes_for_geometry_only(fig, ax, tokens=tokens, grid_axis="y")
    ax.set_xlim(0, len(values) - 1)
    ax.set_ylim(y_min, y_max)
    ax.set_xticks(range(len(months)))
    ax.set_yticks(y_ticks)
    ax.plot(
        range(len(values)),
        values,
        color=line_color,
        linewidth=recipe["focus_series_weight_px"],
        solid_capstyle="round",
        solid_joinstyle="round",
    )

    fragment = figure_to_svg_fragment(fig)
    plt.close(fig)

    def sx(index: int) -> float:
        return plot_x0 + plot_width * index / max(len(values) - 1, 1)

    def sy(value: float) -> float:
        return plot_y1 - ((value - y_min) / (y_max - y_min)) * plot_height

    series_points = [(sx(i), sy(v)) for i, v in enumerate(values)]
    last_x, last_y = series_points[-1]
    latest_text = f"{values[-1]:.1f}"
    latest = choose_latest_label_placement(
        point_x=last_x,
        point_y=last_y,
        text=latest_text,
        font_size=16,
        plot_x0=plot_x0,
        plot_y0=plot_y0,
        plot_x1=plot_x1,
        plot_y1=plot_y1,
        obstacles=polyline_obstacles(
            series_points,
            segment_window=recipe["obstacle_segment_window"],
            stroke_pad_px=recipe["obstacle_stroke_pad_px"],
        ),
        gap_px=layout["latest_label_gap_px"],
        vertical_offset_px=layout["latest_label_vertical_offset_px"],
        min_line_length_px=layout["latest_label_line_min_length_px"],
        single_label_use_line=layout["latest_label_single_use_line"],
    )

    svg: list[str] = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" fill="none">'
    )
    svg.append(build_svg_style_block(rt["font_plan"]))
    svg.extend(
        render_metadata_block(
            width=WIDTH,
            plot_x0=left,
            plot_x1=plot_x1,
            title="Matplotlib Geometry, Boltbird Chrome",
            subtitle=f"Renderer split: plot marks in Matplotlib | type and watermark in SVG | mode {mode}",
            source="",
            title_fill=palette["ink_strong"],
            body_fill=palette["ink_soft"],
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
            source_fill=palette["ink_soft"],
            source_size=16,
            watermark_parts=render_watermark(
                right_edge=plot_x1,
                baseline_y=footer_baseline_y,
                watermark_tokens=rt["watermark_tokens"],
                fill=palette["ink_base"],
                watermark_asset=rt["watermark_lockup_svg"],
            ),
        )
    )
    svg.extend(
        wrap_svg_fragment(
            fragment,
            x=plot_x0,
            y=plot_y0,
            width=plot_width,
            height=plot_height,
        )
    )

    for tick in y_ticks:
        if tick < y_min or tick > y_max:
            continue
        y = sy(tick)
        svg.append(
            draw_text(
                plot_x0 - 16,
                y + 5,
                f"{tick:.0f}",
                klass="gscode",
                size=14,
                weight=500,
                fill=palette["ink_soft"],
                anchor="end",
            )
        )

    for idx, month in enumerate(months):
        svg.append(
            draw_text(
                sx(idx),
                plot_y1 + 34,
                month,
                klass="geist",
                size=15,
                weight=500,
                fill=palette["ink_soft"],
                anchor="middle",
            )
        )

    svg.append(f'<circle cx="{last_x:.2f}" cy="{last_y:.2f}" r="{recipe["latest_marker_radius_px"]:.2f}" fill="{line_color}"/>')
    if latest.use_line:
        svg.append(
            f'<line x1="{last_x:.2f}" y1="{last_y:.2f}" x2="{latest.line_end_x:.2f}" y2="{latest.line_end_y:.2f}" '
            f'stroke="{palette["ink_soft"]}" stroke-width="1.2" stroke-linecap="round"/>'
        )
    svg.append(
        draw_text(
            latest.text_x,
            latest.text_y,
            latest_text,
            klass="gscode",
            size=16,
            weight=500,
            fill=palette["ink_base"],
            anchor=latest.anchor,
        )
    )
    svg.append(
        draw_text(
            plot_x0,
            plot_y0 - 18,
            "Index level",
            klass="geist",
            size=15,
            weight=500,
            fill=palette["ink_soft"],
        )
    )
    svg.append("</svg>")

    out_path = Path(args.output)
    out_path.write_text("".join(svg), encoding="utf-8")
    print(out_path)
    for line in font_report_lines(rt["font_plan"]):
        print(line, file=sys.stderr)
    print(f"MPLCONFIGDIR={os.environ['MPLCONFIGDIR']}", file=sys.stderr)

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
