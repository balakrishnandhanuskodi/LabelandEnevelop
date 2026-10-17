# Label & Envelope PDFs — Entrainment 26

Turns a guest list (Excel or CSV) into two print-ready PDFs:

| Output | Layout |
|---|---|
| `<file>_labels.pdf` | A4, **12 labels per page** (2 × 6, 105 × 49.5 mm) |
| `<file>_envelopes.pdf` | **Standard envelope** — one page per guest, DL 220 × 110 mm, content packed into the top-right corner (about 2 mm from the right edge, 1 mm from the top) |
| `<file>_envelopes_leonia.pdf` | **Leonia envelope** — DL page 220 × 110 mm (same as Standard); same layout, but the 4.5 cm green band at the top is left blank: content starts 1.5 mm below it (46.5 mm from the top), 2 mm from the right edge |

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
python generate.py guests.xlsx --qr-images ./qr_jpegs   # use QR images already on disk
python generate.py guests.xlsx --envelopes leonia       # only the Leonia envelopes (default: all types)
python generate.py guests.xlsx --copies 4               # 4 labels per guest, QR on the first only
```

Expected columns (auto-detected, case-insensitive): `Global Sequence`, `Block Sequence`, `Name`, `QR URL` (or `QR`, `URL`, `Link`…), `Resort`, `Building`, `Floor`, `Room #`.

**QR code — original image, as is:** when the QR column holds links to images (e.g. `https://…cloudfront.net/…/15335_….jpeg`), each image is downloaded and placed on the label/envelope **unchanged** (the JPEG is embedded byte-for-byte; no new QR is generated). If an image can't be downloaded, the label shows a dashed "QR image missing" box and you're warned before the PDF is built.
- Web app on Netlify: images are fetched through the site's own `/qrimg/` proxy (`netlify.toml`), so the browser isn't blocked.
- Web app opened as a local file: if the image host blocks the download, click **Add QR image files…** and pick the downloaded images — matched to rows by file name.
- Python: images are downloaded and cached in `.qr_cache/`, or pass `--qr-images FOLDER` to use files you already have.

If the QR column holds plain text (not image links), a QR containing exactly that text is generated instead. `qr_mode` in `config.json` (`auto` / `image` / `text`) or the "QR code on the label" menu in the web app overrides the choice.

Only `Name` is required. Alternative header names are listed in `config.json → columns`.

## Adjusting to your label stock / envelope

Everything is in `config.json`:

- `labels` — `copies` (1 or 4 labels per guest; with 4, only the first copy has the QR and the rest keep every other detail), page size, columns/rows, label width/height, top/left margins, gaps between labels, padding, `stack_gap_mm` (space between number, QR and code), QR size, font sizes.
- `envelope` — envelope width/height (e.g. C5 = 229 × 162, C6 = 162 × 114, #10 = 241 × 105); `print_area` sets the only box that is printed (`right_mm`, `top_mm` = gap from the envelope's right/top edges, `width_mm`, `height_mm`); `anchor: "top-right"` packs the content into that corner; plus QR size and font sizes.
- `envelope_types` — extra envelope types, each listing only what differs from the standard `envelope` (e.g. `leonia` → `print_area.top_mm: 46.5`). Each type gets its own PDF and its own button/tab in the web app.
- `qr_mode` — `auto` (image links → embed the images as is), `image` or `text`.
- `qr_pattern` — only used when there's no QR column: builds the QR text from `{Column Name}` placeholders.
- `event_title` / `print_event_title` — the event name, and whether to print it on labels and envelopes (off by default).

## Printing

- Print at **Actual size / 100 %** — turn off "Fit to page" / "Fit to printable area". Scaling shrinks everything toward the centre, so envelope text lands well inside the corner.
- Do a first sheet on plain paper with `--guides`, hold it against the label sheet (or an envelope) to check alignment, then adjust `margin_top_mm` / `margin_left_mm` (labels) or `print_area` (envelopes) if needed.
- Envelopes: set the printer's paper size to the envelope size and feed per the printer's envelope guide.

## Files

- `generate.py` — the generator
- `calibrate.py` — prints a millimetre ruler sheet to measure where the printer places things on an envelope
- `config.json` — sizes, fonts, columns, QR pattern
- `fonts/` — Caladea (metric-compatible with Cambria, Apache 2.0)
- `sample/` — made-up sample data, stand-in QR images (`sample/qr_images/`) and the output PDFs
- `web/index.html` — the web app (built file, deploy this)
- `webapp/` — web app source template + build script
- `netlify.toml` — Netlify settings
- `legacy/label-printing-portal-fixed.html` — the original browser-based portal
