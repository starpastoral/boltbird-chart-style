from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree as ET


SVG_NS = {"svg": "http://www.w3.org/2000/svg"}


def _escape_json(raw: str) -> str:
    return (
        raw.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_qa_metadata(manifest: dict) -> str:
    payload = json.dumps(manifest, separators=(",", ":"), sort_keys=True)
    return f'<metadata id="boltbird-qa">{_escape_json(payload)}</metadata>'


def load_qa_manifest(svg_path: str | Path) -> dict:
    root = ET.fromstring(Path(svg_path).read_text(encoding="utf-8"))
    metadata = root.find("svg:metadata[@id='boltbird-qa']", SVG_NS)
    if metadata is None or metadata.text is None:
        raise SystemExit(f"Missing boltbird QA metadata in {svg_path}")
    return json.loads(metadata.text)


__all__ = [
    "load_qa_manifest",
    "render_qa_metadata",
]
