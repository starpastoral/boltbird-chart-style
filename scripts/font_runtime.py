from __future__ import annotations

import base64
import mimetypes
from pathlib import Path


def _candidate_paths(skill_dir: Path, spec: dict) -> list[Path]:
    candidates: list[Path] = []
    for raw in spec.get("bundled_candidates", []):
        candidates.append((skill_dir / raw).resolve())
    for raw in spec.get("local_candidates", []):
        candidates.append(Path(raw).expanduser())
    return candidates


def _resolve_existing_path(candidates: list[Path]) -> Path | None:
    for path in candidates:
        if path.exists() and path.is_file():
            return path
    return None


def _font_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".woff2":
        return "woff2"
    if suffix == ".woff":
        return "woff"
    if suffix == ".otf":
        return "opentype"
    return "truetype"


def _mime_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "font/ttf"


def resolve_font_plan(skill_dir: str | Path, tokens: dict) -> dict:
    skill_path = Path(skill_dir).resolve()
    typography = tokens.get("typography", {})
    roles: dict[str, dict] = {}
    missing_roles: list[str] = []

    for role, spec in typography.get("font_sources", {}).items():
        candidates = _candidate_paths(skill_path, spec)
        resolved = _resolve_existing_path(candidates)
        role_plan = {
            "role": role,
            "family": spec["family"],
            "css_class": spec["css_class"],
            "fallback_stack": spec["fallback_stack"],
            "font_style": spec.get("font_style", "normal"),
            "font_weight": spec.get("font_weight", "400"),
            "resolved_path": resolved,
            "candidates": [str(path) for path in candidates],
            "source_kind": (
                "bundled"
                if resolved and resolved.is_relative_to(skill_path)
                else "local"
                if resolved
                else "fallback"
            ),
        }
        roles[role] = role_plan
        if resolved is None:
            missing_roles.append(role)

    return {
        "embed_fonts": bool(typography.get("svg_embed_fonts", True)),
        "roles": roles,
        "missing_roles": missing_roles,
    }


def _inline_font_src(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"url('data:{_mime_type(path)};base64,{encoded}') format('{_font_format(path)}')"


def build_font_face_rules(font_plan: dict, *, embed_fonts: bool | None = None) -> list[str]:
    if embed_fonts is None:
        embed_fonts = bool(font_plan.get("embed_fonts", True))

    rules: list[str] = []
    for role_plan in font_plan["roles"].values():
        path = role_plan["resolved_path"]
        if path is None:
            continue
        if not embed_fonts:
            src = f"url('{path.as_uri()}') format('{_font_format(path)}')"
        else:
            src = _inline_font_src(path)
        rules.append(
            "@font-face{"
            f"font-family:'{role_plan['family']}';"
            f"src:{src};"
            f"font-style:{role_plan['font_style']};"
            f"font-weight:{role_plan['font_weight']};"
            "font-display:block;"
            "}"
        )
    return rules


def build_font_class_rules(font_plan: dict) -> list[str]:
    return [
        f".{role_plan['css_class']}{{font-family:{role_plan['fallback_stack']};}}"
        for role_plan in font_plan["roles"].values()
    ]


def font_stack_for_role(font_plan: dict, role: str) -> str:
    role_plan = font_plan["roles"].get(role)
    if role_plan is None:
        raise KeyError(f"Unknown font role: {role}")
    return role_plan["fallback_stack"]


def build_svg_style_block(font_plan: dict, *, embed_fonts: bool | None = None) -> str:
    rules = build_font_face_rules(font_plan, embed_fonts=embed_fonts)
    rules.extend(build_font_class_rules(font_plan))
    missing_roles = font_plan.get("missing_roles", [])
    if missing_roles:
        rules.append(f"/* unresolved font roles: {', '.join(missing_roles)} */")
    return f"<style>{''.join(rules)}</style>"


def font_report_lines(font_plan: dict) -> list[str]:
    lines: list[str] = []
    for role, role_plan in font_plan["roles"].items():
        path = role_plan["resolved_path"]
        if path is None:
            lines.append(f"{role}: fallback-only ({role_plan['family']})")
            continue
        lines.append(f"{role}: {role_plan['family']} <- {path} [{role_plan['source_kind']}]")
    return lines


__all__ = [
    "build_font_class_rules",
    "build_font_face_rules",
    "build_svg_style_block",
    "font_stack_for_role",
    "font_report_lines",
    "resolve_font_plan",
]
