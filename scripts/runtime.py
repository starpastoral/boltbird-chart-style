from __future__ import annotations

import json
from pathlib import Path

from palette_system import (
    mode_policy,
    recommended_chart_form,
    recommended_color_strategy,
    resolve_mode,
    resolve_series_palette,
    single_hue_ladder,
)
from svg_chrome import load_single_path_d


def skill_dir_from(current_file: str | Path) -> Path:
    return Path(current_file).resolve().parent.parent


def load_tokens(skill_dir: str | Path) -> dict:
    skill_path = Path(skill_dir)
    return json.loads((skill_path / "assets" / "style-tokens.json").read_text(encoding="utf-8"))


def load_runtime(skill_dir: str | Path, requested_mode: str | None = None) -> dict:
    skill_path = Path(skill_dir)
    tokens = load_tokens(skill_path)
    mode = resolve_mode(tokens, requested_mode)
    watermark = tokens.get("watermark", {})
    return {
        "skill_dir": skill_path,
        "tokens": tokens,
        "mode": mode,
        "policy": mode_policy(tokens, mode),
        "watermark_tokens": watermark,
        "watermark_icon_asset": skill_path / "assets" / Path(watermark.get("icon_asset", "./boltbird-mark.svg")).name,
        "watermark_lockup_asset": skill_path / "assets" / Path(watermark.get("lockup_asset", "./watermark-lockup.svg")).name,
        "watermark_icon_path": load_single_path_d(skill_path / "assets" / "boltbird-mark.svg"),
    }


def chart_plan(
    *,
    chart_kind: str,
    series_count: int = 1,
    category_count: int | None = None,
    tokens: dict,
    requested_mode: str | None = None,
) -> dict:
    resolved_form = recommended_chart_form(
        chart_kind=chart_kind,
        category_count=category_count or series_count,
        tokens=tokens,
        requested_mode=requested_mode,
    )
    color_policy = recommended_color_strategy(
        chart_kind=chart_kind,
        series_count=series_count,
        category_count=category_count,
        tokens=tokens,
        requested_mode=requested_mode,
    )
    return {
        "requested_form": chart_kind,
        "resolved_form": resolved_form,
        "color_policy": color_policy,
    }


def series_palette(
    *,
    chart_kind: str,
    count: int,
    tokens: dict,
    requested_mode: str | None = None,
) -> list[str]:
    return resolve_series_palette(
        count=count,
        palette_tokens=tokens["palette"],
        chart_kind=chart_kind,
        requested_mode=requested_mode,
        tokens=tokens,
    )


__all__ = [
    "chart_plan",
    "load_runtime",
    "load_tokens",
    "mode_policy",
    "recommended_chart_form",
    "recommended_color_strategy",
    "resolve_mode",
    "resolve_series_palette",
    "series_palette",
    "single_hue_ladder",
    "skill_dir_from",
]
