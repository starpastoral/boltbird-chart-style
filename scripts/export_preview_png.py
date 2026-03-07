#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def choose_backend(requested: str) -> str:
    candidates = ["rsvg-convert", "magick", "qlmanage"] if requested == "auto" else [requested]
    for name in candidates:
        if shutil.which(name):
            return name
    raise SystemExit("No supported SVG to PNG backend found. Tried: rsvg-convert, magick, qlmanage")


def export_with_rsvg(svg_path: Path, png_path: Path, scale: float) -> None:
    cmd = [
        "rsvg-convert",
        "-z",
        f"{scale}",
        str(svg_path),
        "-o",
        str(png_path),
    ]
    subprocess.run(cmd, check=True)


def export_with_magick(svg_path: Path, png_path: Path, scale: float) -> None:
    density = int(round(72 * scale))
    cmd = [
        "magick",
        "-background",
        "none",
        "-density",
        str(density),
        str(svg_path),
        str(png_path),
    ]
    subprocess.run(cmd, check=True)


def export_with_qlmanage(svg_path: Path, png_path: Path, scale: float) -> None:
    out_dir = png_path.parent
    size = int(round(1600 * scale))
    subprocess.run(
        [
            "qlmanage",
            "-t",
            "-s",
            str(size),
            "-o",
            str(out_dir),
            str(svg_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    generated = sorted(out_dir.glob(f"{svg_path.name}*.png"))
    if not generated:
        raise SystemExit("qlmanage did not generate a PNG preview.")
    generated[-1].replace(png_path)


def export_svg_to_png(svg_path: Path, png_path: Path, scale: float, backend: str) -> str:
    if backend == "rsvg-convert":
        export_with_rsvg(svg_path, png_path, scale)
    elif backend == "magick":
        export_with_magick(svg_path, png_path, scale)
    elif backend == "qlmanage":
        export_with_qlmanage(svg_path, png_path, scale)
    else:
        raise SystemExit(f"Unsupported backend: {backend}")
    return backend


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a PNG preview from an SVG chart.")
    parser.add_argument("svg", help="Input SVG file.")
    parser.add_argument("--output", help="Output PNG path. Defaults to the same stem as the SVG.")
    parser.add_argument("--scale", type=float, default=2.0, help="Raster export scale multiplier. Default: 2.0")
    parser.add_argument(
        "--backend",
        choices=["auto", "rsvg-convert", "magick", "qlmanage"],
        default="auto",
        help="Rendering backend. Default: auto",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    svg_path = Path(args.svg).expanduser().resolve()
    if not svg_path.exists():
        raise SystemExit(f"Missing SVG file: {svg_path}")
    png_path = Path(args.output).expanduser().resolve() if args.output else svg_path.with_suffix(".png")
    backend = choose_backend(args.backend)
    used = export_svg_to_png(svg_path, png_path, args.scale, backend)
    print(f"{png_path}\nbackend={used}\nscale={args.scale}")


if __name__ == "__main__":
    main()
