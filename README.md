# Label & Envelope PDFs — Entrainment 26

Turns a guest list (Excel or CSV) into two print-ready PDFs:

| Output | Layout |
|---|---|
| `<file>_labels.pdf` | A4, **12 labels per page** (2 × 6, 105 × 49.5 mm) |
| `<file>_envelopes.pdf` | One page per guest, **DL envelope 220 × 110 mm** — content packed into the top-right corner (about 2 mm from the right edge, 1 mm from the top) |

Each label and envelope: global sequence, QR code and block sequence stacked on the left (2 mm apart); name, `Resort - Building` and `X - Room # Y` (floor, then room) on the right, starting level with the sequence number. The event title is off by default (`print_event_title` in `config.json`, or the tick box in the web app).

## Web app (no install)

Open `web/index.html` in a browser (double-click works), or host it:

- **Netlify:** connect this repo — `netlify.toml` publishes the `web/` folder, no build step. Or drag the `web` folder onto Netlify Drop.
- Upload the Excel/CSV → check the column mapping → **Labels PDF** / **Envelopes PDF**.
- Sizes and positions are under *Sizes & positions*; they're remembered in that browser.
- The guest list never leaves the browser — PDFs are built on the device.

To change the web app, edit `webapp/index.template.html`, then run `python webapp/build.py` (it embeds the fonts into `web/index.html`).

## Command line (Python)

```bash
pip install reportlab qrcode openpyxl
python generate.py guests.xlsx                # PDFs go to ./output
python generate.py guests.xlsx --guides       # adds label outlines for a test print
```

Expected columns (auto-detected, case-insensitive): `Global Sequence`, `Block Sequence`, `Name`, `QR URL` (or `QR`, `URL`, `Link`…), `Resort`, `Building`, `Floor`, `Room #`.

**QR code:** encodes the QR column's value exactly as it is in the sheet — nothing is added or changed. If the cell is an Excel hyperlink, the link's address is used (not its display text). An empty cell prints no QR. Only `Name` is required. Alternative header names are listed in `config.json → columns`.

## Adjusting to your label stock / envelope

Everything is in `config.json`:

- `labels` — page size, columns/rows, label width/height, top/left margins, gaps between labels, padding, `stack_gap_mm` (space between number, QR and code), QR size, font sizes.
- `envelope` — envelope width/height (e.g. C5 = 229 × 162, C6 = 162 × 114, #10 = 241 × 105); `print_area` sets the only box that is printed (`right_mm`, `top_mm` = gap from the envelope's right/top edges, `width_mm`, `height_mm`); `anchor: "top-right"` packs the content into that corner; plus QR size and font sizes.
- `qr_pattern` — only used when there's no QR column: builds the QR text from `{Column Name}` placeholders.
- `event_title` / `print_event_title` — the event name, and whether to print it on labels and envelopes (off by default).

## Printing

- Print at **Actual size / 100 %** — turn off "Fit to page" / "Fit to printable area". Scaling shrinks everything toward the centre, so envelope text lands well inside the corner.
- Do a first sheet on plain paper with `--guides`, hold it against the label sheet (or an envelope) to check alignment, then adjust `margin_top_mm` / `margin_left_mm` (labels) or `print_area` (envelopes) if needed.
- Envelopes: set the printer's paper size to the envelope size and feed per the printer's envelope guide.

## Files

- `generate.py` — the generator
- `config.json` — sizes, fonts, columns, QR pattern
- `fonts/` — Caladea (metric-compatible with Cambria, Apache 2.0)
- `sample/` — made-up sample data and its output PDFs
- `web/index.html` — the web app (built file, deploy this)
- `webapp/` — web app source template + build script
- `netlify.toml` — Netlify settings
- `legacy/label-printing-portal-fixed.html` — the original browser-based portal
