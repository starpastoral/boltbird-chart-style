#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from font_runtime import font_report_lines
from runtime import load_runtime


def main() -> int:
    rt = load_runtime(SKILL_DIR)
    for line in font_report_lines(rt["font_plan"]):
        print(line)
    return 0 if not rt["font_plan"]["missing_roles"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
