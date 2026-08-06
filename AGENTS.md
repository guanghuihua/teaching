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

## Knowledge Organization

- Start from `00_开始这里.md` and the relevant concept index before reorganizing content.
- Preserve the hierarchy between curriculum standards, concept structure, teaching materials, representative problems, and classroom reflection.
- Prefer adding or improving an index page over bulk-converting every source file to Markdown.
- Keep Obsidian links valid and use repository-relative paths.
- Do not silently rename or move large groups of linked notes, images, TeX files, PDFs, or slides.
- Preserve original source material; generated summaries, OCR output, and derived artifacts must remain distinguishable from originals.

## Mathematical and Teaching Quality

- Treat curriculum standards, textbooks, source notes, and verified mathematics as evidence; distinguish them from AI inference.
- Check definitions, conditions, quantifiers, notation, calculations, and proof dependencies before presenting a mathematical claim as correct.
- Do not reduce teaching analysis to generic encouragement. Identify the exact misconception, missing prerequisite, representation difficulty, or reasoning break.
- When creating exercises, state the target concept, expected method, likely error, difficulty, and how the result will be assessed.
- When summarizing classroom experience, preserve concrete evidence such as where students became stuck, which explanation worked, and which problem produced useful feedback.
- Do not invent student performance data, curriculum requirements, citations, or answer keys.

## File and Artifact Rules

- Use UTF-8 for text files and preserve existing Chinese filenames unless a rename is explicitly required.
- For TeX changes, compile the affected document and inspect warnings and output when the toolchain is available.
- For PDF, Word, slide, image, or spreadsheet work, use the relevant artifact workflow and visually verify the result.
- Keep temporary OCR, render, build, and visual-QA output in ignored directories.
- Avoid rewriting binary teaching materials when an index or companion note is sufficient.

## Security and Privacy

- Never commit API keys, passwords, `.env` files, local databases, or credential exports.
- `APIKEY`, `DeepSeekAPI`, local secrets, temporary files, and generated caches must remain ignored.
- Do not send identifiable student information to external AI services. Anonymize names, scores, classes, and personal details before analysis.
- Send only the minimum relevant excerpt of teaching or student material to an external model.

## Verification

- Inspect modified Markdown links, referenced paths, formulas, and source attribution.
- Verify generated questions and solutions independently before classroom use.
- For broad reorganizations, report moved files, repaired links, unresolved references, and any material requiring manual review.
- Check `git status` and `git diff` before committing.

## Git Workflow

- Preserve unrelated user changes.
- Do not commit generated PDFs, TeX build products, OCR intermediates, private student data, credentials, or temporary previews unless the repository explicitly tracks that artifact.
- After completing and verifying requested repository changes, create a focused commit and push the current branch unless the user explicitly asks not to push.
- Report the commit hash, verification performed, and any remaining limitation.
