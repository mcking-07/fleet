# PDFs

## Read

| Task                       | Command                                                               |
| -------------------------- | --------------------------------------------------------------------- |
| Text and tables            | `docproc.py extract FILE`. Pages without a text layer go through OCR. |
| Text with the layout kept  | `pdftotext -layout FILE -`                                            |
| Page count, size, producer | `pdfinfo FILE`                                                        |
| Embedded images            | `pdfimages -png FILE prefix`                                          |
| Look at pages              | `docproc.py render FILE --first N --last N`                           |

`docproc.py inspect` lists pages without a text layer under `pages_without_text`. Those pages are scans and need OCR.

## Create

Author the document as Markdown, docx, xlsx, or pptx, then run `docproc.py convert FILE --to pdf`. The design rules come from that format's reference. Convert Markdown to docx first when the PDF needs a table of contents, then convert the docx to PDF.

## Manipulate with `pypdf`

```python
from pypdf import PdfReader, PdfWriter, Transformation

merged = PdfWriter()
for path in ["a.pdf", "b.pdf"]:
  merged.append(path)
merged.write("merged.pdf")

part = PdfWriter()
part.append("merged.pdf", pages=(1, 3))
part.write("pages-2-3.pdf")

rotated = PdfWriter(clone_from="a.pdf")
rotated.pages[0].rotate(90)
rotated.write("rotated.pdf")

stamp = PdfReader("logo.pdf").pages[0]
stamped = PdfWriter(clone_from="a.pdf")
for page in stamped.pages:
  page.merge_transformed_page(stamp, Transformation().scale(0.2).translate(400, 650), over=True)
stamped.write("stamped.pdf")

locked = PdfWriter(clone_from="a.pdf")
locked.encrypt(user_password="open", owner_password="owner", algorithm="AES-256")
locked.write("locked.pdf")
```

- `pages=(1, 3)` is a zero-based, end-exclusive range. It copies pages 2 and 3.
- Read an encrypted file with `reader.decrypt(password)` before using its pages.
- Page coordinates are in points, 72 per inch, from the bottom-left corner.

## Fill Forms

`docproc.py inspect` lists the field names. Checkbox values are export names such as `/1`. `/Off` clears a checkbox. Read a checkbox's allowed values from `reader.get_fields()[name]["/_States_"]`.

```python
from pypdf import PdfWriter

form = PdfWriter(clone_from="fw9.pdf")
acroform = form.root_object["/AcroForm"]

if "/XFA" in acroform:
  del acroform["/XFA"]

form.update_page_form_field_values(
  form.pages[0],
  {
    "topmostSubform[0].Page1[0].f1_01[0]": "Jane Example",
    "topmostSubform[0].Page1[0].Boxes3a-b_ReadOrder[0].c1_1[0]": "/1",
  },
  auto_regenerate=False,
)
form.set_need_appearances_writer(True)
form.write("fw9-filled.pdf")
```

- Forms built in Adobe LiveCycle carry an XFA layer next to the AcroForm fields. Acrobat can show the XFA layer instead of the values you filled. Removing it makes every viewer use the AcroForm fields.
- Pass `flatten=True` to `update_page_form_field_values` to turn the fields into fixed page content.
- Render the filled page and check every value is visible.

## OCR

- `docproc.py extract FILE` runs OCR on pages without text. `--ocr always` forces it on every page.
- Create a searchable PDF from a scan by rendering the page and running tesseract with the `pdf` output:

```text
pdftoppm -r 300 -png -f 1 -l 1 scan.pdf page
tesseract page-1.png searchable pdf
```

- tesseract reads English by default. `tesseract --list-langs` shows the installed languages.

## Redaction

A box drawn over text does not remove the text. It stays selectable and extractable. pypdf cannot remove text from a page. Tell the user that true redaction needs a tool built for it, such as Acrobat's redaction feature.
