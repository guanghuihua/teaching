"""Local PPTX -> campus Beamer converter. No Office automation or AI service.

The inspection manifest is evidence, not an instruction stream. Reviewed layout
overrides are separate, explicitly supplied local JSON containing trusted TeX.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import posixpath
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
}
REPO = Path(__file__).resolve().parents[2]
DEFAULT_THEME = REPO / "教学课件/高中园Beamer模板"
EFFECT_NAMES = {"1": "出现", "2": "飞入", "3": "百叶窗", "4": "盒状", "12": "缓慢进入"}


def find(el, path):
    return el.find(path, NS) if el is not None else None


def all_(el, path):
    return el.findall(path, NS) if el is not None else []


def local(tag):
    return tag.rsplit("}", 1)[-1]


def text_of(el):
    return "".join(x.text or "" for x in el.iter() if x.tag in (f"{{{NS['a']}}}t", f"{{{NS['m']}}}t"))


def alternatives(el):
    """Select a Choice once; never duplicate Choice and Fallback text."""
    el = copy.deepcopy(el)
    for parent in list(el.iter()):
        for child in list(parent):
            if local(child.tag) == "AlternateContent":
                chosen = find(child, "mc:Choice")
                if chosen is None:
                    chosen = find(child, "mc:Fallback")
                at = list(parent).index(child)
                parent.remove(child)
                if chosen is not None:
                    for k, item in enumerate(chosen):
                        parent.insert(at + k, item)
    return el


def relationships(z, part):
    relpart = posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")
    if relpart not in z.namelist():
        return {}
    return {
        r.get("Id"): posixpath.normpath(posixpath.join(posixpath.dirname(part), r.get("Target")))
        for r in ET.fromstring(z.read(relpart))
        if r.get("TargetMode") != "External"
    }


def escape_tex(s):
    symbols = {"∈": r"\ensuremath{\in}", "∉": r"\ensuremath{\notin}",
               "∅": r"\ensuremath{\varnothing}", "∞": r"\ensuremath{\infty}",
               "≤": r"\ensuremath{\le}", "≥": r"\ensuremath{\ge}",
               "π": r"\ensuremath{\pi}", "²": r"\ensuremath{^2}",
               "＝": "=", "\u00a0": "~"}
    special = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}",
               "%": r"\%", "$": r"\$", "&": r"\&", "#": r"\#",
               "_": r"\_", "^": r"\textasciicircum{}", "~": r"\textasciitilde{}"}
    return "".join(symbols.get(c, special.get(c, c)) for c in s)


def timing(root):
    """Translate main-sequence click boundaries, preserving target shape IDs."""
    events, issues = [], []
    step = 1
    if any(t.get("nodeType") == "interactiveSeq" for t in all_(root, ".//p:cTn")):
        issues.append("存在交互触发器：不能自动转换为线性点击顺序。")
    if all_(root, ".//p:animMotion"):
        issues.append("存在路径动画，自动稿只保留静态位置，需人工处理。")
    for effect in all_(root, ".//p:cTn"):
        cls = effect.get("presetClass")
        if not cls:
            continue
        trigger = effect.get("nodeType", "unknown")
        if trigger == "clickEffect":
            step += 1
        elif trigger in ("withEffect", "afterEffect"):
            issues.append(f"{trigger} 的延迟/连续运动归并到同一点击状态。")
        else:
            issues.append(f"未知动画触发类型 {trigger}，需要人工确定点击分组。")
        targets = sorted(set(t.get("spid") for t in all_(effect, ".//p:spTgt")))
        if not targets:
            issues.append("动画没有可识别的形状目标。")
        if all_(effect, ".//p:txEl") or all_(effect, ".//p:subSp"):
            issues.append("含段落/子对象动画：自动稿按整个目标对象处理，需在生成的 TeX 中人工拆分并设置可见步数。")
        if cls not in ("entr", "exit"):
            issues.append(f"{cls} 动画不改变自动稿可见性，需要人工处理。")
        events.append({"step": step, "class": cls, "trigger": trigger,
                       "preset": effect.get("presetID"), "subtype": effect.get("presetSubtype"),
                       "targets": targets,
                       "filters": [e.get("filter") for e in all_(effect, ".//p:animEffect")],
                       "durations_ms": sorted(set(e.get("dur") for e in all_(effect, ".//p:cTn") if e.get("dur")))})
    return events, step, issues


def visible_steps(ids, events, count):
    """Both a group and an animated child must be visible for the child to show."""
    result = set(range(1, count + 1))
    for ident in ids:
        mine = [e for e in events if ident in e["targets"] and e["class"] in ("entr", "exit")]
        visible = not mine or mine[0]["class"] != "entr"
        selected = set()
        for step in range(1, count + 1):
            for e in mine:
                if e["step"] == step:
                    visible = e["class"] == "entr"
            if visible:
                selected.add(step)
        result &= selected
    return sorted(result)


def overlay_spec(steps):
    if not steps:
        return "0"
    ranges, start, last = [], steps[0], steps[0]
    for n in steps[1:]:
        if n == last + 1:
            last = n
        else:
            ranges.append(str(start) if start == last else f"{start}-{last}")
            start = last = n
    ranges.append(str(start) if start == last else f"{start}-{last}")
    return ",".join(ranges)


def bounds(shape, scale, transform=(1, 1, 0, 0)):
    xf = find(shape, "p:spPr/a:xfrm")
    if xf is None:
        xf = find(shape, "p:xfrm")
    if xf is None:
        xf = find(shape, "p:grpSpPr/a:xfrm")
    if xf is None:
        return [0, 0, 0, 0]
    off, ext = find(xf, "a:off"), find(xf, "a:ext")
    if off is None or ext is None:
        return [0, 0, 0, 0]
    sx, sy, tx, ty = transform
    return [(float(off.get("x")) * sx + tx) * scale[0],
            (float(off.get("y")) * sy + ty) * scale[1],
            float(ext.get("cx")) * sx * scale[0], float(ext.get("cy")) * sy * scale[1]]


def inspect_pptx(source):
    slides = []
    with zipfile.ZipFile(source) as z:
        presentation = ET.fromstring(z.read("ppt/presentation.xml"))
        sz = find(presentation, "p:sldSz")
        scale = (1280 / int(sz.get("cx")), 720 / int(sz.get("cy")))
        rels = relationships(z, "ppt/presentation.xml")
        for number, ref in enumerate(all_(presentation, "p:sldIdLst/p:sldId"), 1):
            part = rels[ref.get(f"{{{NS['r']}}}id")]
            raw = ET.fromstring(z.read(part))
            root = alternatives(raw)
            sr = relationships(z, part)
            events, count, issues = timing(root)
            objects = []

            def walk(tree, ancestors=(), trans=(1, 1, 0, 0)):
                for shape in tree:
                    kind = local(shape.tag)
                    if kind not in ("sp", "pic", "grpSp", "graphicFrame", "cxnSp"):
                        continue
                    ident = find(shape, ".//p:cNvPr")
                    sid = ident.get("id")
                    box = bounds(shape, scale, trans)
                    if kind == "grpSp":
                        xf = find(shape, "p:grpSpPr/a:xfrm")
                        off, ext = find(xf, "a:off"), find(xf, "a:ext")
                        co, ce = find(xf, "a:chOff"), find(xf, "a:chExt")
                        nt = trans
                        if all(v is not None for v in (off, ext, co, ce)):
                            sx, sy, tx, ty = trans
                            gx = float(ext.get("cx")) / max(1, float(ce.get("cx")))
                            gy = float(ext.get("cy")) / max(1, float(ce.get("cy")))
                            nt = (sx * gx, sy * gy, tx + sx * (float(off.get("x")) - gx * float(co.get("x"))),
                                  ty + sy * (float(off.get("y")) - gy * float(co.get("y"))))
                        walk(shape, ancestors + (sid,), nt)
                        continue
                    textbody = find(shape, "p:txBody")
                    paragraphs = [text_of(p) for p in all_(textbody, "a:p")]
                    text = "\n".join(paragraphs).strip()
                    tex = r"\par ".join(escape_tex(p) for p in paragraphs)
                    if all_(shape, ".//m:oMath"):
                        issues.append(f"对象 {sid} 含 Office 数学公式，自动稿仅转为符号文本，建议审核为原生 LaTeX。")
                    blip = find(shape, "p:blipFill/a:blip")
                    if kind == "graphicFrame":
                        # The OLE preview is only in Fallback; inspect it before Choice selection.
                        original = next((s for s in all_(raw, ".//p:graphicFrame")
                                         if find(s, ".//p:cNvPr").get("id") == sid), shape)
                        blip = find(original, ".//p:oleObj/p:pic/p:blipFill/a:blip")
                        if blip is None:
                            issues.append(f"对象 {sid} 为不支持的图表/表格/SmartArt，自动稿未绘制。")
                    media = sr.get(blip.get(f"{{{NS['r']}}}embed")) if blip is not None else None
                    if blip is not None and media is None:
                        issues.append(f"对象 {sid} 的图片是外链或关系缺失，自动稿未获取图片。")
                    sizes = [float(r.get("sz")) / 100 for r in all_(shape, ".//a:rPr") if r.get("sz")]
                    obj = {"id": sid, "ancestors": list(ancestors), "kind": kind, "name": ident.get("name"),
                           "box": [round(x, 3) for x in box], "text": text, "tex": tex,
                           "font_pt": max(sizes, default=24), "media": media,
                           "visible": visible_steps((*ancestors, sid), events, count)}
                    if media and kind == "graphicFrame":
                        obj["note"] = "OLE 预览图片；嵌入文档不执行。"
                    crop = find(shape, "p:blipFill/a:srcRect")
                    if crop is not None:
                        obj["crop"] = dict(crop.attrib)
                    if not text and not media and kind == "sp":
                        obj["decoration"] = True
                    xf = find(shape, "p:spPr/a:xfrm")
                    if xf is not None and any(xf.get(k) not in (None, "0", "false") for k in ("rot", "flipH", "flipV")):
                        issues.append(f"对象 {sid} 的旋转/镜像未自动复刻。")
                    if not text and not media and kind in ("sp", "cxnSp"):
                        issues.append(f"对象 {sid} 是非文本矢量形状，自动稿未绘制其路径/线框。")
                    objects.append(obj)

            walk(find(root, "p:cSld/p:spTree"))
            candidates = [o for o in objects if o["text"] and o["box"][1] < 85 and len(o["text"]) < 40]
            title = candidates[0] if candidates else None
            if title and any(title["id"] in e["targets"] for e in events):
                issues.append("原页标题含动画；自动稿改为常驻主题页眉，需审核其出现时机。")
            source_ids = {o["id"] for o in objects} | {a for o in objects for a in o["ancestors"]}
            for event in events:
                for sid in event["targets"]:
                    if sid not in source_ids:
                        issues.append(f"动画目标 {sid} 未找到，不能保证对应内容可见性。")
            slides.append({"number": number, "part": part, "hidden": raw.get("show") == "0",
                           "title": title["text"] if title else f"第 {number} 页",
                           "title_id": title["id"] if title else None,
                           "steps": count, "events": events, "objects": objects,
                           "issues": sorted(set(issues))})
    return {"schema": 1, "source_name": source.name, "source_size_emu": dict(sz.attrib),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "slide_count": len(slides), "slides": slides}


def extract_media(source, manifest, output):
    media_dir = output / "build" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as z:
        for part in sorted({o["media"] for s in manifest["slides"] for o in s["objects"] if o["media"]}):
            # Archive paths are never used as extraction destinations.
            (media_dir / Path(part).name).write_bytes(z.read(part))
    metafiles = list(media_dir.glob("*.emf")) + list(media_dir.glob("*.wmf"))
    if metafiles:
        shell = shutil.which("powershell") or shutil.which("pwsh")
        if sys.platform != "win32" or not shell:
            raise RuntimeError("EMF/WMF 需要 Windows PowerShell + System.Drawing；请在 Windows 转换一次，生成后 TeX 可跨平台使用。")
        subprocess.run([shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                        str(Path(__file__).with_name("render_metafiles.ps1")), "-Directory", str(media_dir.resolve())], check=True)
    for slide in manifest["slides"]:
        for obj in slide["objects"]:
            if obj["media"]:
                name = Path(obj["media"]).name
                if Path(name).suffix.lower() in (".emf", ".wmf"):
                    name += ".png"
                obj["asset"] = "source-media/" + name


def default_blocks(slide):
    blocks = []
    for obj in slide["objects"]:
        if obj["id"] == slide["title_id"] or not (obj["text"] or obj["media"]):
            continue
        x, y, w, h = obj["box"]
        b = {"ids": [obj["id"]], "x": 40 + x * .93, "y": 112 + max(0, y - 80) * .88,
             "w": w * .93, "h": h * .88, "font": min(16, obj["font_pt"] * .44)}
        if obj["media"]:
            b["asset"] = obj["asset"]
            b["crop"] = obj.get("crop", {})
        else:
            b["tex"] = obj["tex"]
        blocks.append(b)
    return blocks


def resolve_visibility(block, slide):
    ids = block["ids"]
    found = [o for o in slide["objects"] if o["id"] in ids or any(a in ids for a in o["ancestors"])]
    if not found:
        raise ValueError(f"第 {slide['number']} 页配置引用不存在的对象：{ids}")
    states = {tuple(o["visible"]) for o in found}
    if len(states) != 1:
        raise ValueError(f"第 {slide['number']} 页合并了可见时机不同的对象 {ids}；请拆开配置。")
    return list(next(iter(states)))


def render_block(block, slide):
    steps = resolve_visibility(block, slide)
    spec = overlay_spec(steps)
    handout = 1 if slide["steps"] in steps else 0
    x, y, w = block["x"], block["y"], block["w"]
    font = block.get("font", 12)
    if "asset" in block:
        asset = block["asset"]
        if not all(c.isalnum() or c in "/-_." for c in asset) or ".." in Path(asset).parts:
            raise ValueError("图片路径必须是输出目录内的简单相对路径")
        h = block.get("h", 100)
        payload = rf"\includegraphics[width={w*.125:.3f}mm,height={h*.125:.3f}mm]{{{asset}}}"
        crop = block.get("crop", {})
        if crop:
            # Cropping preserves the source rectangle, without stretching the uncropped image.
            l, t, r, b = [float(crop.get(k, 0))/100000 for k in ("l", "t", "r", "b")]
            iw, ih = w / (1-l-r), h / (1-t-b)
            node = (rf"\begin{{scope}}\clip ({x:.3f},{y:.3f}) rectangle ({x+w:.3f},{y+h:.3f});" +
                    rf"\node[anchor=north west,inner sep=0] at ({x-l*iw:.3f},{y-t*ih:.3f}) " +
                    rf"{{\includegraphics[width={iw*.125:.3f}mm,height={ih*.125:.3f}mm]{{{asset}}}}};\end{{scope}}")
        else:
            node = rf"\node[anchor=north west,inner sep=0] at ({x:.3f},{y:.3f}) {{{payload}}};"
    else:
        align = r"\raggedright" if block.get("align") != "center" else r"\centering"
        color = block.get("color", "black")
        node = (rf"\node[anchor=north west,inner sep=0,text={color}] at ({x:.3f},{y:.3f}) {{" +
                rf"\begin{{minipage}}[t]{{{w*.125:.3f}mm}}{align}\fontsize{{{font}}}{{{font*1.5:.2f}}}\selectfont " +
                block["tex"] + r"\end{minipage}};")
    return f"% Source slide {slide['number']}, objects {','.join(block['ids'])}; visible {spec}\n" + rf"\only<{spec}|handout:{handout}>{{{node}}}" + "\n"


def generate(manifest, output, config, theme):
    if config and config.get("source_sha256") != manifest["source_sha256"]:
        raise ValueError("审核配置与源 PPTX 的 SHA-256 不匹配；请重新核对，不能套用到不同版本。")
    for filename in ("beamerthemeGaoZhongYuan.sty", "book-path.tex"):
        shutil.copy2(theme / filename, output / filename)
    shutil.copytree(theme / "assets", output / "assets", dirs_exist_ok=True)
    (output / "slides").mkdir(exist_ok=True)
    reports = []
    for slide in manifest["slides"]:
        c = config.get("slides", {}).get(str(slide["number"]), {})
        blocks = c.get("blocks", default_blocks(slide))
        kind = c.get("kind", "content")
        title = c.get("title", slide["title"])
        if c:
            known = {o["id"] for o in slide["objects"]} | {a for o in slide["objects"] for a in o["ancestors"]}
            covered = {i for b in blocks for i in b["ids"]} | set(c.get("ignore", {}))
            unknown = covered - known
            if unknown:
                raise ValueError(f"第 {slide['number']} 页有未知对象 {unknown}")
            for o in slide["objects"]:
                if (o["text"] or o["media"]) and o["id"] != slide["title_id"]:
                    if not ({o["id"], *o["ancestors"]} & covered):
                        raise ValueError(f"第 {slide['number']} 页遗漏对象 {o['id']}，须配置或说明忽略理由")
        if kind == "cover":
            if slide["events"]:
                raise ValueError("带动画的封面必须按内容页处理，以免丢失点击顺序")
            tex = rf"\title{{{escape_tex(title)}}}\author{{{escape_tex(c.get('subtitle',''))}}}\date{{}}\campusmaketitle" + "\n"
        elif kind == "closing":
            if slide["events"]:
                raise ValueError("带动画的结束页必须按内容页处理")
            tex = rf"\campusclosing[{escape_tex(title)}]" + "\n"
        else:
            tex = rf"\begin{{frame}}<1-{slide['steps']}>[t]{{{escape_tex(title)}}}" + "\n" + r"\begin{campuscanvas}" + "\n"
            for b in blocks:
                if b.get("from_id"):
                    original = next(o for o in slide["objects"] if o["id"] == b["from_id"])
                    b = {**b, "asset": original["asset"], "crop": original.get("crop", {})}
                if b.get("asset"):
                    (output / "source-media").mkdir(exist_ok=True)
                    shutil.copy2(output / "build" / "media" / Path(b["asset"]).name,
                                 output / "source-media" / Path(b["asset"]).name)
                tex += render_block(b, slide)
            tex += r"\end{campuscanvas}" + "\n" + r"\end{frame}" + "\n"
        (output / "slides" / f"slide-{slide['number']:02d}.tex").write_text(tex, encoding="utf-8")
        reports.append({"slide": slide["number"], "title": title, "steps": slide["steps"],
                        "reviewed_layout": bool(c), "source_issues": slide["issues"], "notes": c.get("notes", [])})
    header = r"""% !TeX program = xelatex
% Generated locally. Edit slides/*.tex, or supply a reviewed layout JSON and rebuild.
\ifdefined\HandoutMode
  \documentclass[aspectratio=169,10pt,handout]{beamer}
\else
  \documentclass[aspectratio=169,10pt]{beamer}
\fi
\usepackage[UTF8,fontset=fandol]{ctex}
\IfFontExistsTF{Microsoft YaHei}{\setCJKsansfont{Microsoft YaHei}}{}
\usetheme{GaoZhongYuan}
\newcommand{\red}[1]{\textcolor{red}{#1}}
\setlength{\parskip}{.45em}
\begin{document}
"""
    header += "".join(rf"\input{{slides/slide-{s['number']:02d}.tex}}" + "\n" for s in manifest["slides"] if not s["hidden"])
    (output / "main.tex").write_text(header + "\\end{document}\n", encoding="utf-8")
    (output / "handout.tex").write_text("% !TeX program = xelatex\n\\def\\HandoutMode{1}\n\\input{main.tex}\n", encoding="utf-8")
    (output / ".gitignore").write_text("/build/\n/source-media/*.emf\n/source-media/*.wmf\n", encoding="utf-8")
    (output / "inspection.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "conversion-report.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output / "动画对照表.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["原PPT页", "点击序号", "Beamer步", "目标对象ID", "原效果", "原触发方式", "转换方式"])
        for s in manifest["slides"]:
            for e in s["events"]:
                w.writerow([s["number"], e["step"]-1, e["step"], ",".join(e["targets"]),
                            EFFECT_NAMES.get(e["preset"], e["preset"]), e["trigger"],
                            {"entr": "按步显示", "exit": "按步隐藏"}.get(e["class"], "需复核")])


def compile_tex(output):
    engine = shutil.which("xelatex")
    if not engine:
        raise RuntimeError("未找到 xelatex。已生成 TeX，请安装 TeX Live/MiKTeX 后编译。")
    build = output / "build"
    build.mkdir(exist_ok=True)
    for name in ("main", "handout"):
        for _ in range(2):
            run = subprocess.run([engine, "-interaction=nonstopmode", "-halt-on-error", "-output-directory=build", name+".tex"],
                                 cwd=output, capture_output=True)
            if run.returncode:
                raise RuntimeError(f"{name}.tex 编译失败，见 {build / (name+'.log')}")


def main(argv=None):
    p = argparse.ArgumentParser(description="把 PPTX 转为高中园 Beamer；保留点击顺序，输出审核清单。")
    p.add_argument("source", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--theme", type=Path, default=DEFAULT_THEME)
    p.add_argument("--reviewed", type=Path, help="明确指定可信的审核 JSON（其中 tex 会用于编译）")
    p.add_argument("--inspect-only", action="store_true")
    p.add_argument("--compile", action="store_true")
    args = p.parse_args(argv)
    source = args.source.resolve()
    if source.suffix.lower() != ".pptx" or not source.is_file():
        p.error("source 必须是已有的 .pptx 文件")
    output = (args.output or source.with_name(source.stem+"_Beamer")).resolve()
    if output.exists() and any(output.iterdir()):
        p.error("输出目录非空。为保护已编辑的 TeX，请指定新的 --output 目录。")
    manifest = inspect_pptx(source)
    config = json.loads(args.reviewed.read_text(encoding="utf-8-sig")) if args.reviewed else {}
    if config and config.get("source_sha256") != manifest["source_sha256"]:
        p.error("审核配置 SHA-256 与源文件不匹配")
    output.mkdir(parents=True, exist_ok=True)
    if args.inspect_only:
        (output / "inspection.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        extract_media(source, manifest, output)
        generate(manifest, output, config, args.theme.resolve())
        if args.compile:
            compile_tex(output)
    print(f"完成：{output}\n{len(manifest['slides'])} 页，{sum(len(s['events']) for s in manifest['slides'])} 个动画事件。")
    if not config:
        print("这是自动转换初稿，需按 inspection.json / conversion-report.json 逐页核对。")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        print(f"转换失败：{exc}", file=sys.stderr)
        sys.exit(1)
