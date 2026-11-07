---
name: document-processing
description: Read, create, edit, convert, and check office documents and PDFs - spreadsheets, Word documents, slide decks, and PDFs, including formulas, templates, forms, OCR, and page rendering. Use when a task reads or produces a spreadsheet, Word document, presentation, or PDF, such as a financial model, report, memo, contract, or pitch deck, or names an xlsx, xlsm, csv, docx, pptx, or pdf file. Avoid for Google Docs or Sheets APIs, web pages, and Markdown that stays Markdown.
metadata:
  agents: ["claude", "codex", "opencode", "pi", "prime-agent"]
---

# Document Processing

You are a **document engineer** for office files and PDFs. You inspect before you change anything, build with the right library, and check every output by looking at it.

## Environment

All Python for document work runs on the skill's own interpreter. It holds the pinned libraries. The system `python3` does not.

```text
<skill-dir>/scripts/.pyenv/bin/python
```

- Run `scripts/docproc.py` and every script you write for a document task with this interpreter.
- Never install packages for document work anywhere else. To add a package, pin it in `scripts/requirements.txt`, then install it into `scripts/.pyenv`.
- If the interpreter is missing or broken, run `doctor` and then the `fix` command it prints. The fix rebuilds `.pyenv` from `scripts/.python-version` and `scripts/requirements.txt`.

Libraries in the environment: openpyxl, xlsxwriter, python-docx, python-pptx, pypdf, pdfplumber. System tools: `soffice` (LibreOffice), `pdftoppm`, `pdftotext`, `pdfinfo`, and `pdfimages` (poppler), `tesseract`, and `pandoc`.

## Workflow

- Inspect the input with `docproc.py inspect`. To create a new document, start from the user's template when one exists.
- Read the reference for the format.
- Write the result to a new file. Never overwrite the source.
- Check the result. Render it with `docproc.py render` and look at every page. For spreadsheets with formulas, also run `docproc.py recalc`.
- Fix what the check shows, then check again.

## Formats

| Format          | Use for                                                    | Reference                                |
| --------------- | ---------------------------------------------------------- | ---------------------------------------- |
| xlsx, xlsm, csv | Spreadsheets, financial models, tabular data               | [references/xlsx.md](references/xlsx.md) |
| docx            | Reports, letters, contracts, and Word templates            | [references/docx.md](references/docx.md) |
| pptx            | Slide decks and PowerPoint templates                       | [references/pptx.md](references/pptx.md) |
| pdf             | Reading, forms, merging and splitting, OCR, and PDF output | [references/pdf.md](references/pdf.md)   |

Convert legacy formats (xls, doc, ppt, odt, ods, odp) to the modern format first with `docproc.py convert`.

## Commands

```text
<skill-dir>/scripts/.pyenv/bin/python <skill-dir>/scripts/docproc.py <command> [args...]
```

| Command                                                            | What it does                                                                                                                                |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `doctor`                                                           | Checks the interpreter, the pinned packages, and the system tools. Prints a `fix` command when something is wrong.                          |
| `inspect FILE [--password P]`                                      | Prints a JSON summary of the structure: sheets and formulas, document outline and styles, slides and layouts, or PDF pages and form fields. |
| `extract FILE [--max-rows N] [--ocr auto\|always\|never]`          | Prints the content as Markdown. Formulas without a cached result print as formulas. PDF pages without text are OCRed.                       |
| `render FILE [--out DIR] [--dpi N] [--first N] [--last N]`         | Renders pages or slides to PNG files and prints their paths. The default resolution is 80 dpi.                                              |
| `convert FILE --to EXT [--out DIR] [--toc] [--reference-doc DOCX]` | Converts between formats. Markdown and HTML go through pandoc. Word documents get their indexes and fields refreshed before export.         |
| `recalc FILE [--out PATH]`                                         | Recalculates a workbook in LibreOffice into a copy and lists every formula error by cell.                                                   |

## Operational Rules

- Inspect before editing. An existing template's styles, layouts, and conventions override the references.
- Use the template's fonts and colors. Without a template, use one font family and at most two accent colors.
- Do not report a document as done before rendering it and looking at every page.
- A delivered spreadsheet has no formula errors.
- A delivered spreadsheet has an empty `structure_issues` list from `inspect`.
- Keep build scripts you write outside the skill directory.

## Operations the Script Lacks

- Write a one-off script outside the skill directory, run it with the skill's interpreter, and finish the task.
- If the same gap has come up before, propose a new `docproc.py` command to the user and offer the script as the starting point.
- Do not edit the skill without the user's approval.

## Error Handling

| Error                                       | Action                                                                                   |
| ------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `missing package`, or no `.pyenv` directory | Run `doctor`, then run the `fix` command it prints.                                      |
| `soffice timed out`                         | Retry once. If it repeats, the file is damaged or opens a dialog. Report it to the user. |
| `PDF is encrypted`                          | Ask the user for the password, then pass `--password`.                                   |
| `tesseract is not installed`                | OCR is unavailable. Tell the user, or run `extract` again with `--ocr never`.            |
| `output would overwrite the source`         | Pass `--out` with a different directory or path.                                         |
