#!/usr/bin/env python3
"""
Entrainment 26 - Label & Envelope PDF generator.

Reads an Excel/CSV guest list and writes two print-ready PDFs:
  * <name>_labels.pdf    - 12 labels per A4 page (2 x 6), sizes from config.json
  * <name>_envelopes.pdf - one envelope per guest (DL 220 x 110 mm by default)

Usage:
  python generate.py data.xlsx                 # writes to ./output
  python generate.py data.xlsx --out prints    # custom output folder
  python generate.py data.xlsx --guides        # draw label outlines (for test prints)
  python generate.py data.xlsx --config my.json

Print at "Actual size" / 100% scale, no "fit to page".
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

import qrcode
from openpyxl import load_workbook
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
FONT, FONT_BOLD = "Helvetica", "Helvetica-Bold"


# ---------------------------------------------------------------- fonts
def register_fonts():
    """Caladea is metric-compatible with Cambria (the font the HTML portal used)."""
    global FONT, FONT_BOLD
    reg, bold = HERE / "fonts" / "Caladea-Regular.ttf", HERE / "fonts" / "Caladea-Bold.ttf"
    if reg.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("Caladea", str(reg)))
        pdfmetrics.registerFont(TTFont("Caladea-Bold", str(bold)))
        FONT, FONT_BOLD = "Caladea", "Caladea-Bold"


# ---------------------------------------------------------------- data
def clean(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()


def read_rows(path: Path):
    if path.suffix.lower() == ".csv":
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
    else:
        ws = load_workbook(path, read_only=True, data_only=True).worksheets[0]
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
    rows = [r for r in rows if any(clean(c) for c in r)]
    if not rows:
        sys.exit(f"No data found in {path}")
    headers = [clean(h) for h in rows[0]]
    records = [{h: clean(r[i]) if i < len(r) else "" for i, h in enumerate(headers) if h}
               for r in rows[1:]]
    return headers, records


def map_columns(headers, candidates):
    """Same idea as the portal's auto-detect: exact match first, then 'contains'."""
    mapping = {}
    lower = {h.lower(): h for h in headers if h}
    for field, names in candidates.items():
        found = next((lower[n.lower()] for n in names if n.lower() in lower), None)
        if not found:
            found = next((h for n in names for h in headers
                          if h and n.lower() in h.lower()), None)
        mapping[field] = found
    return mapping


def fill_pattern(pattern, rec):
    return re.sub(r"\{([^}]+)\}", lambda m: rec.get(m.group(1), ""), pattern).strip()


def guest(rec, cols, qr_pattern):
    g = {k: (rec.get(c, "") if c else "") for k, c in cols.items()}
    g["resort_line"] = " - ".join(x for x in (g["resort"], g["building"]) if x)
    parts = []
    if g["floor"]:
        parts.append(f"Floor: {g['floor']}")
    if g["room"]:
        parts.append(f"Room # {g['room']}")
    g["floor_room"] = " - ".join(parts)
    g["qr"] = fill_pattern(qr_pattern, rec) or g["name"]
    return g


# ---------------------------------------------------------------- drawing helpers
_qr_cache = {}


def qr_image(text):
    if text not in _qr_cache:
        q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0, box_size=10)
        q.add_data(text)
        q.make(fit=True)
        _qr_cache[text] = ImageReader(q.make_image(fill_color="black", back_color="white").get_image())
    return _qr_cache[text]


def fit_size(text, font, size, max_w, min_size=7):
    """Shrink font until text fits max_w (points)."""
    while size > min_size and pdfmetrics.stringWidth(text, font, size) > max_w:
        size -= 0.5
    return size


def wrap_two_lines(text, font, size, max_w, min_size):
    """Return (lines, size): one line if it fits, else split into two balanced lines."""
    if pdfmetrics.stringWidth(text, font, size) <= max_w or " " not in text:
        return [text], fit_size(text, font, size, max_w, min_size)
    words = text.split()
    best = min(range(1, len(words)),
               key=lambda i: max(pdfmetrics.stringWidth(" ".join(words[:i]), font, size),
                                 pdfmetrics.stringWidth(" ".join(words[i:]), font, size)))
    lines = [" ".join(words[:best]), " ".join(words[best:])]
    s = min(fit_size(l, font, size, max_w, min_size) for l in lines)
    return lines, s


def draw_stack(c, items, cx, top, bottom):
    """items: list of (kind, payload, height_pt, font, size). Centered vertically between top/bottom."""
    total = sum(i[2] for i in items)
    y = bottom + (top - bottom + total) / 2
    for kind, payload, h, font, size in items:
        if kind == "text":
            c.setFont(font, size)
            c.drawCentredString(cx, y - h + (h - size * 0.7) / 2, payload)
        elif kind == "qr":
            c.drawImage(qr_image(payload), cx - h / 2, y - h, h, h)
        y -= h


def text_item(text, font, size, max_w, gap=1.15):
    size = fit_size(text, font, size, max_w)
    return ("text", text, size * gap, font, size)


# ---------------------------------------------------------------- labels
def draw_label(c, g, x, y, w, h, L, title, guides):
    fs = L["font_sizes_pt"]
    pad = L["padding_mm"] * mm
    if guides:
        c.setStrokeColorRGB(0.75, 0.75, 0.75)
        c.setLineWidth(0.3)
        c.rect(x, y, w, h)
    ix, iy, iw, ih = x + pad, y + pad, w - 2 * pad, h - 2 * pad
    left_w = iw * 0.25
    right_x, right_w = ix + left_w + 2 * mm, iw - left_w - 2 * mm

    # left: global seq / QR / block seq
    qr = min(L["qr_size_mm"] * mm, left_w, ih - (fs["global_seq"] + fs["block_seq"]) * 1.2)
    left = []
    if g["global_seq"]:
        left.append(text_item(g["global_seq"], FONT_BOLD, fs["global_seq"], left_w))
    if g["qr"]:
        left.append(("qr", g["qr"], qr, None, None))
    if g["block_seq"]:
        left.append(text_item(g["block_seq"], FONT_BOLD, fs["block_seq"], left_w))
    draw_stack(c, left, ix + left_w / 2, iy + ih, iy)

    # right: event title / name / resort - building / floor - room
    right = []
    if title:
        right.append(text_item(title.upper(), FONT, fs["event"], right_w, 1.5))
    if g["name"]:
        lines, s = wrap_two_lines(g["name"], FONT_BOLD, fs["name"], right_w, 11)
        right += [("text", l, s * 1.15, FONT_BOLD, s) for l in lines]
    if g["resort_line"]:
        right.append(text_item(g["resort_line"], FONT_BOLD, fs["resort"], right_w))
    if g["floor_room"]:
        right.append(text_item(g["floor_room"], FONT, fs["floor_room"], right_w))
    draw_stack(c, right, right_x + right_w / 2, iy + ih, iy)


def build_labels(guests, cfg, out, guides):
    L = cfg["labels"]
    pw, ph = L["page_width_mm"] * mm, L["page_height_mm"] * mm
    lw, lh = L["label_width_mm"] * mm, L["label_height_mm"] * mm
    cols, rows = L["columns"], L["rows"]
    per_page = cols * rows
    c = canvas.Canvas(str(out), pagesize=(pw, ph))
    c.setTitle(f"{cfg['event_title']} - Labels")
    for i, g in enumerate(guests):
        slot = i % per_page
        if slot == 0 and i:
            c.showPage()
        r, col = divmod(slot, cols)
        x = L["margin_left_mm"] * mm + col * (lw + L["gap_x_mm"] * mm)
        y = ph - L["margin_top_mm"] * mm - (r + 1) * lh - r * L["gap_y_mm"] * mm
        draw_label(c, g, x, y, lw, lh, L, cfg["event_title"], guides)
    c.save()
    return -(-len(guests) // per_page)


# ---------------------------------------------------------------- envelopes
def build_envelopes(guests, cfg, out):
    E = cfg["envelope"]
    fs = E["font_sizes_pt"]
    w, h = E["width_mm"] * mm, E["height_mm"] * mm
    m = 10 * mm
    c = canvas.Canvas(str(out), pagesize=(w, h))
    c.setTitle(f"{cfg['event_title']} - Envelopes")
    for g in guests:
        # event title, top-left
        c.setFont(FONT_BOLD, fs["event"])
        c.drawString(m, h - m - fs["event"] * 0.7, cfg["event_title"].upper())
        if cfg.get("event_subtitle"):
            c.setFont(FONT, fs["event"] * 0.7)
            c.drawString(m, h - m - fs["event"] * 1.7, cfg["event_subtitle"])
        c.setLineWidth(0.8)
        c.line(m, h - m - fs["event"] * 1.1 - (fs["event"] * 0.9 if cfg.get("event_subtitle") else 0),
               m + 60 * mm, h - m - fs["event"] * 1.1 - (fs["event"] * 0.9 if cfg.get("event_subtitle") else 0))

        # left column: global seq, QR, block seq (matches the label)
        col_w = max(E["qr_size_mm"] * mm, 34 * mm)
        left = []
        if g["global_seq"]:
            left.append(text_item(g["global_seq"], FONT_BOLD, fs["global_seq"], col_w))
        if g["qr"]:
            left.append(("qr", g["qr"], E["qr_size_mm"] * mm, None, None))
        if g["block_seq"]:
            left.append(text_item(g["block_seq"], FONT_BOLD, fs["block_seq"], col_w, 1.4))
        draw_stack(c, left, m + col_w / 2, h - m - 12 * mm, m)

        # addressee block, right-of-centre
        ax = m + col_w + 15 * mm
        aw = w - ax - m
        block = []
        if g["name"]:
            lines, s = wrap_two_lines(g["name"], FONT_BOLD, fs["name"], aw, 14)
            block += [("text", l, s * 1.2, FONT_BOLD, s) for l in lines]
        if g["resort_line"]:
            block.append(text_item(g["resort_line"], FONT_BOLD, fs["resort"], aw, 1.3))
        if g["floor_room"]:
            block.append(text_item(g["floor_room"], FONT, fs["floor_room"], aw, 1.3))
        draw_stack(c, block, ax + aw / 2, h - m - 12 * mm, m)
        c.showPage()
    c.save()


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data", type=Path, help="Excel (.xlsx) or CSV guest list")
    ap.add_argument("--config", type=Path, default=HERE / "config.json")
    ap.add_argument("--out", type=Path, default=Path("output"))
    ap.add_argument("--guides", action="store_true", help="draw label outlines for an alignment test print")
    a = ap.parse_args()

    cfg = json.loads(a.config.read_text(encoding="utf-8"))
    register_fonts()
    headers, records = read_rows(a.data)
    cols = map_columns(headers, cfg["columns"])
    if not cols.get("name"):
        sys.exit(f"Could not find a Name column. Headers found: {headers}")
    for f, h in cols.items():
        print(f"  {f:<11} <- {h or '(not found)'}")

    guests = [guest(r, cols, cfg["qr_pattern"]) for r in records]
    guests = [g for g in guests if g["name"]]
    a.out.mkdir(parents=True, exist_ok=True)
    stem = a.data.stem
    lab, env = a.out / f"{stem}_labels.pdf", a.out / f"{stem}_envelopes.pdf"
    pages = build_labels(guests, cfg, lab, a.guides)
    build_envelopes(guests, cfg, env)
    print(f"{len(guests)} guests -> {lab} ({pages} pages), {env} ({len(guests)} envelopes)")


if __name__ == "__main__":
    main()
