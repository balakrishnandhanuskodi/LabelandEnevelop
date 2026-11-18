#!/usr/bin/env python3
"""Build web/index.html from webapp/index.template.html, embedding the Caladea fonts."""
import base64
from pathlib import Path
root = Path(__file__).resolve().parent.parent
html = (root / "webapp" / "index.template.html").read_text(encoding="utf-8")
for key, name in (("__CALADEA_REG__", "Caladea-Regular.ttf"), ("__CALADEA_BOLD__", "Caladea-Bold.ttf")):
    html = html.replace(key, base64.b64encode((root / "fonts" / name).read_bytes()).decode())
(root / "web").mkdir(exist_ok=True)
(root / "web" / "index.html").write_text(html, encoding="utf-8")
print("wrote web/index.html", len(html) // 1024, "KB")

# HDB/MSD label page (Label 30 sheets) — served next to index.html so the tool tabs work.
HDB_FILE = root / "hdb-msd" / "hdb_msd_v10.html"
(root / "web" / "hdb-msd.html").write_text(HDB_FILE.read_text(encoding="utf-8"), encoding="utf-8")
print("wrote web/hdb-msd.html from", HDB_FILE.name)
