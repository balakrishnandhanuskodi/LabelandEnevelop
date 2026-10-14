# Label & Envelope PDFs — Entrainment 26

Turns a guest list (Excel or CSV) into two print-ready PDFs:

| Output | Layout |
|---|---|
| `<file>_labels.pdf` | A4, **12 labels per page** (2 × 6, 105 × 49.5 mm) |
| `<file>_envelopes.pdf` | One page per guest, **DL envelope 220 × 110 mm** — prints only in a 92 × 34 mm box in the top-right corner (1 mm from the right edge, 5 mm from the top — text ends about 6 mm from the edge) |

Each label and envelope carries the same layout as the original portal: global sequence, QR code and block sequence on the left; name, `Resort - Building` and `Floor: X - Room # Y` on the right; plus the event title.

## Run it

```bash
pip install reportlab qrcode openpyxl
python generate.py guests.xlsx                # PDFs go to ./output
python generate.py guests.xlsx --guides       # adds label outlines for a test print
```

Expected columns (auto-detected, case-insensitive): `Global Sequence`, `Block Sequence`, `Name`, `Resort`, `Building`, `Floor`, `Room #`. Only `Name` is required. Alternative header names are listed in `config.json → columns`.

## Adjusting to your label stock / envelope

Everything is in `config.json`:

- `labels` — page size, columns/rows, label width/height, top/left margins, gaps between labels, padding, QR size, font sizes.
- `envelope` — envelope width/height (e.g. C5 = 229 × 162, C6 = 162 × 114, #10 = 241 × 105); `print_area` sets the only box that is printed (`right_mm`, `top_mm` = gap from the envelope's right/top edges, `width_mm`, `height_mm`); plus QR size and font sizes.
- `qr_pattern` — what the QR encodes, using `{Column Name}` placeholders, e.g. `"E26-{Global Sequence}-{Name}"`.
- `event_title` / `event_subtitle` — text printed on labels and envelopes.

## Printing

- Print at **Actual size / 100 %** — never "Fit to page".
- Do a first sheet on plain paper with `--guides`, hold it against the label sheet (or an envelope) to check alignment, then adjust `margin_top_mm` / `margin_left_mm` (labels) or `print_area` (envelopes) if needed.
- Envelopes: set the printer's paper size to the envelope size and feed per the printer's envelope guide.

## Files

- `generate.py` — the generator
- `config.json` — sizes, fonts, columns, QR pattern
- `fonts/` — Caladea (metric-compatible with Cambria, Apache 2.0)
- `sample/` — made-up sample data and its output PDFs
- `legacy/label-printing-portal-fixed.html` — the original browser-based portal
