#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from qa_runtime import load_qa_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Boltbird chart QA checks against an SVG with embedded QA metadata.")
    parser.add_argument("svg", help="Input SVG path.")
    return parser.parse_args()


def rects_intersect(a: dict, b: dict, pad: float = 0.0) -> bool:
    return not (
        a["x1"] + pad < b["x0"]
        or a["x0"] - pad > b["x1"]
        or a["y1"] + pad < b["y0"]
        or a["y0"] - pad > b["y1"]
    )


def point_on_rect_edge(point: dict, rect: dict, tol: float = 2.0) -> bool:
    x = point["x"]
    y = point["y"]
    on_vertical = (abs(x - rect["x0"]) <= tol or abs(x - rect["x1"]) <= tol) and rect["y0"] - tol <= y <= rect["y1"] + tol
    on_horizontal = (abs(y - rect["y0"]) <= tol or abs(y - rect["y1"]) <= tol) and rect["x0"] - tol <= x <= rect["x1"] + tol
    return on_vertical or on_horizontal


def run_checks(manifest: dict) -> list[str]:
    findings: list[str] = []
    thresholds = manifest.get("qa_thresholds", {})
    plot = manifest["plot"]
    text_policy = manifest.get("text_policy", {})

    if manifest.get("font_plan_missing_roles"):
        findings.append(f"missing-fonts: unresolved roles {manifest['font_plan_missing_roles']}")

    if manifest.get("background") != "transparent":
        findings.append(f"background: expected transparent, got {manifest.get('background')}")

    if manifest.get("chart_kind") == "candlestick" and manifest.get("watermark_render_mode") != "svg_asset":
        findings.append(f"watermark-render-mode: expected svg_asset, got {manifest.get('watermark_render_mode')}")

    if (
        text_policy.get("default_chart_language") == "en"
        and not text_policy.get("allow_non_english_text_by_default", False)
    ):
        bad_runs = [text for text in manifest.get("text_runs", []) if any(ord(ch) > 127 for ch in text)]
        if bad_runs:
            findings.append(f"non-english-text: found non-ASCII text runs {bad_runs}")

    max_y_gap = thresholds.get("y_axis_label_max_gap_px", 24)
    for label in manifest.get("y_axis_labels", []):
        gap = plot["x0"] - label["x"]
        if gap > max_y_gap:
            findings.append(f"y-axis-gap: label {label['text']} gap {gap:.1f}px > {max_y_gap}px")
        if label["y"] < plot["y0"] or label["y"] > plot["y1"]:
            findings.append(f"y-axis-bounds: label {label['text']} y={label['y']:.1f}px leaves plot bounds")

    tick_positions = [tick["x"] for tick in manifest.get("x_ticks", [])]
    min_tick_gap = thresholds.get("x_tick_min_gap_px", 44)
    if len(tick_positions) >= 2:
        actual = min(b - a for a, b in zip(tick_positions, tick_positions[1:]))
        if actual < min_tick_gap:
            findings.append(f"x-tick-density: min gap {actual:.1f}px < {min_tick_gap}px")

    candles = manifest.get("candles", [])
    min_body_gap = thresholds.get("body_gap_min_px", 1.5)
    if len(candles) >= 2:
        actual = min(next_candle["body_left"] - candle["body_right"] for candle, next_candle in zip(candles, candles[1:]))
        if actual < min_body_gap:
            findings.append(f"candlestick-gap: min body gap {actual:.2f}px < {min_body_gap}px")

    latest_label = manifest.get("latest_label", {})
    latest_box = latest_label.get("box")
    pad = thresholds.get("latest_label_obstacle_pad_px", 8)
    if latest_box is not None:
        for obstacle in manifest.get("latest_obstacles", []):
            if rects_intersect(latest_box, obstacle, pad=pad):
                findings.append("latest-label-collision: latest label intersects recent candle obstacle field")
                break
        if latest_box["x0"] < plot["x0"] or latest_box["x1"] > plot["x1"] or latest_box["y0"] < plot["y0"] or latest_box["y1"] > plot["y1"]:
            findings.append("latest-label-bounds: latest label box leaves plot bounds")
        if latest_label.get("use_line"):
            line_end = latest_label.get("line_end")
            if line_end and not point_on_rect_edge(line_end, latest_box):
                findings.append("latest-label-leader: leader line does not terminate on label box edge")

    watermark = manifest.get("watermark_bbox")
    clearance = thresholds.get("watermark_plot_clearance_px", 24)
    if watermark is not None:
        if watermark["y1"] > plot["y0"] - clearance:
            findings.append(
                f"watermark-clearance: watermark bottom {watermark['y1']:.1f}px intrudes into plot safe zone"
            )
        canvas = manifest.get("canvas", {})
        if watermark["x0"] < 0 or watermark["y0"] < 0 or watermark["x1"] > canvas.get("width", 0) or watermark["y1"] > canvas.get("height", 0):
            findings.append("watermark-bounds: watermark exceeds canvas bounds")

    return findings


def main() -> int:
    args = parse_args()
    svg_path = Path(args.svg).expanduser().resolve()
    manifest = load_qa_manifest(svg_path)
    findings = run_checks(manifest)
    if findings:
        print(f"FAIL {svg_path}")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"PASS {svg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
