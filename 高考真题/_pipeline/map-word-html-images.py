#!/usr/bin/env python3
"""Map DOCX image relationships to raster images from Word's filtered HTML export."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET


R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
P_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
VML_IMAGE = "{urn:schemas-microsoft-com:vml}imagedata"
DRAWING_IMAGE = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("docx", type=Path)
    parser.add_argument("html", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    with zipfile.ZipFile(args.docx) as archive:
        rel_root = ET.fromstring(archive.read("word/_rels/document.xml.rels"))
        relationships = {
            element.attrib["Id"]: element.attrib["Target"]
            for element in rel_root.findall(f"{{{P_NS}}}Relationship")
        }
        document = ET.fromstring(archive.read("word/document.xml"))
        targets = []
        for element in document.iter():
            if element.tag == VML_IMAGE:
                rel_id = element.attrib.get(f"{{{R_NS}}}id")
            elif element.tag == DRAWING_IMAGE:
                rel_id = element.attrib.get(f"{{{R_NS}}}embed")
            else:
                continue
            if rel_id in relationships:
                targets.append(str(PurePosixPath("word") / relationships[rel_id]))

    html_bytes = args.html.read_bytes()
    charset_match = re.search(rb"charset\s*=\s*([A-Za-z0-9_-]+)", html_bytes[:4096], re.I)
    charset = charset_match.group(1).decode("ascii") if charset_match else "utf-8"
    sources = [
        match.decode(charset)
        for match in re.findall(rb"<img\b[^>]*?\bsrc=[\"']?([^\"' >]+)", html_bytes, re.I)
    ]
    sources = [source for source in sources if not source.lower().endswith("header.html")]
    if len(targets) != len(sources):
        raise SystemExit(f"Image count mismatch: DOCX={len(targets)}, HTML={len(sources)}")

    html_dir = args.html.parent
    mapped: dict[str, list[dict]] = defaultdict(list)
    occurrences = []
    for index, (target, source) in enumerate(zip(targets, sources)):
        raster = html_dir / source
        digest = hashlib.sha256(raster.read_bytes()).hexdigest()
        item = {"index": index, "target": target, "raster": str(raster), "sha256": digest}
        occurrences.append(item)
        mapped[target].append({"raster": str(raster), "sha256": digest})

    conflicts = {
        target: entries
        for target, entries in mapped.items()
        if len({entry["sha256"] for entry in entries}) > 1
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "docx": str(args.docx),
                "html": str(args.html),
                "occurrences": occurrences,
                "by_target": mapped,
                "conflicts": conflicts,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"mapped {len(occurrences)} occurrences, {len(mapped)} targets, {len(conflicts)} conflicts")


if __name__ == "__main__":
    main()
