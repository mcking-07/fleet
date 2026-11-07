# Spreadsheets

## Choose the Library

| Task                                    | Library                                                                       |
| --------------------------------------- | ----------------------------------------------------------------------------- |
| Edit an existing workbook or template   | openpyxl. It keeps styles, formats, validation, defined names, and charts.    |
| Write a large new workbook from scratch | xlsxwriter. It is faster, but it cannot open an existing file.                |
| Read values                             | `docproc.py extract`, or openpyxl with `data_only=True`.                      |
| Read or write csv and tsv               | The `csv` module. Build an xlsx with openpyxl when the user wants a workbook. |

## Design a Workbook

- Separate inputs, calculations, and outputs. Use an inputs sheet or block, calculation sheets, and a summary sheet.
- Use a formula for every derived number. The workbook must update when an input changes. A pasted result breaks that.
- Put each assumption in its own labelled cell, with units. Reference the cell or a defined name. `=B5*1.18` hides the 1.18.
- Keep one formula pattern down a column. A row that breaks the pattern is where errors hide.
- Name sheets for what they hold. Delete empty default sheets.
- Freeze the header row, set column widths, and right-align numbers.
- Record the source and date of hardcoded data in a note cell or a Notes sheet.

### Number Formats

| Data                 | Format                                                                                         |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| Currency             | `"$"#,##0.00`, or `"$"#,##0` for large figures                                                 |
| Percentages          | `0.0%`                                                                                         |
| Negatives in finance | `#,##0;(#,##0)`                                                                                |
| Years                | `0`, never `#,##0`, so 2026 does not read 2,026                                                |
| Dates                | Write `datetime` objects and set `number_format = "yyyy-mm-dd"`. Never write dates as strings. |

### Colors in Financial Models

Use this convention unless the template has its own:

| Color                | Meaning                               |
| -------------------- | ------------------------------------- |
| Blue font `0000FF`   | Hardcoded input the user changes      |
| Black font           | Formula                               |
| Green font `008000`  | Link to another sheet in the workbook |
| Red font `FF0000`    | Link to another file                  |
| Yellow fill `FFFF00` | Assumption that needs review          |

## Formulas and Recalculation

openpyxl writes formulas without results. Excel calculates them on open. Previews such as Quick Look, mail clients, and web viewers show empty cells.

- Set `wb.calculation.fullCalcOnLoad = True` before saving. Excel then recalculates every formula on open.
- Run `docproc.py recalc FILE --out PATH`. It recalculates in LibreOffice and lists every error by cell.
- Fix each error and run `recalc` again until the list is empty.

The recalculated copy holds cached results, so every viewer shows numbers. In testing it kept number formats, fonts, fills, column widths, freeze panes, conditional formats, data validation, defined names, and charts. Deliver the copy when the recipient may use a viewer that does not calculate. Deliver the openpyxl file with `fullCalcOnLoad` for workbooks with pivot tables, slicers, or macros, because LibreOffice may rewrite those parts.

### Functions

Functions added after Excel 2010 need the `_xlfn.` prefix when written through openpyxl. Without it, both Excel and LibreOffice show `#NAME?`.

| Write                                 | Not                         |
| ------------------------------------- | --------------------------- |
| `=_xlfn.XLOOKUP("b",A2:A9,B2:B9)`     | `=XLOOKUP("b",A2:A9,B2:B9)` |
| `=_xlfn.IFS(B2>1,"big",TRUE,"small")` | `=IFS(...)`                 |
| `=_xlfn.CONCAT(A2,A3)`                | `=CONCAT(...)`              |

Older functions such as `SUM`, `SUMIFS`, `INDEX`, and `MATCH` need no prefix. LibreOffice rewrites some formula text when it saves. `FALSE` becomes `FALSE()`, which Excel also reads.

## `openpyxl` Behavior

- Loading with `data_only=True` and then saving replaces every formula with its last value. Load the file twice when you need both: once to edit formulas, once to read values.
- `read_only=True` reads large files quickly, but the workbook cannot be saved.
- An xlsm keeps its macros only when loaded with `keep_vba=True` and saved with the `.xlsm` extension.
- In a merged range, only the top-left cell holds a value.
- Column widths are in characters, not pixels.
- Loading a workbook keeps charts and images, and drops shapes and text boxes. To keep text boxes, see Restore Text Boxes After a Save.
- `openpyxl.chart` creates native charts, such as `BarChart`, `LineChart`, and `PieChart`, bound to cell ranges.

```python
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font

workbook = Workbook()
sheet = workbook.active
sheet.title = "Inputs"
sheet.append(["Item", "Value"])
sheet.append(["Price", 12.5])
sheet.append(["Units", 300])
sheet.append(["Revenue", "=B2*B3"])
sheet["B2"].number_format = '"$"#,##0.00'
sheet["B2"].font = Font(color="0000FF")
sheet.freeze_panes = "A2"
chart = BarChart()
chart.add_data(Reference(sheet, min_col=2, min_row=1, max_row=3), titles_from_data=True)
sheet.add_chart(chart, "D2")
workbook.calculation.fullCalcOnLoad = True
workbook.save("model.xlsx")
```

## Restore Text Boxes After a Save

Edit the saved file as a zip archive.

1. Copy each `xl/drawings/drawingN.xml` from the template, with its relationships file. Keep only the images the output still uses, and copy their media files.
2. Add an `Override` for each drawing part to `[Content_Types].xml`.
3. Link each drawing to its sheet. A sheet holds one drawing, so merge into any drawing openpyxl already wrote.
4. Place `<drawing r:id="…"/>` before `legacyDrawing`, `tableParts` and `extLst`.
5. Write the text into the `<a:t>` runs of each `<xdr:sp>`.
6. Set each box's height through the `<xdr:row>` of `<xdr:from>` and `<xdr:to>`. Rows count from 0.

## Check What Excel Would Repair

LibreOffice and `recalc` accept some workbooks that Excel repairs on open. For a workbook, `inspect` lists the tables, pivots and text boxes of each sheet, and reports these problems in `structure_issues`. `extract` prints the full text of each text box.

| Problem                                                                    | Effect                                                               |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| A pivot field flagged as a data field with no value column, or the reverse | Excel offers to repair the pivot table                               |
| A table column name that differs from its header cell                      | Excel repairs the table, and can open the file with editing disabled |
| A `<drawing>` element after `legacyDrawing`, `tableParts` or `extLst`      | The sheet breaks the worksheet schema order                          |

When you change a header cell inside a table, change the table's column name too, or remove the table.
