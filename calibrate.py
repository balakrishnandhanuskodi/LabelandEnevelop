#!/usr/bin/env python3
"""
Envelope calibration sheet: prints millimetre rulers so one test envelope shows
exactly where the printer puts things.

  python calibrate.py                       # DL page, 220 x 110 mm (same as the Standard envelope)
  python calibrate.py --size 241x105        # any other page size

Print it on ONE envelope with the same printer settings you use for real, then read:
  * TOP ruler (left side, numbers going down): the number at the bottom edge of the
    green band  -> that is where the band ends, in PDF millimetres from the top.
  * RIGHT ruler (along the top, numbers going left): the number at the envelope's
    right edge -> how far the page's right edge is from the envelope's right edge.
"""
import argparse
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

ap = argparse.ArgumentParser()
ap.add_argument("--size", default="220x110", help="page size WxH in mm (default DL 220x110)")
ap.add_argument("--out", type=Path, default=Path("output/envelope_calibration.pdf"))
a = ap.parse_args()
W, H = (float(v) for v in a.size.lower().split("x"))
a.out.parent.mkdir(parents=True, exist_ok=True)

c = canvas.Canvas(str(a.out), pagesize=(W * mm, H * mm))
c.setTitle(f"Envelope calibration {W:g} x {H:g} mm")

def ytop(v):          # distance from the top edge -> PDF y
    return (H - v) * mm

def xright(v):        # distance from the right edge -> PDF x
    return (W - v) * mm

# horizontal lines: distance from TOP, every 5 mm, full width
for v in range(0, int(H) + 1, 5):
    major = v % 10 == 0
    c.setLineWidth(0.5 if major else 0.2)
    c.setStrokeGray(0 if major else 0.55)
    c.line(0, ytop(v), W * mm, ytop(v))
    if major and 0 < v < H:
        c.setFont("Helvetica-Bold", 7)
        for x in (4, W * 0.35, W * 0.62):           # labels in three places
            c.drawString(x * mm, ytop(v) + 0.6 * mm, f"T{v}")

# vertical ticks: distance from RIGHT, every 5 mm, along the whole height
for v in range(0, int(W) + 1, 5):
    major = v % 10 == 0
    c.setLineWidth(0.5 if major else 0.2)
    c.setStrokeGray(0 if major else 0.55)
    c.line(xright(v), 0, xright(v), H * mm)
    if major and 0 < v <= 120:
        c.setFont("Helvetica-Bold", 6)
        for y in (3, H * 0.5, H - 7):
            c.saveState()
            c.translate(xright(v) - 0.6 * mm, y * mm)
            c.rotate(90)
            c.drawString(0, 0, f"R{v}")
            c.restoreState()

c.setFont("Helvetica-Bold", 9)
c.setFillGray(0)
c.drawString(30 * mm, H * 0.5 * mm - 12 * mm,
             f"CALIBRATION  {W:g} x {H:g} mm   T = mm from top of page   R = mm from right edge of page")
c.save()
print(f"wrote {a.out}")
