// Entrainment 26 Print Studio — desktop shell around web/index.html.
const { app, BrowserWindow, Menu, dialog, session, shell, ipcMain } = require("electron");
const fs = require("fs");
const path = require("path");

if (!app.requestSingleInstanceLock()) app.quit();

let win;

function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: "Entrainment 26 Print Studio",
    icon: path.join(__dirname, "build", "icon.png"),
    backgroundColor: "#f6f7f9",
    webPreferences: {
      contextIsolation: true, nodeIntegration: false, sandbox: true,
      preload: path.join(__dirname, "preload.js"),
    },
  });
  win.loadFile(path.join(__dirname, "app", "index.html"));

  // Links (e.g. templates) open in the normal browser, not inside the app.
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) shell.openExternal(url);
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (/^https?:/i.test(url)) { e.preventDefault(); shell.openExternal(url); }
  });
}

function setupSession() {
  const ses = session.defaultSession;

  // The QR images live on another site that doesn't allow cross-site downloads,
  // which a browser blocks. The app is local, so allow the page to read them.
  ses.webRequest.onHeadersReceived({ urls: ["http://*/*", "https://*/*"] }, (d, cb) => {
    const h = d.responseHeaders || {};
    if (d.resourceType !== "mainFrame") {
      for (const k of Object.keys(h)) if (k.toLowerCase() === "access-control-allow-origin") delete h[k];
      h["Access-Control-Allow-Origin"] = ["*"];
    }
    cb({ responseHeaders: h });
  });

  // PDFs: ask where to save (Documents by default), then offer to open them.
  ses.on("will-download", (e, item) => {
    const target = dialog.showSaveDialogSync(win, {
      title: "Save PDF",
      defaultPath: path.join(app.getPath("documents"), item.getFilename()),
      filters: [{ name: "PDF", extensions: ["pdf"] }],
    });
    if (!target) return item.cancel();
    item.setSavePath(target);
    item.once("done", async (ev, state) => {
      if (state !== "completed") {
        dialog.showErrorBox("Save failed", `The PDF couldn't be saved (${state}).`);
        return;
      }
      const { response } = await dialog.showMessageBox(win, {
        type: "info",
        message: "PDF saved",
        detail: target + "\n\nPrint at Actual size / 100 %.",
        buttons: ["Open PDF", "Show in folder", "Close"],
        defaultId: 0,
        cancelId: 2,
      });
      if (response === 0) shell.openPath(target);
      if (response === 1) shell.showItemInFolder(target);
    });
  });
}

const TOOLS = {
  entrainment: { file: "index.html", title: "Entrainment 26 Print Studio" },
  hdb: { file: "hdb-msd.html", title: "Entrainment 26 Print Studio — HDB/MSD Labels" },
};

function openTool(key) {
  const t = TOOLS[key];
  win.loadFile(path.join(__dirname, "app", t.file));
  win.webContents.once("did-finish-load", () => win.setTitle(t.title));
}

// HDB/MSD page: "Save PDF for printing" renders the print layout to an exact A4 PDF
// (no margins, no scaling) — the file prints aligned from Acrobat at "Actual size".
function setupIpc() {
  ipcMain.handle("save-pdf", async (e, suggestedName) => {
    try {
      const target = dialog.showSaveDialogSync(win, {
        title: "Save labels PDF",
        defaultPath: path.join(app.getPath("documents"), suggestedName || "labels.pdf"),
        filters: [{ name: "PDF", extensions: ["pdf"] }],
      });
      if (!target) return { ok: false };
      const data = await e.sender.printToPDF({
        pageSize: "A4",
        margins: { marginType: "none" },
        printBackground: false,
        preferCSSPageSize: true,
        scale: 1,
      });
      fs.writeFileSync(target, data);
      const { response } = await dialog.showMessageBox(win, {
        type: "info",
        message: "PDF saved",
        detail: target + "\n\nPrint it from Adobe Acrobat Reader:\nPage Sizing → Size → Actual size,\ntick \"Choose paper source by PDF page size\", Orientation Auto.",
        buttons: ["Open PDF", "Show in folder", "Close"],
        defaultId: 0,
        cancelId: 2,
      });
      if (response === 0) shell.openPath(target);
      if (response === 1) shell.showItemInFolder(target);
      return { ok: true, path: target };
    } catch (err) {
      return { ok: false, error: String(err && err.message || err) };
    }
  });
}

function setupMenu() {
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    { label: "File", submenu: [{ role: "reload", label: "Start over" }, { type: "separator" }, { role: "quit" }] },
    { label: "Tools", submenu: [
      { label: "Entrainment Labels && Envelopes", accelerator: "CmdOrCtrl+1", click: () => openTool("entrainment") },
      { label: "HDB/MSD Labels (Label 30 sheets)", accelerator: "CmdOrCtrl+2", click: () => openTool("hdb") },
    ] },
    { label: "Edit", submenu: [{ role: "undo" }, { role: "redo" }, { type: "separator" }, { role: "cut" }, { role: "copy" }, { role: "paste" }, { role: "selectAll" }] },
    { label: "View", submenu: [{ role: "zoomIn" }, { role: "zoomOut" }, { role: "resetZoom" }, { type: "separator" }, { role: "togglefullscreen" }, { role: "toggleDevTools" }] },
    { label: "Help", submenu: [{
      label: "About",
      click: () => dialog.showMessageBox(win, {
        message: "Entrainment 26 Print Studio",
        detail: `Version ${app.getVersion()}\nLabels (12 per A4) and envelope PDFs from an Excel/CSV guest list.\nTools → HDB/MSD Labels: room, T-shirt and name labels on Label 30 sheets.\nYour data stays on this computer.`,
      }),
    }] },
  ]));
}

app.on("second-instance", () => { if (win) { if (win.isMinimized()) win.restore(); win.focus(); } });
app.whenReady().then(() => { setupSession(); setupIpc(); setupMenu(); createWindow(); });
app.on("window-all-closed", () => app.quit());
