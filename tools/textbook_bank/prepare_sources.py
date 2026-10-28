"""Local-only PDF rendering, Windows OCR, source geometry and page markers."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image
from pypdfium2 import raw


def render_one(task):
    source, work, number = task
    target = Path(work) / "pages" / f"{number:03}.png"
    if target.exists():
        return
    with pdfium.PdfDocument(source) as doc:
        page = doc[number - 1]
        bitmap = page.render(scale=2.1)
        bitmap.to_pil().save(target)
        bitmap.close()
        page.close()


def runs(values, gap=45):
    out = []
    for y in np.where(values)[0]:
        if not out or y > out[-1][1] + gap + 1:
            out.append([int(y), int(y)])
        else:
            out[-1][1] = int(y)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    source, work = args.source.resolve(), args.work.resolve()
    for name in ("pages", "ocr"):
        (work / name).mkdir(parents=True, exist_ok=True)
    fingerprint = hashlib.sha256(source.read_bytes()).hexdigest()
    stamp = work / "source_fingerprint.json"
    if stamp.exists():
        assert json.loads(stamp.read_text(encoding="utf-8"))["sha256"] == fingerprint, "源PDF已变化，请指定新的工作目录。"
    with pdfium.PdfDocument(str(source)) as d:
        count = len(d)
    assert count == 281, "本流程的页码与分组已针对所提供的281页教材核对，其他版本须重新校订。"
    stamp.write_text(json.dumps({"sha256": fingerprint, "pages": count}), encoding="utf-8")
    tasks = [(str(source), str(work), n) for n in range(1, count + 1)]
    with ProcessPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        for i, _ in enumerate(pool.map(render_one, tasks), 1):
            if i % 40 == 0:
                print(f"页面渲染 {i}/{count}", flush=True)
    ps = Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
    subprocess.run([str(ps), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        str(Path(__file__).with_name("ocr_pages.ps1")), "-InputDirectory", str(work / "pages"),
        "-OutputDirectory", str(work / "ocr"), "-First", "1", "-Last", str(count)], check=True)
    assets, geometry = {}, []
    with pdfium.PdfDocument(str(source)) as doc:
        for n in range(1, count + 1):
            page = doc[n - 1]
            pw, ph = page.get_size()
            rec = {"page": n, "width": pw, "height": ph, "images": []}
            for obj in page.get_objects():
                if obj.type != raw.FPDF_PAGEOBJ_IMAGE:
                    continue
                x0, y0, x1, y1 = obj.get_bounds()
                w, h, top = x1-x0, y1-y0, ph-y1
                info = {"x0": x0, "top": top, "width": w, "height": h}
                if 20 < w < 180 and 8 < h < 40 and 55 < x0 < 150 and 8 <= n <= 277:
                    bitmap = obj.get_bitmap()
                    image = bitmap.to_pil().convert("RGB")
                    hs = hashlib.sha256(image.tobytes()).hexdigest()[:16]
                    info["hash"] = hs
                    assets.setdefault(hs, {"page": n, **info})
                    bitmap.close()
                rec["images"].append(info)
            geometry.append(rec)
            page.close()
    (work / "pdf_geometry.json").write_text(json.dumps(geometry), encoding="utf-8")
    inventory = [{"index": i, **rec} for i, rec in enumerate(assets.values())]
    (work / "label_inventory.json").write_text(json.dumps(inventory), encoding="utf-8")
    pages = []
    for n in range(8, 278):
        ocr = json.loads((work / "ocr" / f"{n:03}.json").read_text(encoding="utf-8"))
        image = np.array(Image.open(work / "pages" / f"{n:03}.png").convert("RGB"))
        cyan = np.max(np.abs(image.astype("int16") - np.array([225,244,252])), axis=2) < 4
        bands = [(max(170,a-34),min(1644,b+10)) for a,b in runs(cyan[:,140:1140].sum(axis=1)>350)
                 if b-a>50 and a<1620 and b>180]
        lines = []
        for line in ocr["lines"]:
            words = line["words"]
            lines.append({"x": min(w["x"] for w in words), "y": min(w["y"] for w in words),
                          "text": re.sub(r"\s+", "", line["text"]), "words": words})
        heads = [l for l in lines if l["y"]<1645 and any(t in l["text"] for t in
            ["习题", "学而时", "温故而", "上下而", "探究", "？思考", "?思考", "数学实验"])]
        pages.append({"page": n, "bands": bands, "heads": heads, "lines": lines})
    (work / "markers.json").write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
    print("本地页面、OCR、标签图像与坐标数据准备完成。")


if __name__ == "__main__":
    main()
