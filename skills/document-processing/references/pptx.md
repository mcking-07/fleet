# Presentations

## Design a Deck

- Give each slide one message. Write the title as the takeaway, such as "Revenue grew 18% in Q3", not the topic, such as "Revenue".
- Start from the user's template or brand deck. Use its layouts and placeholders. Do not add loose text boxes where a placeholder exists.
- Set titles at 28 to 40 pt and body text at 18 pt or larger. Use at most six bullets and one level of nesting. Move detail into speaker notes.
- Use one visual per slide: a chart, a table, an image, or a diagram. Build charts as native charts when the data exists, so they stay editable.
- Align everything to a grid. Keep margins near 0.5 in, share left edges, and keep gaps equal.
- Keep contrast at 4.5 to 1 or higher between text and background.
- Keep titles in the same position on every slide. Give the same data series the same color on every chart.
- Label units, round to the precision the audience needs, and make the one number that matters stand out.
- New decks without a template default to 4:3 in python-pptx. Set 16:9 with `slide_width = Inches(13.333)` and `slide_height = Inches(7.5)`.

## `python-pptx`

### Build from a Template

`docproc.py inspect` lists the template's layouts. Find a layout by name and fill its placeholders by index. In the standard layouts, index 0 is the title and index 1 is the body. Check a layout with `[(ph.placeholder_format.idx, ph.name) for ph in slide.placeholders]`.

```python
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

deck = Presentation("template.pptx")
layout = next(layout for layout in deck.slide_layouts if layout.name == "Title and Content")
slide = deck.slides.add_slide(layout)
slide.placeholders[0].text = "Revenue grew 18% in Q3"
body = slide.placeholders[1].text_frame
body.text = "Enterprise deals closed early"
detail = body.add_paragraph()
detail.text = "Three deals moved from Q4"
detail.level = 1
slide.notes_slide.notes_text_frame.text = "Mention the Q4 pipeline."

chart_layout = next(layout for layout in deck.slide_layouts if layout.name == "Title Only")
chart_slide = deck.slides.add_slide(chart_layout)
chart_slide.shapes.title.text = "Revenue by quarter"
data = CategoryChartData()
data.categories = ["Q1", "Q2", "Q3"]
data.add_series("2026", (120, 150, 180))
chart_slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(1), Inches(1.5), Inches(8), Inches(5), data)

deck.save("deck.pptx")
```

| Element       | Call                                                                                          |
| ------------- | --------------------------------------------------------------------------------------------- |
| Table         | `slide.shapes.add_table(rows, cols, x, y, width, height).table`, then `table.cell(r, c).text` |
| Image         | `slide.shapes.add_picture(path, x, y, width=Inches(4))`. Height follows the aspect ratio.     |
| Speaker notes | `slide.notes_slide.notes_text_frame.text`                                                     |

### Delete and Reorder Slides

python-pptx has no public API for either. Both work through the slide list.

```python
slide_ids = deck.slides._sldIdLst
removed = slide_ids[2]
deck.part.drop_rel(removed.rId)
slide_ids.remove(removed)

last = slide_ids[-1]
slide_ids.remove(last)
slide_ids.insert(0, last)
```

## Limits

- python-pptx does not measure text. Text that overflows its box stays overflowing. Render the deck and look at every slide.
- Autofit settings take effect only when PowerPoint opens the file.
- python-pptx cannot create SmartArt, animations, or transitions. It keeps existing ones.
