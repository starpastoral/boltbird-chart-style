from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree as ET


def safe(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def draw_text(
    x: float,
    y: float,
    text: str,
    *,
    klass: str,
    size: int,
    weight: int,
    fill: str,
    anchor: str = "start",
    letter_spacing: float | None = None,
    font_family: str | None = None,
) -> str:
    extra = ""
    if letter_spacing is not None:
        extra += f' letter-spacing="{letter_spacing}"'
    if font_family is not None:
        extra += f' font-family="{safe(font_family)}"'
    return (
        f'<text class="{klass}" x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}"{extra}>'
        f"{safe(text)}</text>"
    )


def draw_rotated_y_axis_title(
    *,
    x: float,
    y_center: float,
    text: str,
    klass: str,
    size: int,
    weight: int,
    fill: str,
) -> str:
    return (
        f'<text class="{klass}" transform="translate({x:.2f} {y_center:.2f}) rotate(-90)" '
        f'text-anchor="middle" font-size="{size}" font-weight="{weight}" fill="{fill}">{safe(text)}</text>'
    )


def render_metadata_block(
    *,
    width: float,
    plot_x0: float,
    plot_x1: float,
    title: str,
    subtitle: str,
    source: str,
    title_fill: str,
    body_fill: str,
    title_size: int,
    subtitle_size: int,
    meta_size: int,
    metadata_tokens: dict,
    extra_right: str | None = None,
) -> list[str]:
    title_y = metadata_tokens["title_y_px"]
    subtitle_y = metadata_tokens["subtitle_y_px"]
    source_y = metadata_tokens.get("source_y_px", subtitle_y)
    parts = [
        draw_text(
            width / 2,
            title_y,
            title,
            klass="geist",
            size=title_size,
            weight=600,
            fill=title_fill,
            anchor="middle",
            letter_spacing=-0.35,
        ),
        draw_text(
            width / 2,
            subtitle_y,
            subtitle,
            klass="geist",
            size=subtitle_size,
            weight=500,
            fill=body_fill,
            anchor="middle",
        ),
        draw_text(
            plot_x0,
            source_y,
            source,
            klass="geist",
            size=meta_size,
            weight=500,
            fill=body_fill,
        ),
    ]
    if extra_right:
        parts.append(
            draw_text(
                plot_x1,
                subtitle_y,
                extra_right,
                klass="gscode",
                size=max(meta_size - 1, 12),
                weight=500,
                fill=body_fill,
                anchor="end",
            )
        )
    return parts


def render_metadata_footer_row(
    *,
    plot_x0: float,
    plot_x1: float,
    baseline_y: float,
    rule_y: float | None,
    source: str,
    source_fill: str,
    source_size: int,
    watermark_parts: list[str] | None = None,
    rule_stroke: str | None = None,
) -> list[str]:
    parts = [
        draw_text(
            plot_x0,
            baseline_y,
            source,
            klass="geist",
            size=source_size,
            weight=500,
            fill=source_fill,
        ),
    ]
    if rule_y is not None and rule_stroke:
        parts.insert(
            0,
            f'<line x1="{plot_x0:.2f}" y1="{rule_y:.2f}" x2="{plot_x1:.2f}" y2="{rule_y:.2f}" stroke="{rule_stroke}" stroke-width="1.0"/>',
        )
    if watermark_parts:
        parts.extend(watermark_parts)
    return parts


def render_legend(
    *,
    width: float,
    plot_x1: float,
    plot_y0: float,
    items: list[dict],
    subtitle_y: float,
    layout_tokens: dict,
    legend_tokens: dict,
    body_fill: str,
) -> list[str]:
    if not items:
        return []

    sample_len = legend_tokens["sample_length_px"]
    label_gap = legend_tokens["label_gap_px"]
    item_gap = legend_tokens["item_gap_px"]
    row_gap = legend_tokens["row_gap_px"]
    text_shift = legend_tokens["text_baseline_shift_px"]
    base_stroke_width = legend_tokens["sample_stroke_width_px"]
    parts: list[str] = []

    if len(items) <= layout_tokens["legend_inline_threshold"]:
        legend_y = subtitle_y + layout_tokens["legend_gap_y_px"]
        total_width = 0.0
        item_widths: list[float] = []
        for item in items:
            label_width = max(len(item["label"]) * 8.8, 28)
            width_i = sample_len + label_gap + label_width
            item_widths.append(width_i)
            total_width += width_i
        total_width += item_gap * max(len(items) - 1, 0)
        cursor = width / 2 - total_width / 2 + legend_tokens.get("inline_center_nudge_px", 0)
        for item, width_i in zip(items, item_widths):
            stroke = item.get("stroke", body_fill)
            stroke_width = item.get("stroke_width", base_stroke_width)
            parts.append(
                f'<line x1="{cursor:.2f}" y1="{legend_y:.2f}" x2="{cursor + sample_len:.2f}" y2="{legend_y:.2f}" '
                f'stroke="{stroke}" stroke-width="{stroke_width:.2f}" stroke-linecap="round"/>'
            )
            parts.append(
                draw_text(
                    cursor + sample_len + label_gap,
                    legend_y + text_shift,
                    item["label"],
                    klass="geist",
                    size=17,
                    weight=600,
                    fill=body_fill,
                )
            )
            cursor += width_i + item_gap
    else:
        x = max(layout_tokens["legend_vertical_x_px"], plot_x1 + legend_tokens.get("outside_gap_px", 20))
        if layout_tokens.get("legend_vertical_anchor") == "plot_top":
            y = plot_y0 + layout_tokens.get("legend_vertical_top_offset_px", 16)
        else:
            y = layout_tokens["legend_vertical_top_px"]
        for item in items:
            stroke = item.get("stroke", body_fill)
            stroke_width = item.get("stroke_width", base_stroke_width)
            parts.append(
                f'<line x1="{x:.2f}" y1="{y:.2f}" x2="{x + sample_len:.2f}" y2="{y:.2f}" '
                f'stroke="{stroke}" stroke-width="{stroke_width:.2f}" stroke-linecap="round"/>'
            )
            parts.append(
                draw_text(
                    x + sample_len + label_gap,
                    y + text_shift,
                    item["label"],
                    klass="geist",
                    size=17,
                    weight=600,
                    fill=body_fill,
                )
            )
            y += row_gap
    return parts


def render_watermark(
    *,
    right_edge: float,
    baseline_y: float,
    watermark_tokens: dict,
    fill: str,
    watermark_asset: dict,
) -> list[str]:
    if watermark_tokens.get("anchor_mode") == "icon_right_edge":
        wm_x = right_edge - watermark_tokens["icon_right_edge_px"]
    else:
        wm_x = right_edge - watermark_tokens["width_px"]
    wm_y = baseline_y - watermark_tokens["baseline_y_px"]
    return [
        f'<g transform="translate({wm_x},{wm_y})" opacity="{watermark_tokens["opacity"]}">',
        f'<g color="{fill}" fill="{fill}">',
        watermark_asset["content"],
        "</g></g>",
    ]


def load_svg_asset(svg_path: Path) -> dict:
    text = svg_path.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    view_box = root.get("viewBox")
    if view_box:
        _, _, width, height = (float(part) for part in view_box.split())
    else:
        width = float(root.get("width", "0"))
        height = float(root.get("height", "0"))
    content = "".join(ET.tostring(child, encoding="unicode") for child in list(root))
    content = re.sub(r"\s+xmlns(:\w+)?=\"[^\"]+\"", "", content)
    content = re.sub(r"(<\/?)ns\d+:", r"\1", content)
    return {
        "width": width,
        "height": height,
        "content": content,
    }


def load_single_path_d(svg_path: Path) -> str:
    text = svg_path.read_text(encoding="utf-8")
    match = re.search(r'<path[^>]* d="([^"]+)"', text)
    if not match:
        raise ValueError(f"No <path d=...> found in {svg_path}")
    return match.group(1)
