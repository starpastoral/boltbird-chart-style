from __future__ import annotations


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def resolve_candle_geometry(
    *,
    plot_width: float,
    candle_count: int,
    recipe_tokens: dict,
) -> dict:
    slot_width = plot_width / max(candle_count, 1)
    body_width = clamp(
        slot_width * recipe_tokens["body_width_ratio"],
        recipe_tokens["body_width_min_px"],
        recipe_tokens["body_width_max_px"],
    )
    gap = slot_width - body_width
    return {
        "slot_width": slot_width,
        "body_width": body_width,
        "body_half_width": body_width / 2.0,
        "body_gap": gap,
        "body_gap_ok": gap >= recipe_tokens["body_gap_min_px"],
    }


def resolve_price_bounds(
    *,
    ohlc: list[dict],
    top_padding_ratio: float = 0.14,
    bottom_padding_ratio: float = 0.08,
) -> tuple[float, float]:
    highs = [row["high"] for row in ohlc]
    lows = [row["low"] for row in ohlc]
    low = min(lows)
    high = max(highs)
    span = max(high - low, 1.0)
    return (
        low - span * bottom_padding_ratio,
        high + span * top_padding_ratio,
    )


def price_to_y(value: float, *, y_min: float, y_max: float, plot_y0: float, plot_y1: float) -> float:
    return plot_y1 - ((value - y_min) / (y_max - y_min)) * (plot_y1 - plot_y0)


__all__ = [
    "clamp",
    "price_to_y",
    "resolve_candle_geometry",
    "resolve_price_bounds",
]
