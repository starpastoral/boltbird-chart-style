#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from candlestick_runtime import price_to_y, resolve_candle_geometry, resolve_price_bounds
from font_runtime import build_svg_style_block, font_report_lines
from label_placement import LabelPlacement, Rect, candlestick_obstacles, choose_latest_label_placement, estimate_label_width, line_endpoint_for_box
from qa_runtime import render_qa_metadata
from runtime import load_runtime
from svg_chrome import draw_text, render_metadata_block, render_metadata_footer_row, render_watermark


WIDTH = 1600
HEIGHT = 900


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Canonical Boltbird candlestick starter with QA metadata.")
    parser.add_argument(
        "--output",
        default=str(SKILL_DIR / "examples" / "candlestick_canonical.svg"),
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
    span = max(max_value - min_value, 1.0)
    step = span / (count - 1)
    magnitude = 10 ** int(f"{step:e}".split("e")[1])
    normalized = step / magnitude
    if normalized <= 1:
        step = 1 * magnitude
    elif normalized <= 2:
        step = 2 * magnitude
    elif normalized <= 5:
        step = 5 * magnitude
    else:
        step = 10 * magnitude
    start = step * int(min_value // step)
    if start > min_value:
        start -= step
    ticks: list[float] = []
    value = start
    while value <= max_value + step:
        if value >= min_value - step * 0.5:
            ticks.append(round(value, 2))
        value += step
    return ticks[: count + 1]


def watermark_bbox(right_edge: float, baseline_y: float, watermark_tokens: dict, watermark_asset: dict) -> dict:
    if watermark_tokens.get("anchor_mode") == "icon_right_edge":
        wm_x = right_edge - watermark_tokens["icon_right_edge_px"]
    else:
        wm_x = right_edge - watermark_tokens["width_px"]
    wm_y = baseline_y - watermark_tokens["baseline_y_px"]
    return {
        "x0": wm_x,
        "y0": wm_y,
        "x1": wm_x + watermark_asset["width"],
        "y1": wm_y + watermark_asset["height"],
    }


def label_collides(box: Rect, obstacles: list[Rect], pad: float) -> bool:
    return any(box.intersects(obstacle, pad=pad) for obstacle in obstacles)


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
    recipe = tokens["chart_recipes"]["candlestick"]

    ohlc = [
        {"date": "Mar 03", "open": 176.4, "high": 179.2, "low": 174.8, "close": 178.6},
        {"date": "Mar 04", "open": 178.8, "high": 180.1, "low": 176.9, "close": 177.4},
        {"date": "Mar 05", "open": 177.2, "high": 181.5, "low": 176.3, "close": 180.9},
        {"date": "Mar 06", "open": 181.1, "high": 182.7, "low": 178.5, "close": 179.3},
        {"date": "Mar 07", "open": 179.5, "high": 183.9, "low": 178.6, "close": 183.2},
        {"date": "Mar 10", "open": 183.0, "high": 184.1, "low": 179.9, "close": 180.7},
        {"date": "Mar 11", "open": 180.5, "high": 181.8, "low": 177.6, "close": 178.4},
        {"date": "Mar 12", "open": 178.8, "high": 182.9, "low": 178.0, "close": 182.1},
        {"date": "Mar 13", "open": 182.0, "high": 185.6, "low": 181.4, "close": 184.7},
        {"date": "Mar 14", "open": 184.2, "high": 186.0, "low": 182.5, "close": 183.8},
        {"date": "Mar 17", "open": 183.6, "high": 187.4, "low": 182.7, "close": 186.5},
        {"date": "Mar 18", "open": 186.8, "high": 188.9, "low": 184.3, "close": 185.1},
    ]
    events = [
        {"date": "Mar 07", "label": "Product Launch", "color": "#2F80ED"},
        {"date": "Mar 13", "label": "Earnings", "color": "#D64545"},
    ]

    left = layout["padding_px"]["left"]
    right = layout["padding_px"]["right"]
    top = layout["padding_px"]["top"]
    bottom = layout["padding_px"]["bottom"]
    meta_h = layout["metadata_band_height_px"]

    plot_x0 = left + 84
    plot_x1 = WIDTH - right - 56
    plot_y0 = top + meta_h + 28
    plot_y1 = HEIGHT - bottom - 24
    plot_width = plot_x1 - plot_x0

    y_min, y_max = resolve_price_bounds(ohlc=ohlc)
    ticks = nice_ticks(y_min, y_max, count=5)
    candle_geo = resolve_candle_geometry(
        plot_width=plot_width,
        candle_count=len(ohlc),
        recipe_tokens=recipe,
    )
    slot_width = candle_geo["slot_width"]
    body_width = candle_geo["body_width"]
    body_half_width = candle_geo["body_half_width"]

    def candle_x(index: int) -> float:
        return plot_x0 + slot_width * (index + 0.5)

    candles_manifest: list[dict] = []
    obstacles_input: list[tuple[float, float, float, float, float]] = []
    svg: list[str] = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" fill="none">'
    )
    manifest = {
        "chart_kind": "candlestick",
        "background": "transparent",
        "watermark_render_mode": "svg_asset",
        "canvas": {"width": WIDTH, "height": HEIGHT},
        "plot": {"x0": plot_x0, "x1": plot_x1, "y0": plot_y0, "y1": plot_y1},
        "font_plan_missing_roles": rt["font_plan"]["missing_roles"],
        "text_policy": {
            "default_chart_language": tokens["typography"]["default_chart_language"],
            "allow_non_english_text_by_default": tokens["typography"]["allow_non_english_text_by_default"],
        },
        "qa_thresholds": {
            "y_axis_label_max_gap_px": recipe["y_axis_label_max_gap_px"],
            "x_tick_min_gap_px": recipe["x_tick_min_gap_px"],
            "body_gap_min_px": recipe["body_gap_min_px"],
            "latest_label_obstacle_pad_px": recipe["latest_label_obstacle_pad_px"],
            "watermark_plot_clearance_px": recipe["watermark_plot_clearance_px"],
        },
    }
    svg.append(render_qa_metadata(manifest))
    svg.append(build_svg_style_block(rt["font_plan"]))
    svg.extend(
        render_metadata_block(
            width=WIDTH,
            plot_x0=left,
            plot_x1=plot_x1,
            title="AAPL Event-Annotated Candlestick",
            subtitle=f"Canonical Boltbird candlestick starter | mode {mode} | grayscale candles, explicit QA",
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
            source="Source: synthetic OHLC demo data",
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

    y_labels: list[dict] = []
    for tick in ticks:
        if tick < y_min or tick > y_max:
            continue
        y = price_to_y(tick, y_min=y_min, y_max=y_max, plot_y0=plot_y0, plot_y1=plot_y1)
        svg.append(
            f'<line x1="{plot_x0:.2f}" y1="{y:.2f}" x2="{plot_x1:.2f}" y2="{y:.2f}" '
            f'stroke="{palette["grid_major"]}" stroke-width="1.0"/>'
        )
        label_x = plot_x0 - recipe["y_axis_label_gap_px"]
        svg.append(
            draw_text(
                label_x,
                y + 5,
                f"{tick:.0f}",
                klass="gscode",
                size=14,
                weight=500,
                fill=palette["ink_soft"],
                anchor="end",
            )
        )
        y_labels.append({"x": label_x, "y": y + 5, "text": f"{tick:.0f}", "anchor": "end"})

    x_ticks: list[dict] = []
    for index, row in enumerate(ohlc):
        x = candle_x(index)
        if index % 2 == 1:
            svg.append(
                draw_text(
                    x,
                    plot_y1 + 34,
                    row["date"],
                    klass="geist",
                    size=15,
                    weight=500,
                    fill=palette["ink_soft"],
                    anchor="middle",
                )
            )
            x_ticks.append({"x": x, "label": row["date"]})

    event_lookup = {event["date"]: event for event in events}
    for index, row in enumerate(ohlc):
        x = candle_x(index)
        open_y = price_to_y(row["open"], y_min=y_min, y_max=y_max, plot_y0=plot_y0, plot_y1=plot_y1)
        close_y = price_to_y(row["close"], y_min=y_min, y_max=y_max, plot_y0=plot_y0, plot_y1=plot_y1)
        high_y = price_to_y(row["high"], y_min=y_min, y_max=y_max, plot_y0=plot_y0, plot_y1=plot_y1)
        low_y = price_to_y(row["low"], y_min=y_min, y_max=y_max, plot_y0=plot_y0, plot_y1=plot_y1)
        body_top = min(open_y, close_y)
        body_bottom = max(open_y, close_y)
        is_up = row["close"] >= row["open"]
        stroke = palette[recipe["wick_up_color"] if is_up else recipe["wick_down_color"]]
        fill = "none" if is_up else palette[recipe["down_body_color"]]
        body_stroke = palette[recipe["up_body_color"] if is_up else recipe["down_body_color"]]
        stroke_width = recipe["up_body_stroke_width_px"] if is_up else recipe["down_body_stroke_width_px"]

        svg.append(
            f'<line x1="{x:.2f}" y1="{high_y:.2f}" x2="{x:.2f}" y2="{low_y:.2f}" '
            f'stroke="{stroke}" stroke-width="{recipe["wick_width_px"]}" stroke-linecap="round"/>'
        )
        svg.append(
            f'<rect x="{x - body_half_width:.2f}" y="{body_top:.2f}" width="{body_width:.2f}" '
            f'height="{max(body_bottom - body_top, 1.8):.2f}" rx="{recipe["corner_radius_px"]}" '
            f'fill="{fill}" stroke="{body_stroke}" stroke-width="{stroke_width:.2f}"/>'
        )
        if row["date"] in event_lookup:
            event = event_lookup[row["date"]]
            svg.append(
                f'<line x1="{x:.2f}" y1="{plot_y0:.2f}" x2="{x:.2f}" y2="{plot_y1:.2f}" '
                f'stroke="{event["color"]}" stroke-width="1.2" stroke-dasharray="5 7"/>'
            )
            svg.append(
                draw_text(
                    x + 8,
                    plot_y0 + 18,
                    event["label"],
                    klass="geist",
                    size=13,
                    weight=600,
                    fill=event["color"],
                )
            )

        candles_manifest.append(
            {
                "date": row["date"],
                "x": x,
                "body_left": x - body_half_width,
                "body_right": x + body_half_width,
                "body_width": body_width,
                "wick_top": high_y,
                "wick_bottom": low_y,
            }
        )
        obstacles_input.append((x, open_y, close_y, high_y, low_y))

    recent_obstacles = candlestick_obstacles(
        candles=obstacles_input[-6:],
        body_half_width=body_half_width,
        pad_px=recipe["latest_label_obstacle_pad_px"],
    )
    latest_row = ohlc[-1]
    latest_x = candle_x(len(ohlc) - 1)
    latest_y = price_to_y(latest_row["close"], y_min=y_min, y_max=y_max, plot_y0=plot_y0, plot_y1=plot_y1)
    latest_text = f"{latest_row['close']:.1f}"
    latest = choose_latest_label_placement(
        point_x=latest_x,
        point_y=latest_y,
        text=latest_text,
        font_size=16,
        plot_x0=plot_x0,
        plot_y0=plot_y0,
        plot_x1=plot_x1,
        plot_y1=plot_y1,
        obstacles=recent_obstacles,
        gap_px=layout["latest_label_gap_px"],
        vertical_offset_px=layout["latest_label_vertical_offset_px"],
        min_line_length_px=layout["latest_label_line_min_length_px"],
        single_label_use_line=layout["latest_label_single_use_line"],
    )
    if label_collides(latest.box, recent_obstacles, pad=recipe["latest_label_obstacle_pad_px"]):
        width = estimate_label_width(latest_text, 16)
        fallback_text_x = plot_x1 - 8
        fallback_text_y = plot_y0 + 24
        latest = LabelPlacement(
            text_x=fallback_text_x,
            text_y=fallback_text_y,
            anchor="end",
            use_line=True,
            box=Rect(fallback_text_x - width, fallback_text_y - 24, fallback_text_x, fallback_text_y),
            line_end_x=0.0,
            line_end_y=0.0,
        )
        latest.line_end_x, latest.line_end_y = line_endpoint_for_box(
            latest.box,
            point_x=latest_x,
            point_y=latest_y,
        )
    svg.append(
        f'<circle cx="{latest_x:.2f}" cy="{latest_y:.2f}" r="4.4" fill="{palette["primary_accent"]}"/>'
    )
    if latest.use_line:
        svg.append(
            f'<line x1="{latest_x:.2f}" y1="{latest_y:.2f}" x2="{latest.line_end_x:.2f}" y2="{latest.line_end_y:.2f}" '
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
            "Adjusted close, USD",
            klass="geist",
            size=15,
            weight=500,
            fill=palette["ink_soft"],
        )
    )

    wm_bbox = watermark_bbox(plot_x1, footer_baseline_y, rt["watermark_tokens"], rt["watermark_lockup_svg"])
    manifest.update(
        {
            "text_runs": [
                "AAPL Event-Annotated Candlestick",
                f"Canonical Boltbird candlestick starter | mode {mode} | grayscale candles, explicit QA",
                "Source: synthetic OHLC demo data",
                "Adjusted close, USD",
                *[event["label"] for event in events],
                *[row["date"] for row in ohlc],
                *[label["text"] for label in y_labels],
                latest_text,
                "Powered by",
                "Boltbird",
            ],
            "y_axis_labels": y_labels,
            "x_ticks": x_ticks,
            "candles": candles_manifest,
            "candle_geometry": candle_geo,
            "latest_label": {
                "box": latest.box.__dict__,
                "point": {"x": latest_x, "y": latest_y},
                "line_end": {"x": latest.line_end_x, "y": latest.line_end_y},
                "text_anchor": latest.anchor,
                "use_line": latest.use_line,
            },
            "latest_obstacles": [rect.__dict__ for rect in recent_obstacles],
            "watermark_bbox": wm_bbox,
        }
    )

    svg[1] = render_qa_metadata(manifest)
    svg.append("</svg>")

    out_path = Path(args.output)
    out_path.write_text("".join(svg), encoding="utf-8")
    print(out_path)
    for line in font_report_lines(rt["font_plan"]):
        print(line, file=sys.stderr)

    if not args.no_png:
        export_script = SKILL_DIR / "scripts" / "export_preview_png.py"
        subprocess.run([sys.executable, str(export_script), str(out_path)], check=True)


if __name__ == "__main__":
    main()
