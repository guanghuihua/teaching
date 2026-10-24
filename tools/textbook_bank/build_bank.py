"""Build a source-image question bank from the supplied Xiangjiao first volume.

OCR is a retrieval draft, never the canonical mathematical statement. Work files
are read from --work; published crops, JSON, Markdown and offline HTML go to --out.
The source PDF is read only. Coordinates refer to pages rendered at scale 2.1.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path

from PIL import Image

SECTIONS = [
    (2, "1.1", "集合"), (14, "1.2", "常用逻辑用语"),
    (32, "2.1", "相等关系与不等关系"), (45, "2.2", "从函数观点看一元二次方程"),
    (50, "2.3", "一元二次不等式"), (65, "3.1", "函数"),
    (79, "3.2", "函数的基本性质"), (94, "4.1", "实数指数幂和幂函数"),
    (106, "4.2", "指数函数"), (115, "4.3", "对数函数"),
    (130, "4.4", "函数与方程"), (139, "4.5", "函数模型及其应用"),
    (156, "5.1", "任意角和弧度制"), (163, "5.2", "任意角的三角函数"),
    (177, "5.3", "三角函数的图象与性质"), (188, "5.4", "函数 y=A sin(ωx+φ) 的图象与性质"),
    (199, "5.5", "三角函数模型的简单应用"), (211, "6.1", "获取数据的途径与统计的一些基本概念"),
    (215, "6.2", "抽样"), (224, "6.3", "统计图表"), (235, "6.4", "用样本估计总体"),
]
CHAPTERS = {
    1: "集合与逻辑", 2: "一元二次函数、方程和不等式", 3: "函数的概念与性质",
    4: "幂函数、指数函数和对数函数", 5: "三角函数", 6: "统计学初步",
}
CHAPTER_START = [(1, 1), (31, 2), (64, 3), (93, 4), (155, 5), (210, 6)]
GROUPS = [
    ("1.1", 19, 20, 17), ("1.2", 30, 31, 10), ("复习题一", 36, 37, 19),
    ("2.1", 50, 51, 12), ("2.2", 56, 56, 7), ("2.3", 65, 66, 12), ("复习题二", 68, 70, 17),
    ("3.1", 83, 85, 16), ("3.2", 92, 93, 13), ("复习题三", 97, 99, 20),
    ("4.1", 111, 112, 13), ("4.2", 120, 121, 15), ("4.3", 131, 133, 19),
    ("4.4", 143, 143, 7), ("4.5", 154, 156, 8), ("复习题四", 158, 161, 25),
    ("5.1", 168, 169, 13), ("5.2", 182, 183, 15), ("5.3", 193, 194, 14),
    ("5.4", 203, 204, 8), ("5.5", 208, 209, 5), ("复习题五", 213, 216, 24),
    ("6.1", 221, 221, 5), ("6.2", 228, 229, 8), ("6.3", 238, 240, 8),
    ("6.4", 261, 264, 14), ("复习题六", 271, 276, 17),
]
# These labels were missed by OCR. Each was read against the original page.
LABEL_FIXES = [(93, 1046, 11, "3.2"), (276, 465, 17, "复习题六")]
PRACTICE_FIXES = {128: [(230, 1)], 234: [(229, 1)], 248: [(659, 1)]}
SUMMARY_GROUPS = [(35, 35, 6), (67, 67, 5), (96, 96, 5), (157, 157, 7), (212, 212, 6), (269, 270, 5)]
EXPERIMENTS = [(80, 80, "用计算机作函数图象和列函数表"), (144, 145, "用二分法求方程的近似解"),
               (205, 205, "用计算机作三角函数图象"), (241, 241, "利用计算机制作统计图表")]


def clean(text: str) -> str:
    return re.sub(r"\s+", "", text)


def parse_number(text: str) -> int | None:
    text = text.replace("巧", "15").replace("I", "1").replace("l", "1")
    if re.match(r"^\d+[．.]\d+[%％]", text):
        return None
    m = re.match(r"^(\d{1,2})(?:[．·。]|[.](?!\d))", text)
    return int(m[1]) if m else None


def section_at(page: int) -> tuple[int, str, str]:
    printed = page - 7
    chapter = max(c for start, c in CHAPTER_START if start <= printed)
    starts = [(p, s, title) for p, s, title in SECTIONS if p <= printed and int(s[0]) == chapter]
    if not starts:
        return chapter, "", CHAPTERS[chapter]
    _, sec, title = starts[-1]
    return chapter, sec, title


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    work, out = args.work, args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "题目原图").mkdir(exist_ok=True)
    (out / "原页上下文").mkdir(exist_ok=True)
    (out / "分章题库").mkdir(exist_ok=True)
    pages = {p["page"]: p for p in json.loads((work / "markers.json").read_text(encoding="utf-8"))}
    geometry = {p["page"]: p for p in json.loads((work / "pdf_geometry.json").read_text(encoding="utf-8"))}
    labels = json.loads((work / "label_inventory.json").read_text(encoding="utf-8"))
    label_numbers = {p["hash"]: p["index"] - 1 for p in labels if 2 <= p["index"] <= 13}
    label_numbers.update({p["hash"]: 13 for p in labels if p["index"] == 27})
    thought_hash = labels[0]["hash"]
    records: list[dict] = []
    reports: list[dict] = []
    events: list[tuple[int, int]] = []
    examples: list[tuple[int, int, int]] = []
    thoughts: list[tuple[int, int]] = []
    for page, geo in geometry.items():
        if not 8 <= page <= 276:
            continue
        for im in geo["images"]:
            y = round(im["top"] * 2.1)
            if im.get("hash") in label_numbers:
                examples.append((page, y, label_numbers[im["hash"]]))
            if im.get("hash") == thought_hash:
                thoughts.append((page, y))
    examples = sorted(set(examples))
    thoughts = sorted(set(thoughts))
    for page in pages.values():
        for line in page["lines"]:
            if line["x"] <= 250 and re.match(r"^案例[123]", line["text"]):
                events.append((page["page"], round(line["y"])))
    for p, y, _ in examples:
        events.append((p, y))
    events.extend(thoughts)
    for p in pages.values():
        events.extend((p["page"], int(a)) for a, _ in p["bands"])
    events = sorted(set(events))

    def make_parts(start: tuple[int, int], stop: tuple[int, int]) -> list[dict]:
        result = []
        for p in range(start[0], stop[0] + 1):
            top = start[1] if p == start[0] else 176
            bottom = stop[1] if p == stop[0] else 1645
            if bottom - top < 18:
                continue
            result.append({"pdf_page": p, "printed_page": p - 7,
                           "box": [140, max(150, top), 1160, min(1650, bottom)]})
        return result

    def draft_for(parts: list[dict]) -> str:
        result = []
        for part in parts:
            lines = [l for l in pages[part["pdf_page"]]["lines"]
                     if part["box"][1] <= l["y"] < part["box"][3] and 135 <= l["x"] < 1165]
            result.append(f"[教材p.{part['printed_page']} / PDF第{part['pdf_page']}页]\n" +
                          "\n".join(l["text"] for l in sorted(lines, key=lambda l: (round(l["y"] / 12), l["x"]))))
        return "\n\n".join(result)

    def add(kind: str, group: str, number: int | None, start, stop, method: str,
            title: str | None = None, source_solution: bool = False) -> dict:
        chapter, section, sec_title = section_at(start[0])
        if group.startswith("复习题"):
            section, sec_title = "章末复习", group
        if kind == "小结与复习":
            section, sec_title = "小结与复习", "小结与复习"
        code = {"例题": "EX", "练习": "PR", "习题": "HW", "复习题": "RV", "思考": "TH",
                "小结与复习": "SU", "案例": "CA", "数学实验": "LAB"}[kind]
        ident = f"XJ-B1-C{chapter:02}-{code}-P{start[0]-7:03}-Y{start[1]:04}"
        parts = make_parts(start, stop)
        assert parts, (ident, start, stop)
        draft = draft_for(parts)
        original = f"第{number}题" if number is not None else "未编号题组"
        if kind in ("例题", "案例"):
            original = f"{kind}{number}"
        if kind == "数学实验":
            original = "完整实验任务"
        r = {"id": ident, "type": kind, "chapter": chapter, "chapter_title": CHAPTERS[chapter],
             "section": section, "section_title": sec_title, "group": group,
             "original_number": number, "original_label": original,
             "title": title or f"{group} {original}", "printed_pages": sorted({z["printed_page"] for z in parts}),
             "pdf_pages": sorted({z["pdf_page"] for z in parts}), "parts": parts,
             "source_solution_included": source_solution, "locator_method": method,
             "ocr_draft": draft, "ocr_status": "未校对，仅供检索", "answer_status": "未录入独立答案",
             "midterm_scope": start[0] - 7 <= 114,
             "context_note": "配图、共用图表及前后题引用请同时核对原页上下文。"}
        records.append(r)
        return r

    def anchors_in(page: int, top: int, bottom: int, practice=False):
        expected_x = (234 if page % 2 else 216) + (12 if practice else 0)
        vals = []
        for line in pages[page]["lines"]:
            number = parse_number(line["text"])
            if number is not None and top < line["y"] < bottom and abs(line["x"] - expected_x) < (9 if practice else 22):
                vals.append({"page": page, "y": round(line["y"]), "number": number, "method": "OCR题号及连续序列核对"})
        return sorted(vals, key=lambda x: x["y"])

    def add_group(kind: str, label: str, anchors: list[dict], last_page: int, last_y: int):
        anchors.sort(key=lambda a: (a["page"], a["y"]))
        seq = [a["number"] for a in anchors]
        assert seq == list(range(1, len(seq) + 1)), (kind, label, seq)
        for i, a in enumerate(anchors):
            b = anchors[i+1] if i+1 < len(anchors) else {"page": last_page, "y": last_y + 12}
            stop = (b["page"], b["y"] - 12)
            # Remove the chapter book's tier headings from the end of a card.
            tier = [l for l in pages[a["page"]]["heads"]
                    if any(t in l["text"] for t in ["温故而知新", "上下而求索", "学而时习之"])
                    and a["y"] < l["y"] < (stop[1] if stop[0] == a["page"] else 1645)]
            if tier and stop[0] == a["page"]:
                stop = (stop[0], round(tier[0]["y"]) - 15)
            add(kind, label, a["number"], (a["page"], a["y"] - 12), stop, a["method"])

    for label, start, end, expected_count in GROUPS:
        anchors = []
        for p in range(start, end + 1):
            heads = [l for l in pages[p]["heads"] if "习题" in l["text"] and l["y"] < 1200]
            top = round(heads[0]["y"]) + 40 if p == start and heads else 175
            anchors.extend(anchors_in(p, top, 1645))
        for p, y, num, grp in LABEL_FIXES:
            if grp == label:
                anchors.append({"page": p, "y": y, "number": num, "method": "原页图像人工核对补齐题号"})
        assert len(anchors) == expected_count, (label, len(anchors), expected_count)
        add_group("复习题" if label.startswith("复习题") else "习题",
                  label if label.startswith("复习题") else f"习题{label}", anchors, end, 1320 if label == "4.4" else 1645)
        reports.append({"group": label, "expected": expected_count, "found": len(anchors), "sequence": "连续"})

    for p in pages.values():
        for band_index, (top, bottom) in enumerate(p["bands"], 1):
            n = p["page"]
            anchors = anchors_in(n, top, bottom, practice=True)
            for y, num in PRACTICE_FIXES.get(n, []):
                if top < y < bottom:
                    anchors.append({"page": n, "y": y, "number": num, "method": "原页图像人工核对补齐题号"})
            anchors.sort(key=lambda a: a["y"])
            label = f"p.{n-7} 练习" + (f"第{band_index}组" if len(p["bands"]) > 1 else "")
            if not anchors:
                add("练习", label, None, (n, top), (n, bottom), "练习框图像定位；原题组未编号")
            else:
                add_group("练习", label, anchors, n, bottom)
            reports.append({"group": label, "found": len(anchors) or 1,
                            "sequence": "连续" if anchors else "原文未编号，整组保留"})

    for start, end, count in SUMMARY_GROUPS:
        anchors = []
        for p in range(start, end + 1):
            anchors.extend(anchors_in(p, 175, 1645))
        assert len(anchors) == count, ("小结", start, [a["number"] for a in anchors])
        add_group("小结与复习", f"第{section_at(start)[0]}章 小结与复习", anchors, end, 1645)

    # Examples keep their textbook solution together. This avoids deleting a
    # condition or diagram by guessing where an OCR-damaged solution begins.
    for p, y, number in examples:
        chapter, section, _ = section_at(p)
        candidates = [e for e in events if e > (p, y+8) and e[0] <= p+2]
        stop = candidates[0] if candidates else (p, 1645)
        # Never run past the end of the same subsection's pages.
        stop = min(stop, (p+2, 1645))
        r = add("例题", f"{section} 例题", number, (p, y-8), (stop[0], stop[1]-12),
                "教材例题标签图像精确匹配", source_solution=True)
        r["context_note"] = "保留教材例题及原解、紧邻说明；可展开完整原页核对。"

    for p, y in thoughts:
        later = [e for e in events if e > (p, y+8) and e[0] <= p+1]
        stop = later[0] if later else (p, 1645)
        add("思考", f"{section_at(p)[1]} 思考", None, (p, y-8), (stop[0], stop[1]-12),
            "教材思考标签图像精确匹配", title=f"p.{p-7} 思考（含紧邻说明）", source_solution=True)

    for p in pages.values():
        for l in p["lines"]:
            m = re.match(r"^案例([123])", l["text"])
            if not m or l["x"] > 250:
                continue
            start = (p["page"], round(l["y"]) - 8)
            later = [e for e in events if e > (start[0], start[1]+16) and e[0] <= start[0]+3]
            stop = later[0] if later else (start[0], 1645)
            # The two introductory inequality cases share one page.
            if start[0] == 40 and int(m[1]) == 1:
                stop = (40, 947)
            add("案例", f"{section_at(start[0])[1]} 案例", int(m[1]), start, stop,
                "案例标题与原页坐标定位", source_solution=True)

    for start, end, title in EXPERIMENTS:
        add("数学实验", "数学实验", None, (start, 145), (end, 1645), "目录及完整实验页范围核对", title=title,
            source_solution=True)

    records.sort(key=lambda r: (r["pdf_pages"][0], r["parts"][0]["box"][1], r["id"]))
    assert len({r["id"] for r in records}) == len(records)
    for r in records:
        for i, part in enumerate(r["parts"], 1):
            image = Image.open(work / f"pages/{part['pdf_page']:03}.png")
            box = part["box"]
            assert 0 <= box[0] < box[2] <= image.width and 0 <= box[1] < box[3] <= image.height
            target = f"题目原图/{r['id']}-{i:02}.webp"
            image.crop(box).convert("RGB").save(out / target, "WEBP", lossless=True, method=4)
            part["image"] = target
    # Remove only stale generated crops from this exact output directory.
    referenced = {part["image"] for r in records for part in r["parts"]}
    crop_root = (out / "题目原图").resolve()
    for file in crop_root.glob("XJ-B1-*.webp"):
        assert file.resolve().parent == crop_root
        if file.relative_to(out.resolve()).as_posix() not in referenced:
            file.unlink()
    used_pages = sorted({p for r in records for p in r["pdf_pages"]})
    for p in used_pages:
        image = Image.open(work / f"pages/{p:03}.png").convert("RGB")
        image.save(out / f"原页上下文/PDF{p:03}-教材p{p-7:03}.webp", "WEBP", lossless=True, method=4)
    for r in records:
        r["context_images"] = [f"原页上下文/PDF{p:03}-教材p{p-7:03}.webp" for p in r["pdf_pages"]]
    source_hash = hashlib.sha256(args.source.read_bytes()).hexdigest()
    stats = {"total": len(records), "by_type": dict(Counter(r["type"] for r in records)),
             "by_chapter": {str(c): sum(r["chapter"] == c for r in records) for c in CHAPTERS},
             "midterm": sum(r["midterm_scope"] for r in records), "source_pages_with_items": len(used_pages),
             "cross_page_records": sum(len(r["pdf_pages"]) > 1 for r in records)}
    payload = {"book": "湘教版普通高中教科书数学必修第一册", "source_sha256": source_hash,
               "source_pdf_pages": 281, "printed_to_pdf_offset": 7, "statistics": stats,
               "policy": "原图为准；OCR未校对；小问不拆分；例题保留教材原解；未创建独立答案", "items": records}
    (out / "题库数据.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "题库数据.js").write_text("window.TEXTBOOK_BANK = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
    (out / "提取核查记录.json").write_text(json.dumps({"statistics": stats, "groups": reports,
        "manual_label_fixes": LABEL_FIXES, "manual_practice_label_fixes": PRACTICE_FIXES,
        "mathematical_transcription_reviewed": False}, ensure_ascii=False, indent=2), encoding="utf-8")

    for c, title in CHAPTERS.items():
        lines = [f"# 第{c}章 {title} 教材题库", "", "原图保留题目、公式和图形。OCR文字仅供检索，未经人工逐字校对。例题及思考保留教材原解或紧邻说明。", ""]
        for r in records:
            if r["chapter"] != c:
                continue
            ps = "、".join(map(str, r["printed_pages"]))
            pdf = "、".join(map(str, r["pdf_pages"]))
            lines += [f"## {r['id']} {r['title']}", "", f"教材位置：第{c}章 / {r['section']} {r['section_title']} / 印刷页 p.{ps} / PDF 第{pdf}页。", "",
                      f"类型：{r['type']}；原题号：{r['original_label']}。", ""]
            for part in r["parts"]:
                lines.append(f"![教材原图 p.{part['printed_page']}](../{part['image']})")
            lines += ["", "原页上下文：" + "；".join(f"[PDF第{p}页](../{im})" for p, im in zip(r["pdf_pages"], r["context_images"])), ""]
        (out / "分章题库" / f"第{c}章_{title.replace('、','_')}.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
