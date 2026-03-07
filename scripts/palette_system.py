from __future__ import annotations


def resolve_mode(tokens: dict, requested_mode: str | None = None) -> str:
    profiles = tokens.get("profiles", {})
    default_mode = profiles.get("default_mode", "consulting_safe")
    available = set(profiles.get("available_modes", [default_mode]))
    if requested_mode and requested_mode in available:
        return requested_mode
    return default_mode


def mode_policy(tokens: dict, requested_mode: str | None = None) -> dict:
    mode = resolve_mode(tokens, requested_mode)
    return tokens.get("profiles", {}).get(mode, {})


def recommended_chart_form(
    *,
    chart_kind: str,
    category_count: int,
    tokens: dict,
    requested_mode: str | None = None,
) -> str:
    policy = mode_policy(tokens, requested_mode)
    if chart_kind in {"pie", "donut"} and policy.get("prefer_chart_form_change"):
        if category_count > policy.get("pie_max_slices_before_bar", 6):
            return "bar"
    return chart_kind


def recommended_color_strategy(
    *,
    chart_kind: str,
    series_count: int = 1,
    category_count: int | None = None,
    tokens: dict,
    requested_mode: str | None = None,
) -> dict:
    palette = tokens.get("palette", {})
    policies = palette.get("role_policies", {})
    policy = mode_policy(tokens, requested_mode)
    kind = chart_kind.lower()
    base = policies.get(kind, "single_accent_first")

    if kind in {"pie", "donut"}:
        slices = category_count if category_count is not None else series_count
        forced_bar_threshold = policy.get("pie_max_slices_before_bar", 6)
        if slices > forced_bar_threshold and policy.get("prefer_chart_form_change"):
            return {
                "strategy": "change_chart_form",
                "recommended_form": "bar",
            }
        if slices >= policy.get("pie_external_labels_required_at", 5):
            return {
                "strategy": "single_hue_with_structural_labels",
                "recommended_form": kind,
            }

    if kind in {"bar", "column", "scatter", "bubble"}:
        accent_slots = 1 if series_count <= 1 else min(2, series_count)
        return {
            "strategy": base,
            "accent_slots": accent_slots,
            "neutral_rest": True,
        }

    if kind in {"grouped_bar", "stacked_bar", "line", "area"}:
        if series_count <= 4:
            return {
                "strategy": "single_accent_first",
                "accent_slots": min(series_count, 3),
                "neutral_rest": False,
            }
        return {
            "strategy": "highlight_plus_muted",
            "accent_slots": 2,
            "neutral_rest": True,
        }

    return {
        "strategy": base,
        "accent_slots": 1,
        "neutral_rest": True,
    }


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{max(0, min(255, c)):02X}" for c in rgb)


def _mix(hex_a: str, hex_b: str, ratio: float) -> str:
    a = _hex_to_rgb(hex_a)
    b = _hex_to_rgb(hex_b)
    mixed = tuple(round(a[i] * (1 - ratio) + b[i] * ratio) for i in range(3))
    return _rgb_to_hex(mixed)


def single_hue_ladder(base_hex: str, count: int) -> list[str]:
    if count <= 1:
        return [base_hex]
    dark = _mix(base_hex, "#233136", 0.18)
    light = _mix(base_hex, "#F0EEE8", 0.62)
    return [
        _mix(dark, light, i / max(count - 1, 1))
        for i in range(count)
    ]


def resolve_series_palette(
    *,
    count: int,
    palette_tokens: dict,
    chart_kind: str = "line",
    requested_mode: str | None = None,
    tokens: dict | None = None,
) -> list[str]:
    primary = palette_tokens["primary_accent"]
    reserves = palette_tokens["reserve_accents"]
    neutrals = palette_tokens["neutral_series"]
    quartet = palette_tokens["quartet"]
    policy = mode_policy(tokens or {}, requested_mode) if tokens else {}

    if chart_kind in {"pie", "donut"} and count >= policy.get("pie_external_labels_required_at", 5):
        return single_hue_ladder(primary, count)

    if count <= 1:
        return [primary]
    if count == 2:
        return [primary, neutrals[0]]
    if count == 3:
        return [primary, reserves[0], reserves[1]]
    if count == 4:
        return quartet[:4]

    # highlight-plus-muted: preserve the first three/four identities and fade the rest
    colors = quartet[:4]
    extra = count - len(colors)
    for i in range(extra):
        colors.append(neutrals[min(i, len(neutrals) - 1)])
    return colors[:count]
