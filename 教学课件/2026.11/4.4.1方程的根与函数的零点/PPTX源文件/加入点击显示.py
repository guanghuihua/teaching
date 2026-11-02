"""Add native PowerPoint click-to-appear effects to named editable objects.

The slide timing container follows the real native animation tree in the
user-supplied source PPTX, slides 5 and 20. This module changes only p:timing.
It does not convert slide content into images or alter shape/equation markup.

CLI: python inject_appear.py input.pptx output.pptx reveal_spec.json
Spec: {"slides": {"2": [["answer-line-1", "answer-formula-1"], ["answer-2"]]}}
Selectors are exact p:cNvPr names, integer shape ids, or strings "id:123".
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any
from zipfile import ZipFile

from lxml import etree as ET

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"p": P, "a": A}


def ptag(local: str) -> str:
    return f"{{{P}}}{local}"


def child(parent: ET._Element, local: str, **attrs: Any) -> ET._Element:
    return ET.SubElement(parent, ptag(local), {k: str(v) for k, v in attrs.items()})


def condition(parent: ET._Element, delay: str = "0") -> None:
    child(child(parent, "stCondLst"), "cond", delay=delay)


class IdSequence:
    def __init__(self):
        self.value = 0

    def take(self) -> str:
        self.value += 1
        return str(self.value)


def build_timing(groups: list[list[str]], text_ids: set[str] | None = None) -> ET._Element:
    """Each group is revealed by the next click, its members simultaneously."""
    ids = IdSequence()
    timing = ET.Element(ptag("timing"))
    root = child(child(child(timing, "tnLst"), "par"), "cTn",
                 id=ids.take(), dur="indefinite", restart="never", nodeType="tmRoot")
    sequence = child(child(root, "childTnLst"), "seq", concurrent="1", nextAc="seek")
    main = child(sequence, "cTn", id=ids.take(), dur="indefinite", nodeType="mainSeq")
    steps = child(main, "childTnLst")

    for group in groups:
        click = child(child(steps, "par"), "cTn", id=ids.take(), fill="hold")
        condition(click, "indefinite")
        sync = child(child(child(click, "childTnLst"), "par"), "cTn",
                     id=ids.take(), fill="hold")
        condition(sync)
        effects = child(sync, "childTnLst")
        for index, spid in enumerate(group):
            effect = child(child(effects, "par"), "cTn", id=ids.take(),
                           presetID="1", presetClass="entr", presetSubtype="0",
                           fill="hold", grpId="0",
                           nodeType="clickEffect" if index == 0 else "withEffect")
            condition(effect)
            set_node = child(child(effect, "childTnLst"), "set")
            behavior = child(set_node, "cBhvr")
            behavior_time = child(behavior, "cTn", id=ids.take(), dur="1", fill="hold")
            condition(behavior_time)
            child(child(behavior, "tgtEl"), "spTgt", spid=spid)
            child(child(behavior, "attrNameLst"), "attrName").text = "style.visibility"
            child(child(set_node, "to"), "strVal", val="visible")

    for local, evt in [("prevCondLst", "onPrev"), ("nextCondLst", "onNext")]:
        cond = child(child(sequence, local), "cond", evt=evt, delay="0")
        child(child(cond, "tgtEl"), "sldTgt")
    # Native text boxes use an all-at-once text build, matching PowerPoint's
    # saved structure. No paragraph splitting: the complete object appears.
    if text_ids:
        builds = child(timing, "bldLst")
        for spid in [s for g in groups for s in g if s in text_ids]:
            child(builds, "bldP", spid=spid, grpId="0")
    return timing


def resolve_groups(root: ET._Element, steps: list[list[Any]]) -> list[list[str]]:
    by_id: dict[str, list[ET._Element]] = defaultdict(list)
    by_name: dict[str, list[ET._Element]] = defaultdict(list)
    for nv in root.xpath(".//p:cNvPr", namespaces=NS):
        by_id[nv.get("id", "")].append(nv)
        by_name[nv.get("name", "")].append(nv)
    result: list[list[str]] = []
    used: set[str] = set()
    for step in steps:
        if not isinstance(step, list) or not step:
            raise ValueError("Every reveal step must be a non-empty array of selectors")
        targets = []
        for selector in step:
            if isinstance(selector, int) or (isinstance(selector, str) and selector.startswith("id:")):
                key = str(selector) if isinstance(selector, int) else selector[3:]
                matches = by_id[key]
            elif isinstance(selector, str):
                matches = by_name[selector]
            else:
                raise ValueError(f"Invalid shape selector: {selector!r}")
            if len(matches) != 1:
                raise ValueError(f"Shape selector {selector!r} resolved to {len(matches)} objects")
            shape_id = matches[0].get("id")
            if shape_id in used:
                raise ValueError(f"Shape id {shape_id} occurs in more than one reveal step")
            # Id 1 normally belongs to the slide's non-drawing root group.
            owner = matches[0].getparent().getparent()
            if owner.tag not in {ptag("sp"), ptag("pic"), ptag("grpSp"), ptag("graphicFrame"), ptag("cxnSp")}:
                raise ValueError(f"Selector {selector!r} does not identify an animatable object")
            used.add(shape_id)
            targets.append(shape_id)
        result.append(targets)
    return result


def validate_timing(root: ET._Element) -> dict[str, int]:
    timing = root.find(ptag("timing"))
    if timing is None:
        return {"clicks": 0, "objects": 0}
    time_ids = timing.xpath(".//p:cTn/@id", namespaces=NS)
    if len(time_ids) != len(set(time_ids)):
        raise ValueError("Animation time node ids are not unique")
    available = set(root.xpath(".//p:cNvPr/@id", namespaces=NS))
    targets = timing.xpath(".//p:spTgt/@spid", namespaces=NS)
    if set(targets) - available:
        raise ValueError(f"Missing animation targets: {set(targets) - available}")
    return {
        "clicks": len(timing.xpath(".//p:cTn[@nodeType='clickEffect']", namespaces=NS)),
        "objects": len(targets),
    }


def inject_appear(input_path: str | Path, output_path: str | Path,
                  spec: dict[str, Any]) -> dict[str, Any]:
    source = Path(input_path).resolve()
    dest = Path(output_path).resolve()
    if source == dest:
        raise ValueError("Use a new output path; the source PPTX is preserved")
    slides = spec.get("slides", spec)
    changes: dict[str, bytes] = {}
    report: dict[str, Any] = {}
    parser = ET.XMLParser(remove_blank_text=False, resolve_entities=False)
    with ZipFile(source) as zin:
        for index, steps in slides.items():
            member = f"ppt/slides/slide{int(index)}.xml"
            root = ET.fromstring(zin.read(member), parser)
            groups = resolve_groups(root, steps)
            old = root.find(ptag("timing"))
            if old is not None:
                root.remove(old)
            if groups:
                text_ids = set()
                for shape in root.xpath(".//p:sp[p:txBody]", namespaces=NS):
                    shape_nv = shape.find("p:nvSpPr/p:cNvPr", NS)
                    if shape_nv is not None:
                        text_ids.add(shape_nv.get("id"))
                timing = build_timing(groups, text_ids)
                # p:sld child sequence: cSld, clrMapOvr?, transition?, timing?, extLst?
                ext = root.find(ptag("extLst"))
                if ext is None:
                    root.append(timing)
                else:
                    root.insert(root.index(ext), timing)
            report[str(index)] = validate_timing(root)
            changes[member] = ET.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(dest, "w") as zout:
            for entry in zin.infolist():
                zout.writestr(entry, changes.get(entry.filename, zin.read(entry.filename)))
    with ZipFile(dest) as final:
        if final.testzip() is not None:
            raise ValueError("Output PPTX failed ZIP CRC check")
        for member in changes:
            validate_timing(ET.fromstring(final.read(member), parser))
    return {"output": str(dest), "slides": report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("spec")
    args = parser.parse_args()
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8-sig"))
    result = inject_appear(args.input, args.output, spec)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
