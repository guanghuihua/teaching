# Teaching Knowledge Base Agent Guide

## Communication

- Communicate with the user primarily in Chinese.
- When the user writes English, briefly correct important grammar or wording mistakes while still answering the request.
- Lead with the usable teaching outcome, then explain evidence, changes, and verification.

## Project Purpose

- This repository is an Obsidian-style knowledge base for high-school mathematics teaching.
- Markdown provides curriculum mapping, concept indexes, problem indexes, reflections, and links between materials.
- TeX, PDF, PPT, images, and other source files remain the formal lesson, handout, assessment, and presentation materials.
- The long-term goal is to turn authentic teaching experience, student difficulties, and problem-solving evidence into a personalized AI-assisted mathematics education system.

## Repository Map

- `00_开始这里.md` is the repository entry point. `00_课程标准与总纲/` holds curriculum-standard sources and teaching-content mappings.
- `01_知识点索引/` contains concept entry pages. Update these pages when adding reusable material for an existing topic.
- `04_题库积累/` is the curated problem-bank layer; `好题索引.md` is its main entry point.
- `题目积累/` stores topic-level working materials and source-derived problem collections. OCR or model-extracted content remains a draft until a teacher has checked it.
- `教学课件/` contains lesson-specific materials and reusable presentation or handout templates.
- `高考真题/` contains source papers, their TeX/PDF derivatives, the `exam-zh` corpus, and the twelve-topic classification. Do not change a question's source wording, answer, or classification without recording the source and reason.
- `AlJabr-1-master/` is a third-party TeX textbook source. Keep its upstream structure and license intact; make local changes there only when explicitly requested.

## Knowledge Organization

- Start from `00_开始这里.md` and the relevant concept index before reorganizing content.
- Preserve the hierarchy between curriculum standards, concept structure, teaching materials, representative problems, and classroom reflection.
- Prefer adding or improving an index page over bulk-converting every source file to Markdown.
- Keep Obsidian links valid and use repository-relative paths.
- Do not silently rename or move large groups of linked notes, images, TeX files, PDFs, or slides.
- Preserve original source material; generated summaries, OCR output, and derived artifacts must remain distinguishable from originals.
- When importing a problem, retain enough provenance to locate the original paper, book, image, or solution. Flag uncertain transcriptions rather than guessing.
- For materials under `题目积累/圆锥曲线/图片资料整理/`, treat `pages/`, `qa/`, `import_reports/`, and `revision_work/` as reproducible working output. Do not promote an OCR candidate into a classroom problem or answer key until it has been manually checked against the source image.

## Mathematical and Teaching Quality

- Treat curriculum standards, textbooks, source notes, and verified mathematics as evidence; distinguish them from AI inference.
- Check definitions, conditions, quantifiers, notation, calculations, and proof dependencies before presenting a mathematical claim as correct.
- Do not reduce teaching analysis to generic encouragement. Identify the exact misconception, missing prerequisite, representation difficulty, or reasoning break.
- When creating exercises, state the target concept, expected method, likely error, difficulty, and how the result will be assessed.
- When summarizing classroom experience, preserve concrete evidence such as where students became stuck, which explanation worked, and which problem produced useful feedback.
- Do not invent student performance data, curriculum requirements, citations, or answer keys.

## File and Artifact Rules

- Use UTF-8 for text files and preserve existing Chinese filenames unless a rename is explicitly required.
- Before creating or revising a student-facing question paper, read and follow `试题排版规范.md`. Independently check every question's mathematical correctness before layout; selection questions do not receive answer space; subjective questions receive space only after the complete question; subquestions start on their own lines but are not separated by answer-space gaps.
- For TeX changes, compile the affected document and inspect warnings and output when the toolchain is available.
- For PDF, Word, slide, image, or spreadsheet work, use the relevant artifact workflow and visually verify the result.
- Keep temporary OCR, render, build, and visual-QA output in ignored directories.
- Avoid rewriting binary teaching materials when an index or companion note is sufficient.
- Do not commit TeX auxiliary files or generated PDFs merely because a local compilation produced them. Retain PDFs only when they are intentional, tracked teaching deliverables.

## Security and Privacy

- Never commit API keys, passwords, `.env` files, local databases, or credential exports.
- `APIKEY`, `DeepSeekAPI`, local secrets, temporary files, and generated caches must remain ignored.
- Do not send identifiable student information to external AI services. Anonymize names, scores, classes, and personal details before analysis.
- Send only the minimum relevant excerpt of teaching or student material to an external model.

## Verification

- For Markdown changes, open the changed note, confirm its Obsidian links resolve to the intended repository note, and check displayed mathematics, referenced paths, and source attribution.
- For TeX changes, compile only the affected document from its own directory. Use `xelatex -interaction=nonstopmode "<file>.tex"` twice when cross-references are involved, or use that directory's documented `latexmk`/`make` target. Inspect the `.log` for errors and verify the resulting PDF opens.
- For generated question sets, independently verify every question, answer, diagram reference, and scoring rule before classroom use. Items listed in `需复核题目.csv` or a `review-items.csv` remain review work, not validated material.
- For broad reorganizations, report moved files, repaired links, unresolved references, and any material requiring manual review.
- Before committing, run `git diff --check`, inspect `git diff --cached`, and confirm `git status --short` contains only the intended files.

## Git Workflow

- Preserve unrelated user changes.
- Do not commit generated PDFs, TeX build products, OCR intermediates, private student data, credentials, or temporary previews unless the repository explicitly tracks that artifact.
- After completing and verifying requested repository changes, create a focused commit and push the current branch unless the user explicitly asks not to push.
- Report the commit hash, verification performed, and any remaining limitation.
