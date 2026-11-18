// Copies ../web/index.html into app/index.html and swaps the CDN <script> tags
// for local copies of the same library versions, so the desktop app works offline.
// Run after `python webapp/build.py` whenever the web app changes (npm start / dist do it for you).
const fs = require("fs");
const path = require("path");

const root = __dirname;
const app = path.join(root, "app");
const vendor = path.join(app, "vendor");
fs.mkdirSync(vendor, { recursive: true });

const libs = [
  // [CDN URL in index.html, file in node_modules, local name]
  ["https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js", "xlsx/dist/xlsx.full.min.js", "xlsx.full.min.js"],
  ["https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js", "jspdf/dist/jspdf.umd.min.js", "jspdf.umd.min.js"],
  ["https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js", "qrcode-generator/qrcode.js", "qrcode.js"],
  ["https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js", "pdfjs-dist/build/pdf.min.js", "pdf.min.js"],
  ["https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js", "pdfjs-dist/build/pdf.worker.min.js", "pdf.worker.min.js"],
];

let html = fs.readFileSync(path.join(root, "..", "web", "index.html"), "utf8");
for (const [url, src, name] of libs) {
  if (!html.includes(url)) throw new Error(`web/index.html no longer references ${url} — update prepare.js`);
  fs.copyFileSync(require.resolve(src, { paths: [root] }), path.join(vendor, name));
  html = html.split(url).join(`vendor/${name}`);
}
const left = html.match(/https:\/\/cdnjs\.[^"']+/g);
if (left) throw new Error("Unhandled CDN reference(s): " + left.join(", "));

fs.writeFileSync(path.join(app, "index.html"), html);
console.log(`app/index.html ready (${Math.round(html.length / 1024)} KB), ${libs.length} libraries bundled`);

// HDB/MSD label printer (Label 30 sheets) — second tool in the app (Tools menu).
// Update HDB_FILE when a new version of the page is added under hdb-msd/.
const HDB_FILE = path.join(root, "..", "hdb-msd", "hdb_msd_v10.html");
let hdb = fs.readFileSync(HDB_FILE, "utf8");
const xlsxUrl = libs[0][0];
if (!hdb.includes(xlsxUrl)) throw new Error(`${HDB_FILE} no longer references ${xlsxUrl} — update prepare.js`);
hdb = hdb.split(xlsxUrl).join("vendor/xlsx.full.min.js");
fs.writeFileSync(path.join(app, "hdb-msd.html"), hdb);
console.log(`app/hdb-msd.html ready (${Math.round(hdb.length / 1024)} KB) from ${path.basename(HDB_FILE)}`);
