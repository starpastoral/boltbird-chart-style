#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont


SKILL_DIR = Path(__file__).resolve().parents[1]
ASSET_PATH = SKILL_DIR / "assets" / "watermark-lockup.svg"
MARK_PATH = SKILL_DIR / "assets" / "boltbird-mark.svg"

CANVAS_WIDTH = 352
CANVAS_HEIGHT = 96
BASELINE_Y = 78
PREFIX_TEXT = "Powered by"
WORDMARK_TEXT = "Boltbird"
PREFIX_X = 0
WORDMARK_X = 168
PREFIX_SIZE = 28
WORDMARK_SIZE = 34
ICON_X = 306
ICON_Y = 28
ICON_SCALE = 0.195


def resolve_font_paths() -> tuple[Path, Path]:
    primary = Path("~/Library/Fonts/Geist-VariableFont_wght.ttf").expanduser()
    wordmark = Path("~/Library/Fonts/SourceSerif4-VariableFont_opsz,wght.ttf").expanduser()
    if not primary.exists() or not wordmark.exists():
        raise SystemExit("Missing required local font files to build watermark lockup asset.")
    return primary, wordmark


def load_font(path: Path, location: dict[str, float]) -> TTFont:
    font = TTFont(path)
    if "fvar" in font:
        font = instantiateVariableFont(font, location, inplace=False)
    return font


def glyph_group(font: TTFont, text: str, *, x: float, baseline_y: float, font_size: float) -> ET.Element:
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    units_per_em = font["head"].unitsPerEm
    scale = font_size / units_per_em
    cursor = x

    group = ET.Element("g", {"fill": "currentColor"})
    for char in text:
        if char == " ":
            cursor += hmtx["space"][0] * scale
            continue
        glyph_name = cmap.get(ord(char))
        if glyph_name is None:
            raise SystemExit(f"Missing glyph for {char!r}")
        pen = SVGPathPen(glyph_set)
        glyph_set[glyph_name].draw(pen)
        d = pen.getCommands()
        path = ET.SubElement(
            group,
            "path",
            {
                "d": d,
                "transform": f"translate({cursor:.3f} {baseline_y:.3f}) scale({scale:.6f} {-scale:.6f})",
            },
        )
        advance = hmtx[glyph_name][0] * scale
        cursor += advance
    return group


def load_mark_group() -> ET.Element:
    root = ET.fromstring(MARK_PATH.read_text(encoding="utf-8"))
    group = ET.Element(
        "g",
        {
            "transform": f"translate({ICON_X} {ICON_Y}) scale({ICON_SCALE})",
            "fill": "currentColor",
        },
    )
    for child in list(root):
        tag = child.tag.rsplit("}", 1)[-1]
        if tag != "path":
            continue
        group.append(ET.fromstring(ET.tostring(child, encoding="unicode")))
    return group


def main() -> None:
    primary_path, wordmark_path = resolve_font_paths()
    primary_font = load_font(primary_path, {"wght": 600})
    wordmark_font = load_font(wordmark_path, {"wght": 700, "opsz": 34})

    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(CANVAS_WIDTH),
            "height": str(CANVAS_HEIGHT),
            "viewBox": f"0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}",
            "fill": "none",
        },
    )
    root_group = ET.SubElement(svg, "g", {"fill": "currentColor"})
    root_group.append(glyph_group(primary_font, PREFIX_TEXT, x=PREFIX_X, baseline_y=BASELINE_Y, font_size=PREFIX_SIZE))
    root_group.append(glyph_group(wordmark_font, WORDMARK_TEXT, x=WORDMARK_X, baseline_y=BASELINE_Y, font_size=WORDMARK_SIZE))
    root_group.append(load_mark_group())

    xml = ET.tostring(svg, encoding="unicode")
    ASSET_PATH.write_text(xml, encoding="utf-8")
    print(ASSET_PATH)


if __name__ == "__main__":
    main()
