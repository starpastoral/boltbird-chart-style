from __future__ import annotations

import io
import os
import re
from pathlib import Path
from xml.etree import ElementTree as ET


SVG_NS = "{http://www.w3.org/2000/svg}"


RGBA_RE = re.compile(
    r"rgba?\(\s*(?P<r>\d+)\s*,\s*(?P<g>\d+)\s*,\s*(?P<b>\d+)\s*(?:,\s*(?P<a>\d*\.?\d+)\s*)?\)"
)


def configure_matplotlib_env(cache_root: str | Path) -> Path:
    root = Path(cache_root).expanduser().resolve()
    cache_dir = root / "matplotlib-cache"
    xdg_cache = root / "xdg-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    xdg_cache.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(cache_dir)
    os.environ["XDG_CACHE_HOME"] = str(xdg_cache)
    return cache_dir


def require_matplotlib():
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
        raise SystemExit(
            "matplotlib is not installed. Install it only if you need the geometry-only adapter."
        ) from exc
    return plt


def mpl_color(color: str):
    match = RGBA_RE.fullmatch(color.strip())
    if not match:
        return color
    alpha = float(match.group("a")) if match.group("a") is not None else 1.0
    return (
        int(match.group("r")) / 255.0,
        int(match.group("g")) / 255.0,
        int(match.group("b")) / 255.0,
        alpha,
    )


def prepare_axes_for_geometry_only(
    fig,
    ax,
    *,
    tokens: dict,
    grid_axis: str = "y",
) -> None:
    palette = tokens["palette"]
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    ax.set_title("")
    ax.set_xlabel("")
    ax.set_ylabel("")
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()

    ax.tick_params(
        axis="both",
        which="both",
        length=0,
        labelbottom=False,
        labelleft=False,
    )
    for spine_name in ("top", "right"):
        ax.spines[spine_name].set_visible(False)
    for spine_name in ("left", "bottom"):
        spine = ax.spines[spine_name]
        spine.set_color(mpl_color(palette["grid_major"]))
        spine.set_linewidth(1.0)

    ax.grid(False)
    if grid_axis in {"x", "y", "both"}:
        ax.grid(
            axis=grid_axis,
            color=mpl_color(palette["grid_major"]),
            linewidth=1.0,
            alpha=1.0,
        )


def _parse_length(raw: str | None) -> float:
    if raw is None:
        return 0.0
    value = raw.strip()
    if value.endswith("pt"):
        return float(value[:-2]) * 96.0 / 72.0
    if value.endswith("px"):
        return float(value[:-2])
    return float(value)


def figure_to_svg_fragment(fig) -> dict:
    buffer = io.StringIO()
    fig.savefig(
        buffer,
        format="svg",
        transparent=True,
        bbox_inches=None,
        pad_inches=0,
    )
    root = ET.fromstring(buffer.getvalue())
    view_box = root.get("viewBox")
    if view_box:
        _, _, width, height = (float(part) for part in view_box.split())
    else:
        width = _parse_length(root.get("width"))
        height = _parse_length(root.get("height"))

    parts: list[str] = []
    for child in list(root):
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "metadata":
            continue
        parts.append(ET.tostring(child, encoding="unicode"))

    return {
        "view_width": width,
        "view_height": height,
        "content": "".join(parts),
    }


def wrap_svg_fragment(
    fragment: dict,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    clip_id: str = "plot-clip",
) -> list[str]:
    sx = width / fragment["view_width"]
    sy = height / fragment["view_height"]
    return [
        "<defs>",
        f'<clipPath id="{clip_id}"><rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}"/></clipPath>',
        "</defs>",
        f'<g clip-path="url(#{clip_id})">',
        f'<g transform="translate({x:.2f} {y:.2f}) scale({sx:.6f} {sy:.6f})">',
        fragment["content"],
        "</g>",
        "</g>",
    ]


__all__ = [
    "configure_matplotlib_env",
    "figure_to_svg_fragment",
    "mpl_color",
    "prepare_axes_for_geometry_only",
    "require_matplotlib",
    "wrap_svg_fragment",
]
