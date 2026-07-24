#!/usr/bin/env python3
"""Extract ordered text and image references from a Word DOCX file."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "o": "urn:schemas-microsoft-com:office:office",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "v": "urn:schemas-microsoft-com:vml",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def qname(prefix: str, name: str) -> str:
    return f"{{{NS[prefix]}}}{name}"


def relationship_map(xml: bytes) -> dict[str, str]:
    root = ET.fromstring(xml)
    return {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in root.findall("pr:Relationship", NS)
    }


def dimensions(element: ET.Element) -> tuple[float | None, float | None]:
    shape = element.find(".//v:shape", NS)
    if shape is not None:
        style = shape.attrib.get("style", "")
        width = re.search(r"(?:^|;)width:([0-9.]+)pt", style)
        height = re.search(r"(?:^|;)height:([0-9.]+)pt", style)
        if width and height:
            return float(width.group(1)), float(height.group(1))

    extent = element.find(".//wp:extent", NS)
    if extent is not None:
        return (
            round(int(extent.attrib["cx"]) / 12700, 2),
            round(int(extent.attrib["cy"]) / 12700, 2),
        )
    return None, None


def image_part(element: ET.Element, relationships: dict[str, str]) -> dict | None:
    image = element.find(".//v:imagedata", NS)
    rel_id = image.attrib.get(qname("r", "id")) if image is not None else None
    if rel_id is None:
        image = element.find(".//a:blip", NS)
        rel_id = image.attrib.get(qname("r", "embed")) if image is not None else None
    if not rel_id or rel_id not in relationships:
        return None

    width, height = dimensions(element)
    target = str(PurePosixPath("word") / relationships[rel_id])
    return {
        "type": "image",
        "relationship": rel_id,
        "target": target,
        "name": PurePosixPath(target).name,
        "width_pt": width,
        "height_pt": height,
        "ole": element.find(".//o:OLEObject", NS) is not None,
    }


def paragraph_parts(paragraph: ET.Element, relationships: dict[str, str]) -> list[dict]:
    parts: list[dict] = []
    seen_images: set[str] = set()
    parents = {child: parent for parent in paragraph.iter() for child in parent}

    def formatted_text(node: ET.Element) -> str:
        text = node.text or ""
        current = parents.get(node)
        while current is not None and current.tag != qname("w", "r"):
            current = parents.get(current)
        if current is None:
            return text
        vertical = current.find("w:rPr/w:vertAlign", NS)
        value = vertical.attrib.get(qname("w", "val")) if vertical is not None else None
        if value == "superscript":
            return f"^{{{text}}}"
        if value == "subscript":
            return f"_{{{text}}}"
        return text

    for node in paragraph.iter():
        if node.tag == qname("w", "t") and node.text:
            parts.append({"type": "text", "text": formatted_text(node)})
        elif node.tag in {qname("w", "tab"), qname("w", "br"), qname("w", "cr")}:
            parts.append({"type": "text", "text": "\t" if node.tag == qname("w", "tab") else "\n"})
        elif node.tag in {qname("w", "object"), qname("w", "pict"), qname("w", "drawing")}:
            part = image_part(node, relationships)
            if part and part["relationship"] not in seen_images:
                parts.append(part)
                seen_images.add(part["relationship"])

    merged: list[dict] = []
    for part in parts:
        if part["type"] == "text" and merged and merged[-1]["type"] == "text":
            merged[-1]["text"] += part["text"]
        else:
            merged.append(part)
    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--assets", type=Path)
    args = parser.parse_args()

    with zipfile.ZipFile(args.input) as archive:
        relationships = relationship_map(archive.read("word/_rels/document.xml.rels"))
        document = ET.fromstring(archive.read("word/document.xml"))
        paragraphs = []
        for index, paragraph in enumerate(document.findall(".//w:body/w:p", NS)):
            parts = paragraph_parts(paragraph, relationships)
            if parts:
                paragraphs.append({"index": index, "parts": parts})

        if args.assets:
            args.assets.mkdir(parents=True, exist_ok=True)
            targets = {
                part["target"]
                for paragraph in paragraphs
                for part in paragraph["parts"]
                if part["type"] == "image"
            }
            for target in targets:
                destination = args.assets / PurePosixPath(target).name
                destination.write_bytes(archive.read(target))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"source": str(args.input), "paragraphs": paragraphs}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
