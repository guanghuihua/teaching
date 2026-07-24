#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd)
INPUT="$REPO_ROOT/题目积累/8.专题八三角函数.doc"
OUTPUT_DIR="$REPO_ROOT/题目积累/三角函数"
NAME="专题八三角函数"
KEEP_WORK=0
DEEPSEEK_REVIEW=0

usage() {
  printf '%s\n' \
    "用法：$0 [--input 文件.doc] [--output-dir 目录] [--keep-work] [--deepseek-review]" \
    "" \
    "依赖：Windows WPS、PowerShell、XeLaTeX、~/tools/latexocr。" \
    "--deepseek-review 需要环境变量 DEEPSEEK_API_KEY。"
}

while (($#)); do
  case "$1" in
    --input) INPUT=$2; shift 2 ;;
    --output-dir) OUTPUT_DIR=$2; shift 2 ;;
    --keep-work) KEEP_WORK=1; shift ;;
    --deepseek-review) DEEPSEEK_REVIEW=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf '未知参数：%s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

for command in python3 powershell.exe wslpath; do
  command -v "$command" >/dev/null || { printf '缺少命令：%s\n' "$command" >&2; exit 1; }
done
[[ -f "$INPUT" ]] || { printf '找不到原稿：%s\n' "$INPUT" >&2; exit 1; }
[[ -d "$HOME/tools/latexocr" ]] || { printf '找不到 pix2tex：%s\n' "$HOME/tools/latexocr" >&2; exit 1; }

XELATEX=${XELATEX:-/mnt/d/texlive/2025/bin/windows/xelatex.exe}
[[ -x "$XELATEX" ]] || { printf '找不到 XeLaTeX：%s\n' "$XELATEX" >&2; exit 1; }

mkdir -p "$OUTPUT_DIR"
WORK_DIR=$(mktemp -d "${TMPDIR:-/tmp}/trig-topic.XXXXXX")
cleanup() {
  if ((KEEP_WORK)); then
    printf '保留中间文件：%s\n' "$WORK_DIR"
  else
    find "$WORK_DIR" -type f -delete 2>/dev/null || true
    find "$WORK_DIR" -depth -type d -empty -delete 2>/dev/null || true
  fi
}
trap cleanup EXIT

DOCX="$WORK_DIR/$NAME.docx"
HTML="$WORK_DIR/$NAME.html"
STRUCTURE="$WORK_DIR/structure.json"
MAPPING="$WORK_DIR/mapping.json"
SOURCE_ASSETS="$WORK_DIR/source-assets"
OCR_ONE="$WORK_DIR/formulas-1x.json"
OCR_THREE="$WORK_DIR/formulas-3x.json"
OCR_FINAL="$WORK_DIR/formulas.json"
FINAL_ASSETS="$OUTPUT_DIR/$NAME-assets"
CONTENT="$OUTPUT_DIR/$NAME-内容.tex"

printf '[1/8] WPS 转 DOCX\n'
powershell.exe -NoProfile -ExecutionPolicy Bypass \
  -File "$(wslpath -w "$SCRIPT_DIR/convert-word-docx.ps1")" \
  -InputPath "$(wslpath -w "$INPUT")" -OutputPath "$(wslpath -w "$DOCX")"

printf '[2/8] WPS 导出网页图像\n'
powershell.exe -NoProfile -ExecutionPolicy Bypass \
  -File "$(wslpath -w "$SCRIPT_DIR/export-word-html.ps1")" \
  -InputPath "$(wslpath -w "$DOCX")" -OutputPath "$(wslpath -w "$HTML")"

printf '[3/8] 提取 Word 结构\n'
python3 "$SCRIPT_DIR/extract-docx-structure.py" "$DOCX" "$STRUCTURE" --assets "$SOURCE_ASSETS"
python3 "$SCRIPT_DIR/map-word-html-images.py" "$DOCX" "$HTML" "$MAPPING"

printf '[4/8] 本地公式 OCR（1 倍）\n'
python3 "$SCRIPT_DIR/ocr-docx-formulas.py" "$MAPPING" "$SOURCE_ASSETS" "$OCR_ONE"

printf '[5/8] 本地公式 OCR（3 倍）\n'
python3 "$SCRIPT_DIR/ocr-docx-formulas.py" "$MAPPING" "$SOURCE_ASSETS" "$OCR_THREE" --scale 3
python3 "$SCRIPT_DIR/select-formula-ocr.py" "$OCR_ONE" "$OCR_THREE" "$OCR_FINAL"

printf '[6/8] 生成 exam-zh 公共内容\n'
python3 "$SCRIPT_DIR/render-trig-topic.py" \
  "$STRUCTURE" "$OCR_FINAL" "$SOURCE_ASSETS" "$CONTENT" "$FINAL_ASSETS"

printf '[7/8] 编译试卷版和答案版\n'
for tex in "$NAME-试卷版.tex" "$NAME-答案版.tex"; do
  [[ -f "$OUTPUT_DIR/$tex" ]] || { printf '缺少模板：%s\n' "$OUTPUT_DIR/$tex" >&2; exit 1; }
  for pass in 1 2; do
    (cd "$OUTPUT_DIR" && "$XELATEX" -interaction=nonstopmode -halt-on-error "$tex" >/dev/null)
  done
done

if ((DEEPSEEK_REVIEW)); then
  printf '[8/8] DeepSeek 文本校对\n'
  python3 "$SCRIPT_DIR/deepseek-review-tex.py" \
    "$CONTENT" "$OUTPUT_DIR/$NAME-DeepSeek校对.md"
else
  printf '[8/8] 跳过 DeepSeek 校对\n'
fi

find "$OUTPUT_DIR" -maxdepth 1 -type f \
  \( -name '*.aux' -o -name '*.out' -o -name '*.log' \) -delete

printf '\n完成：\n- %s\n- %s\n' \
  "$OUTPUT_DIR/$NAME-试卷版.pdf" \
  "$OUTPUT_DIR/$NAME-答案版.pdf"
