#!/usr/bin/env python3
"""Inspect, extract, render, convert, and recalculate office documents and PDFs.

Run with the skill's own interpreter, never the system python3: <skill-dir>/scripts/.pyenv/bin/python <skill-dir>/scripts/docproc.py <command> ...

Commands:
  doctor                                                                        Check the interpreter, packages, and system tools.
  inspect FILE [--password P]                                                   Summarize structure as JSON (xlsx, xlsm, docx, pptx, pdf). Workbooks also list structure_issues.
  extract FILE [--max-rows N] [--ocr auto|always|never] [--password P]          Print content as Markdown, with workbook text boxes. PDF pages without a text layer are OCRed.
  render FILE [--out DIR] [--dpi N] [--first N] [--last N]                       Render pages or slides to PNG for visual review. Prints the PNG paths.
  convert FILE --to EXT [--out DIR] [--toc] [--reference-doc DOCX]              Convert between formats. Word documents get their indexes and fields refreshed.
  recalc FILE [--out PATH]                                                      Recalculate an xlsx in LibreOffice and report formula errors.

System tools: soffice (LibreOffice), pdftoppm, pdftotext, pdfinfo (poppler), tesseract (OCR), pandoc.
"""

import argparse
import html
import importlib.metadata
import json
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

try:
  import openpyxl
  import pdfplumber
  from docx import Document
  from docx.enum.section import WD_ORIENT
  from pptx import Presentation
  from pptx.enum.shapes import MSO_SHAPE_TYPE
  from pptx.util import Emu
  from pypdf import PdfReader
except ImportError as error:
  _IMPORT_ERROR = error
else:
  _IMPORT_ERROR = None

_SCRIPTS_DIR = Path(__file__).resolve().parent
_VENV_HOME = (_SCRIPTS_DIR / ".pyenv").resolve().parent
_REQUIREMENTS = _SCRIPTS_DIR / "requirements.txt"
_PYTHON_VERSION = _SCRIPTS_DIR / ".python-version"
_SOFFICE_TIMEOUT = 180
_WRITER_INPUTS = {".docx", ".doc", ".odt", ".rtf"}
_PANDOC_INPUTS = {".md", ".markdown", ".html", ".htm"}
_WRITER_FILTERS = {"pdf": "writer_pdf_Export", "docx": "MS Word 2007 XML", "odt": "writer8"}
_EXCEL_ERRORS = {"#DIV/0!", "#N/A", "#NAME?", "#NULL!", "#NUM!", "#REF!", "#VALUE!", "#SPILL!", "#CALC!"}
_TOOLS = {
  "soffice": "required for render, convert, recalc. brew install --cask libreoffice",
  "pdftoppm": "required for render. brew install poppler",
  "pdftotext": "required for PDF text checks. brew install poppler",
  "pdfinfo": "required for PDF checks. brew install poppler",
  "tesseract": "optional, OCR for scanned PDFs. brew install tesseract",
  "pandoc": "optional, Markdown to docx and docx extraction. brew install pandoc",
}
_MACRO = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Refresh" script:language="StarBasic">
Sub Export(source As String, target As String, filterName As String)
  Dim loadArgs(0) As New com.sun.star.beans.PropertyValue
  loadArgs(0).Name = "Hidden" : loadArgs(0).Value = True
  document = StarDesktop.loadComponentFromURL(ConvertToURL(source), "_blank", 0, loadArgs())
  indexes = document.getDocumentIndexes()
  For i = 0 To indexes.getCount() - 1
    indexes.getByIndex(i).update()
  Next i
  document.getTextFields().refresh()
  Dim storeArgs(0) As New com.sun.star.beans.PropertyValue
  storeArgs(0).Name = "FilterName" : storeArgs(0).Value = filterName
  document.storeToURL(ConvertToURL(target), storeArgs())
  document.close(True)
End Sub
</script:module>
"""


class _Failure(Exception):
  pass


def _run(command, timeout=60):
  try:
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
  except FileNotFoundError as error:
    raise _Failure(f"{command[0]} is not installed. {_TOOLS.get(command[0], '')}".strip()) from error
  except subprocess.TimeoutExpired as error:
    raise _Failure(f"{command[0]} timed out after {timeout}s") from error

  if completed.returncode != 0:
    raise _Failure(f"{command[0]} failed ({completed.returncode}): {(completed.stderr or completed.stdout).strip()[:400]}")

  return completed.stdout


def _source(path):
  file = Path(path).expanduser().resolve()

  if not file.is_file():
    raise _Failure(f"file not found: {file}")

  return file


def _profile_url(directory):
  return Path(directory).as_uri()


def _prepare_profile(directory):
  _run(["soffice", f"-env:UserInstallation={_profile_url(directory)}", "--headless", "--terminate_after_init"], _SOFFICE_TIMEOUT)
  library = Path(directory) / "user" / "basic" / "Standard"

  if not library.is_dir():
    raise _Failure("LibreOffice did not create a profile")

  (library / "Refresh.xba").write_text(_MACRO)
  index = library / "script.xlb"
  index.write_text(index.read_text().replace("</library:library>", ' <library:element library:name="Refresh"/>\n</library:library>'))


def _basic_string(text):
  return '"' + text.replace('"', '""') + '"'


def _writer_export(source, target, filter_name):
  with tempfile.TemporaryDirectory(prefix="doc-lo-") as profile:
    _prepare_profile(profile)
    arguments = ",".join(_basic_string(part) for part in (str(source), str(target), filter_name))
    _run(["soffice", f"-env:UserInstallation={_profile_url(profile)}", "--headless", f"macro:///Standard.Refresh.Export({arguments})"], _SOFFICE_TIMEOUT)

  if not target.is_file():
    raise _Failure(f"LibreOffice did not write {target}")

  return target


def _soffice_convert(source, target):
  with tempfile.TemporaryDirectory(prefix="doc-lo-") as profile, tempfile.TemporaryDirectory(prefix="doc-out-") as staging:
    _run(["soffice", f"-env:UserInstallation={_profile_url(profile)}", "--headless", "--convert-to", target.suffix[1:], "--outdir", staging, str(source)], _SOFFICE_TIMEOUT)
    produced = Path(staging) / f"{source.stem}{target.suffix}"

    if not produced.is_file():
      raise _Failure(f"LibreOffice could not convert {source.name} to {target.suffix[1:]}")

    shutil.move(produced, target)

  return target


def _convert(source, target, toc=False, reference_doc=None):
  extension = target.suffix[1:].lower()

  if target == source:
    raise _Failure("output would overwrite the source. Pass a different --out")

  if source.suffix.lower() in _PANDOC_INPUTS:
    if extension not in {"docx", "odt", "pdf"}:
      raise _Failure("Markdown and HTML convert to docx, odt, or pdf")

    with tempfile.TemporaryDirectory(prefix="doc-pandoc-") as staging:
      intermediate = target if extension != "pdf" else Path(staging) / f"{source.stem}.docx"
      command = ["pandoc", str(source), "-o", str(intermediate)]
      command += ["--toc"] if toc else []
      command += [f"--reference-doc={Path(reference_doc).expanduser().resolve()}"] if reference_doc else []
      _run(command)
      return _writer_export(intermediate, target, _WRITER_FILTERS["pdf"]) if extension == "pdf" else intermediate

  if source.suffix.lower() == ".pdf":
    raise _Failure("PDF is not an editable source. Use extract for its content")

  if source.suffix.lower() in _WRITER_INPUTS and extension in _WRITER_FILTERS:
    return _writer_export(source, target, _WRITER_FILTERS[extension])

  return _soffice_convert(source, target)


def _cell_errors(sheet):
  errors = []

  for row in sheet.iter_rows():
    for cell in row:
      if isinstance(cell.value, str) and cell.value in _EXCEL_ERRORS:
        errors.append(f"{sheet.title}!{cell.coordinate} {cell.value}")

  return errors


def _xlsx_links(path, part):
  folder, _, name = part.rpartition("/")
  links = []

  for tag in re.findall(r"<Relationship [^>]*>", _zip_part(path, f"{folder}/_rels/{name}.rels")):
    target = re.search(r'Target="([^"]+)"', tag).group(1)
    target = target.lstrip("/") if target.startswith("/") else posixpath.normpath(f"{folder}/{target}")
    links.append((re.search(r'Id="([^"]+)"', tag).group(1), re.search(r'Type="[^"]*/([^"/]+)"', tag).group(1), target))

  return links


def _xlsx_sheet_parts(path):
  targets = {link: target for link, _, target in _xlsx_links(path, "xl/workbook.xml")}
  sheets = re.findall(r'<sheet [^>]*name="([^"]+)"[^>]*r:id="([^"]+)"', _zip_part(path, "xl/workbook.xml"))
  return {html.unescape(name): targets.get(link) for name, link in sheets}


def _xlsx_text_boxes(path, part):
  drawings = [target for _, kind, target in _xlsx_links(path, part) if kind == "drawing"]
  xml = _zip_part(path, drawings[0]) if drawings else ""
  boxes = []

  for match in re.finditer(r"<xdr:(\w+Anchor)\b.*?</xdr:\1>", xml, re.DOTALL):
    anchor = match.group(0)
    rows = re.findall(r"<xdr:row>(\d+)</xdr:row>", anchor)

    for shape in re.findall(r"<xdr:sp\b.*?</xdr:sp>", anchor, re.DOTALL):
      name = re.search(r'<xdr:cNvPr [^>]*name="([^"]*)"', shape)
      paragraphs = re.findall(r"<a:p\b.*?</a:p>", shape, re.DOTALL)
      text = html.unescape("\n".join("".join(re.findall(r"<a:t>(.*?)</a:t>", paragraph, re.DOTALL)) for paragraph in paragraphs).strip())
      label = html.unescape(name.group(1)) if name else None
      span = "-".join(str(int(row) + 1) for row in rows[:2])
      boxes.append({"name": label, "rows": span, "characters": len(text), "preview": text[:120], "text": text})

  return boxes


def _xlsx_pivot(path, part):
  pivot = _zip_part(path, part)
  caches = [target for _, kind, target in _xlsx_links(path, part) if kind == "pivotCacheDefinition"]
  names = [html.unescape(name) for name in re.findall(r'<cacheField [^>]*name="([^"]*)"', _zip_part(path, caches[0]) if caches else "")]
  label = html.unescape(re.search(r'<pivotTableDefinition [^>]*name="([^"]*)"', pivot).group(1))
  flagged = {index for index, field in enumerate(re.findall(r"<pivotField(?=[\s/>])[^>]*>", pivot)) if 'dataField="1"' in field}
  listed = {int(index) for index in re.findall(r'<dataField [^>]*fld="(\d+)"', pivot)}
  field = {index: names[index] if index < len(names) else f"field {index}" for index in flagged | listed}
  issues = [f"pivot {label}: {field[index]} is flagged as a data field but has no value column" for index in sorted(flagged - listed)]
  issues += [f"pivot {label}: {field[index]} has a value column but is not flagged as a data field" for index in sorted(listed - flagged)]
  return {"name": label, "data_fields": [field[index] for index in sorted(listed)], "issues": issues}


def _xlsx_table_issues(sheet):
  issues = []

  for table in sheet.tables.values():
    column, row = openpyxl.utils.cell.range_boundaries(table.ref)[:2]

    for offset, stored in enumerate(table.tableColumns):
      header = sheet.cell(row=row, column=column + offset).value

      if table.headerRowCount != 0 and ("" if header is None else str(header)) != stored.name:
        issues.append(f"table {table.name} on {sheet.title}: stored column {stored.name!r}, header cell {header!r}")

  return issues


def _inspect_xlsx(path):
  formulas = openpyxl.load_workbook(path, keep_vba=path.suffix.lower() == ".xlsm")
  values = openpyxl.load_workbook(path, data_only=True)
  parts = _xlsx_sheet_parts(path)
  sheets, issues = [], []

  for sheet in formulas.worksheets:
    cached = values[sheet.title]
    part = parts.get(sheet.title)
    pivots = [_xlsx_pivot(path, target) for _, kind, target in _xlsx_links(path, part) if kind == "pivotTable"] if part else []
    boxes = _xlsx_text_boxes(path, part) if part else []
    xml = _zip_part(path, part) if part else ""
    drawing_at = xml.find("<drawing ")
    late = [tag for tag in ("<legacyDrawing", "<tableParts", "<extLst") if drawing_at > xml.find(tag) > -1]
    issues += _xlsx_table_issues(sheet)

    for pivot in pivots:
      issues += pivot.pop("issues")

    if late:
      issues.append(f"sheet {sheet.title}: <drawing> must come before {late[0]}>")

    formula_cells = [cell for row in sheet.iter_rows() for cell in row if cell.data_type == "f"]
    missing = [cell.coordinate for cell in formula_cells if cached[cell.coordinate].value is None]
    sheets.append(
      {
        "name": sheet.title,
        "state": sheet.sheet_state,
        "dimensions": sheet.dimensions,
        "formulas": len(formula_cells),
        "formulas_without_cached_value": len(missing),
        "error_cells": _cell_errors(cached)[:20],
        "merged_ranges": len(sheet.merged_cells.ranges),
        "conditional_formats": len(sheet.conditional_formatting),
        "data_validations": len(sheet.data_validations.dataValidation),
        "freeze_panes": sheet.freeze_panes,
        "tables": [f"{table.name} {table.ref}" for table in sheet.tables.values()],
        "pivots": pivots,
        "text_boxes": [{key: box[key] for key in ("name", "rows", "characters", "preview")} for box in boxes],
      }
    )

  return {
    "format": path.suffix.lower().lstrip("."),
    "sheets": sheets,
    "defined_names": list(formulas.defined_names.keys()),
    "has_macros": path.suffix.lower() == ".xlsm",
    "needs_recalc": any(sheet["formulas_without_cached_value"] for sheet in sheets),
    "structure_issues": issues,
  }


def _zip_part(path, name):
  with zipfile.ZipFile(path) as archive:
    return archive.read(name).decode("utf-8", "replace") if name in archive.namelist() else ""


def _inspect_docx(path):
  document = Document(path)
  body = _zip_part(path, "word/document.xml")
  footnotes = _zip_part(path, "word/footnotes.xml")
  headings = []

  for paragraph in document.paragraphs:
    style = paragraph.style.name if paragraph.style is not None else ""

    if style == "Title" or style.startswith("Heading"):
      level = 0 if style == "Title" else int(re.sub(r"\D", "", style) or 1)
      headings.append({"level": level, "text": paragraph.text[:120]})

  section = document.sections[0]
  return {
    "format": "docx",
    "paragraphs": len(document.paragraphs),
    "outline": headings[:60],
    "styles_used": dict(Counter(p.style.name for p in document.paragraphs if p.style is not None).most_common(15)),
    "tables": [f"{len(table.rows)}x{len(table.columns)}" for table in document.tables],
    "images": len(document.inline_shapes),
    "sections": len(document.sections),
    "page": {
      "width_cm": round(section.page_width.cm, 1) if section.page_width else None,
      "height_cm": round(section.page_height.cm, 1) if section.page_height else None,
      "orientation": "landscape" if section.orientation == WD_ORIENT.LANDSCAPE else "portrait",
    },
    "comments": len(list(document.comments)),
    "footnotes": len(re.findall(r"<w:footnote (?![^>]*w:type=)", footnotes)),
    "tracked_insertions": body.count("<w:ins "),
    "tracked_deletions": body.count("<w:del "),
    "has_toc": "TOC \\" in body or 'w:val="Table of Contents"' in body,
  }


def _shape_kind(shape):
  if shape.has_chart:
    return "chart"

  if shape.has_table:
    return "table"

  if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
    return "picture"

  return "text" if shape.has_text_frame else "other"


def _inspect_pptx(path):
  presentation = Presentation(path)
  slides = []

  for number, slide in enumerate(presentation.slides, start=1):
    title = slide.shapes.title.text if slide.shapes.title is not None else ""
    text = " ".join(shape.text_frame.text for shape in slide.shapes if shape.has_text_frame and shape != slide.shapes.title)
    notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
    slides.append(
      {
        "slide": number,
        "layout": slide.slide_layout.name,
        "title": title[:120],
        "shapes": dict(Counter(_shape_kind(shape) for shape in slide.shapes)),
        "text": re.sub(r"\s+", " ", text)[:200],
        "notes": notes[:200],
      }
    )

  return {
    "format": "pptx",
    "slide_size_in": [round(Emu(presentation.slide_width).inches, 2), round(Emu(presentation.slide_height).inches, 2)],
    "layouts": [layout.name for layout in presentation.slide_layouts],
    "slides": slides,
  }


def _pdf_reader(path, password):
  reader = PdfReader(path)

  if reader.is_encrypted and not reader.decrypt(password or ""):
    raise _Failure("PDF is encrypted. Pass --password")

  return reader


def _inspect_pdf(path, password):
  reader = _pdf_reader(path, password)
  fields = reader.get_fields() or {}
  text_pages = [len((page.extract_text() or "").strip()) for page in reader.pages]
  box = reader.pages[0].mediabox if reader.pages else None
  return {
    "format": "pdf",
    "pages": len(reader.pages),
    "encrypted": reader.is_encrypted,
    "page_size_pt": [round(float(box.width)), round(float(box.height))] if box else None,
    "metadata": {key.lstrip("/"): str(value) for key, value in (reader.metadata or {}).items()},
    "pages_without_text": [number for number, length in enumerate(text_pages, start=1) if length < 20],
    "form_fields": len(fields),
    "form_field_names": list(fields)[:40],
  }


def _inspect(path, password=None):
  suffix = path.suffix.lower()

  if suffix in {".xlsx", ".xlsm"}:
    return _inspect_xlsx(path)

  if suffix == ".docx":
    return _inspect_docx(path)

  if suffix == ".pptx":
    return _inspect_pptx(path)

  if suffix == ".pdf":
    return _inspect_pdf(path, password)

  raise _Failure(f"unsupported format {suffix}. Supported: xlsx, xlsm, docx, pptx, pdf. Convert other office formats first with convert FILE --to EXT")


def _markdown_table(rows):
  rows = [["" if cell is None else str(cell).replace("|", "\\|").replace("\n", " ") for cell in row] for row in rows]

  if not rows:
    return ""

  width = max(len(row) for row in rows)
  rows = [row + [""] * (width - len(row)) for row in rows]
  lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
  lines += ["| " + " | ".join(row) + " |" for row in rows[1:]]
  return "\n".join(lines)


def _extract_xlsx(path, max_rows):
  values = openpyxl.load_workbook(path, data_only=True, read_only=True)
  formulas = openpyxl.load_workbook(path, read_only=True)
  sheet_parts = _xlsx_sheet_parts(path)
  parts = []

  for sheet in values.worksheets:
    rows = []

    for cached_row, formula_row in zip(sheet.iter_rows(values_only=True), formulas[sheet.title].iter_rows(values_only=True)):
      if len(rows) >= max_rows:
        break

      row = [formula if cached is None and isinstance(formula, str) and formula.startswith("=") else cached for cached, formula in zip(cached_row, formula_row)]

      if any(cell is not None for cell in row):
        rows.append(row)

    parts.append(f"## {sheet.title}\n\n{_markdown_table(rows) or '(empty)'}")
    part = sheet_parts.get(sheet.title)

    for box in _xlsx_text_boxes(path, part) if part else []:
      if box["text"]:
        parts.append(f"### Text box {box['name']} (rows {box['rows']})\n\n{box['text']}")

  return "\n\n".join(parts)


def _extract_docx(path):
  if shutil.which("pandoc"):
    return _run(["pandoc", str(path), "-t", "gfm", "--wrap=none"])

  document = Document(path)
  return "\n\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())


def _chart_summary(chart):
  series = "; ".join(f"{series.name}: {list(series.values)}" for plot in chart.plots for series in plot.series)
  categories = list(chart.plots[0].categories) if chart.plots else []
  return f"[chart {chart.chart_type}] categories {categories}; {series}"


def _extract_pptx(path):
  presentation = Presentation(path)
  parts = []

  for number, slide in enumerate(presentation.slides, start=1):
    title = slide.shapes.title.text if slide.shapes.title is not None else ""
    lines = [f"## Slide {number}: {title}".rstrip(": ")]

    for shape in slide.shapes:
      if shape == slide.shapes.title:
        continue

      if shape.has_table:
        lines.append(_markdown_table([[cell.text for cell in row.cells] for row in shape.table.rows]))
      elif shape.has_chart:
        lines.append(_chart_summary(shape.chart))
      elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        lines.append(f"[picture {shape.name}]")
      elif shape.has_text_frame and shape.text_frame.text.strip():
        lines.append(shape.text_frame.text)

    if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
      lines.append(f"Notes: {slide.notes_slide.notes_text_frame.text}")

    parts.append("\n\n".join(lines))

  return "\n\n".join(parts)


def _ocr_page(path, number, password):
  with tempfile.TemporaryDirectory(prefix="doc-ocr-") as staging:
    command = ["pdftoppm", "-r", "300", "-png", "-f", str(number), "-l", str(number)]
    command += ["-upw", password] if password else []
    _run(command + [str(path), f"{staging}/page"], 120)
    image = next(Path(staging).glob("page*.png"))
    return _run(["tesseract", str(image), "-"], 120)


def _extract_pdf(path, ocr, password):
  _pdf_reader(path, password)
  parts = []

  with pdfplumber.open(path, password=password or "") as document:
    for number, page in enumerate(document.pages, start=1):
      text = (page.extract_text() or "").strip()
      tables = [_markdown_table(table) for table in page.extract_tables() if table]

      if ocr == "always" or (ocr == "auto" and len(text) < 20):
        text = f"[OCR]\n{_ocr_page(path, number, password).strip()}"

      parts.append("\n\n".join([f"## Page {number}", text or "(no text)"] + tables))

  return "\n\n".join(parts)


def _extract(path, max_rows, ocr, password):
  suffix = path.suffix.lower()

  if suffix in {".xlsx", ".xlsm"}:
    return _extract_xlsx(path, max_rows)

  if suffix == ".docx":
    return _extract_docx(path)

  if suffix == ".pptx":
    return _extract_pptx(path)

  if suffix == ".pdf":
    return _extract_pdf(path, ocr, password)

  if suffix in {".csv", ".tsv", ".txt", ".md"}:
    return path.read_text(errors="replace")

  raise _Failure(f"unsupported format {suffix}. Supported: xlsx, xlsm, docx, pptx, pdf. Convert other office formats first with convert FILE --to EXT")


def _render(path, out, dpi, first, last):
  out = Path(out).expanduser().resolve() if out else Path(tempfile.mkdtemp(prefix=f"doc-render-{path.stem}-"))
  out.mkdir(parents=True, exist_ok=True)

  with tempfile.TemporaryDirectory(prefix="doc-pdf-") as staging:
    pdf = path if path.suffix.lower() == ".pdf" else _convert(path, Path(staging) / f"{path.stem}.pdf")
    command = ["pdftoppm", "-r", str(dpi), "-png"]
    command += ["-f", str(first)] if first else []
    command += ["-l", str(last)] if last else []
    _run(command + [str(pdf), str(out / path.stem)], 300)

  return {"pages": [str(png) for png in sorted(out.glob(f"{path.stem}*.png"))]}


def _recalc(path, out):
  if path.suffix.lower() not in {".xlsx", ".xlsm"}:
    raise _Failure("recalc takes an xlsx or xlsm file")

  target = Path(out).expanduser().resolve() if out else Path(tempfile.mkdtemp(prefix="doc-recalc-")) / path.name

  if target == path:
    raise _Failure("output would overwrite the source. Pass a different --out")

  _soffice_convert(path, target)
  formulas = openpyxl.load_workbook(path)
  values = openpyxl.load_workbook(target, data_only=True)
  errors, empty, checked = [], [], 0

  for sheet in formulas.worksheets:
    for cell in (cell for row in sheet.iter_rows() for cell in row if cell.data_type == "f"):
      checked += 1
      value = values[sheet.title][cell.coordinate].value

      if isinstance(value, str) and value in _EXCEL_ERRORS:
        errors.append({"cell": f"{sheet.title}!{cell.coordinate}", "error": value, "formula": cell.value})
      elif value is None:
        empty.append(f"{sheet.title}!{cell.coordinate}")

  return {"recalculated_copy": str(target), "formulas_checked": checked, "errors": errors, "empty_results": empty[:50]}


def _doctor():
  expected = _PYTHON_VERSION.read_text().strip() if _PYTHON_VERSION.is_file() else None
  actual = ".".join(map(str, sys.version_info[:3]))
  packages = {}

  for line in _REQUIREMENTS.read_text().split():
    name, _, pinned = line.partition("==")

    try:
      installed = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
      installed = None

    packages[name] = {"pinned": pinned, "installed": installed, "ok": installed == pinned}

  tools = {name: {"path": shutil.which(name), "note": note} for name, note in _TOOLS.items()}
  required_missing = [name for name, tool in tools.items() if tool["path"] is None and tool["note"].startswith("required")]
  ok = actual == expected and all(package["ok"] for package in packages.values()) and not required_missing
  report = {"ok": ok, "python": {"expected": expected, "actual": actual, "executable": sys.executable}, "packages": packages, "tools": tools}

  if not ok:
    report["fix"] = f'cd "{_VENV_HOME}" && rm -rf .pyenv && "$(pyenv root)/versions/$(cat .python-version)/bin/python" -m venv .pyenv && .pyenv/bin/pip install -r requirements.txt'

  return report


def _parser():
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  commands = parser.add_subparsers(dest="command", required=True)
  commands.add_parser("doctor")
  inspect = commands.add_parser("inspect")
  inspect.add_argument("file")
  inspect.add_argument("--password")
  extract = commands.add_parser("extract")
  extract.add_argument("file")
  extract.add_argument("--max-rows", type=int, default=200)
  extract.add_argument("--ocr", choices=["auto", "always", "never"], default="auto")
  extract.add_argument("--password")
  render = commands.add_parser("render")
  render.add_argument("file")
  render.add_argument("--out")
  render.add_argument("--dpi", type=int, default=80)
  render.add_argument("--first", type=int)
  render.add_argument("--last", type=int)
  convert = commands.add_parser("convert")
  convert.add_argument("file")
  convert.add_argument("--to", required=True)
  convert.add_argument("--out")
  convert.add_argument("--toc", action="store_true")
  convert.add_argument("--reference-doc")
  recalc = commands.add_parser("recalc")
  recalc.add_argument("file")
  recalc.add_argument("--out")
  return parser


def main():
  arguments = _parser().parse_args()

  if _IMPORT_ERROR is not None and arguments.command != "doctor":
    print(f"missing package: {_IMPORT_ERROR}. Run: {_SCRIPTS_DIR}/.pyenv/bin/python {__file__} doctor", file=sys.stderr)
    sys.exit(1)

  try:
    if arguments.command == "doctor":
      report = _doctor()
      print(json.dumps(report, indent=2))
      sys.exit(0 if report["ok"] else 1)

    source = _source(arguments.file)

    if arguments.command == "inspect":
      print(json.dumps(_inspect(source, arguments.password), indent=2, default=str))
    elif arguments.command == "extract":
      print(_extract(source, arguments.max_rows, arguments.ocr, arguments.password))
    elif arguments.command == "render":
      print(json.dumps(_render(source, arguments.out, arguments.dpi, arguments.first, arguments.last), indent=2))
    elif arguments.command == "convert":
      out_dir = Path(arguments.out).expanduser().resolve() if arguments.out else source.parent
      out_dir.mkdir(parents=True, exist_ok=True)
      target = out_dir / f"{source.stem}.{arguments.to.lstrip('.').lower()}"
      print(json.dumps({"output": str(_convert(source, target, arguments.toc, arguments.reference_doc))}, indent=2))
    elif arguments.command == "recalc":
      print(json.dumps(_recalc(source, arguments.out), indent=2))
  except _Failure as error:
    print(f"error: {error}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
  main()
