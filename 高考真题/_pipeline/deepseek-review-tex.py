#!/usr/bin/env python3
"""Ask DeepSeek to flag suspicious OCR/LaTeX text without modifying the source."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


SYSTEM_PROMPT = """\
你是高中数学 LaTeX 校对助手。请只检查文本，不要重写整份文档。
重点找出：
1. OCR 造成的明显乱码或不可能的公式；
2. 题干、选项、答案之间的明显矛盾；
3. 缺失的区间端点、正负号、括号或变量；
4. 可能导致 XeLaTeX 失败的命令。
输出简短问题清单，每条必须引用输入中的行号和原文片段。
没有发现问题时只输出“未发现明显问题”。
"""


def chunks(lines: list[str], size: int) -> list[tuple[int, str]]:
    result = []
    for start in range(0, len(lines), size):
        numbered = "\n".join(
            f"{number}: {line}" for number, line in enumerate(lines[start : start + size], start + 1)
        )
        result.append((start + 1, numbered))
    return result


def request_review(api_key: str, model: str, content: str, timeout: int) -> str:
    payload = json.dumps(
        {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", default="deepseek-chat")
    parser.add_argument("--lines-per-request", type=int, default=180)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise SystemExit("请先设置环境变量 DEEPSEEK_API_KEY，不要把 Key 写入命令或脚本。")

    lines = args.input.read_text(encoding="utf-8").splitlines()
    reports = [f"# DeepSeek 校对报告：{args.input.name}", ""]
    for index, (start, content) in enumerate(chunks(lines, args.lines_per_request), 1):
        try:
            review = request_review(api_key, args.model, content, args.timeout)
        except (urllib.error.URLError, KeyError, json.JSONDecodeError) as error:
            raise SystemExit(f"第 {index} 批请求失败：{error}") from error
        reports.extend([f"## 第 {start} 行起", "", review, ""])
        if index < len(chunks(lines, args.lines_per_request)):
            time.sleep(args.delay)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(reports), encoding="utf-8")
    print(f"校对报告已写入：{args.output}")


if __name__ == "__main__":
    main()
