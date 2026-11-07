# Word Documents

## Choose the Approach

| Task                                                    | Approach                                                                                                        |
| ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| New prose document, such as a report, memo, or spec     | Write Markdown, then run `docproc.py convert report.md --to docx`. Add `--toc` and `--reference-doc` as needed. |
| Fill a template, change text, add rows, or add comments | python-docx on a copy of the file.                                                                              |
| Read a document                                         | `docproc.py extract`. It keeps headings, tables, and footnotes.                                                 |
| PDF output                                              | `docproc.py convert FILE --to pdf`. It fills tables of contents and fields first.                               |

## Design a Document

- Build structure with styles, not direct formatting. Headings use Heading 1 to Heading 3. Body text uses Normal or Body Text. The table of contents, the navigation pane, and PDF bookmarks all come from heading styles. Bold text is not a heading.
- Step down one heading level at a time. Do not jump from Heading 1 to Heading 3.
- Set body text at 10 to 12 pt, line spacing at 1.15 to 1.5, and margins at 2 to 2.5 cm.
- Use one font family for body text and at most one more for headings.
- Use tables for data, not for layout. Repeat the header row across pages, right-align numbers, and leave out empty spacer rows.
- Put page numbers, the document title, and confidentiality lines in headers and footers.
- Use list styles such as List Bullet and List Number. Typed "1." text breaks automatic numbering.
- Place figure captions below figures and table captions above tables.

## Templates with `pandoc`

pandoc takes styles from a reference document, not content.

- Export pandoc's default reference: `pandoc -o ref.docx --print-default-data-file reference.docx`.
- Change its styles with python-docx, or use the user's own docx as the reference.
- Convert: `docproc.py convert report.md --to docx --reference-doc ref.docx`.

```python
from docx import Document
from docx.shared import Pt, RGBColor

reference = Document("ref.docx")
reference.styles["Heading 1"].font.color.rgb = RGBColor(0x8B, 0x00, 0x00)
reference.styles["Normal"].font.size = Pt(11)
reference.save("ref.docx")
```

- `--toc` inserts a table of contents field. Word fills it when the file opens. `docproc.py convert FILE --to pdf` fills it before export.
- Footnotes come from Markdown `[^1]` references.
- LibreOffice previews show every pandoc footnote as number 1. The docx itself numbers them correctly in Word.

## `python-docx`

- Open the source, then save to a new path.
- A style must exist in the document before `add_paragraph(text, style="Heading 1")` can use it. Otherwise python-docx raises `KeyError`.
- `document.add_comment(runs, text="...", author="...")` adds a comment to a list of runs.
- Change page orientation by setting `section.orientation` and swapping `section.page_width` and `section.page_height`.
- python-docx has no API for footnotes, tables of contents, or tracked changes. Use pandoc for footnotes and tables of contents. A table of contents field written by python-docx stays empty in LibreOffice output, even after a refresh.

### Replace Placeholders

Word splits paragraph text into runs at arbitrary points. A placeholder such as `{amount}` can arrive as `Total: {amo` and `unt}`, so replacing run by run misses it. Replace at paragraph level. Keep the first run, which keeps its formatting.

```python
from docx import Document


def replace_in_paragraph(paragraph, old, new):
  if old not in paragraph.text:
    return

  text = paragraph.text.replace(old, new)

  for run in paragraph.runs[1:]:
    run.text = ""

  paragraph.runs[0].text = text


document = Document("template.docx")

for paragraph in document.paragraphs:
  replace_in_paragraph(paragraph, "{amount}", "$4,200")

for table in document.tables:
  for row in table.rows:
    for cell in row.cells:
      for paragraph in cell.paragraphs:
        replace_in_paragraph(paragraph, "{amount}", "$4,200")

document.save("filled.docx")
```

Headers and footers hold their own paragraphs in `section.header.paragraphs` and `section.footer.paragraphs`.

### Tracked Changes

Write `w:ins` and `w:del` elements. Word and LibreOffice show them as changes to accept or reject. `docproc.py inspect` counts them.

```python
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

document = Document()
paragraph = document.add_paragraph("Price is ")

for change_id, tag, text in [("1", "w:ins", "$12"), ("2", "w:del", "$10")]:
  change = OxmlElement(tag)
  change.set(qn("w:id"), change_id)
  change.set(qn("w:author"), "Reviewer")
  change.set(qn("w:date"), "2026-11-05T00:00:00Z")
  run = OxmlElement("w:r")
  run_text = OxmlElement("w:delText" if tag == "w:del" else "w:t")
  run_text.text = text
  run.append(run_text)
  change.append(run)
  paragraph._p.append(change)

document.save("tracked.docx")
```

Each change needs a `w:id` that is unique in the document.
