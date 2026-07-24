#!/usr/bin/env python3
"""OCR formula images from a DOCX/HTML image map with local pix2tex."""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import time
from collections import defaultdict
from pathlib import Path


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG file: {path}")
    return struct.unpack(">II", header[16:24])


def is_formula(target: str, source_assets: Path) -> bool:
    name = Path(target).name
    if name.lower().endswith(".wmf"):
        return True
    width, height = png_size(source_assets / name)
    # In these WPS exports, formulas are generally short inline images.
    return height < 78


def save(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mapping", type=Path)
    parser.add_argument("source_assets", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--rerun-extension", choices=("png", "wmf"))
    parser.add_argument("--scale", type=int, default=1)
    args = parser.parse_args()

    tool_path = Path.home() / "tools" / "latexocr"
    sys.path.insert(0, str(tool_path))
    os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")
    os.environ.setdefault("TRANSFORMERS_CACHE", "/tmp/huggingface-cache")
    from PIL import Image
    from pix2tex.cli import LatexOCR

    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    grouped: dict[str, list[tuple[str, Path]]] = defaultdict(list)
    for target, entries in mapping["by_target"].items():
        if is_formula(target, args.source_assets):
            grouped[entries[0]["sha256"]].append((target, Path(entries[0]["raster"])))

    if args.output.exists():
        result = json.loads(args.output.read_text(encoding="utf-8"))
    else:
        result = {"formulas": {}, "by_hash": {}}
    completed = set(result.get("by_hash", {}))
    pending = []
    for digest, entries in grouped.items():
        extension = Path(entries[0][0]).suffix.lower().lstrip(".")
        if args.rerun_extension:
            if extension == args.rerun_extension:
                pending.append((digest, entries))
        elif digest not in completed:
            pending.append((digest, entries))
    if args.limit is not None:
        pending = pending[: args.limit]

    print(f"formula targets={sum(map(len, grouped.values()))}, unique={len(grouped)}, pending={len(pending)}", flush=True)
    if not pending:
        return

    model = LatexOCR()
    started = time.monotonic()
    for number, (digest, entries) in enumerate(pending, 1):
        image = Image.open(entries[0][1])
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")
        if args.scale > 1:
            image = image.resize(
                (image.width * args.scale, image.height * args.scale),
                Image.Resampling.LANCZOS,
            )
        extrema = image.getextrema()
        is_uniform = all(low == high for low, high in extrema)
        try:
            latex = r"\text{公式缺失}" if is_uniform else model(image).strip()
        except Exception as error:
            latex = r"\text{公式缺失}"
            print(
                f"warning: skipped {entries[0][0]} ({type(error).__name__}: {error})",
                flush=True,
            )
        result.setdefault("by_hash", {})[digest] = latex
        for target, raster in entries:
            result.setdefault("formulas", {})[Path(target).name] = {
                "latex": latex,
                "sha256": digest,
                "raster": str(raster),
                "method": "pix2tex",
            }
        if number % 10 == 0 or number == len(pending):
            save(args.output, result)
            elapsed = time.monotonic() - started
            print(f"{number}/{len(pending)} ({elapsed / number:.2f}s each)", flush=True)


if __name__ == "__main__":
    main()
