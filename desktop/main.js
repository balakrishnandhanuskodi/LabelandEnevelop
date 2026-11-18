// Entrainment 26 Print Studio — desktop shell around web/index.html.
const { app, BrowserWindow, Menu, dialog, session, shell } = require("electron");
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
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true },
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

function setupMenu() {
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    { label: "File", submenu: [{ role: "reload", label: "Start over" }, { type: "separator" }, { role: "quit" }] },
    { label: "Edit", submenu: [{ role: "undo" }, { role: "redo" }, { type: "separator" }, { role: "cut" }, { role: "copy" }, { role: "paste" }, { role: "selectAll" }] },
    { label: "View", submenu: [{ role: "zoomIn" }, { role: "zoomOut" }, { role: "resetZoom" }, { type: "separator" }, { role: "togglefullscreen" }, { role: "toggleDevTools" }] },
    { label: "Help", submenu: [{
      label: "About",
      click: () => dialog.showMessageBox(win, {
        message: "Entrainment 26 Print Studio",
        detail: `Version ${app.getVersion()}\nLabels (12 per A4) and envelope PDFs from an Excel/CSV guest list.\nYour data stays on this computer.`,
      }),
    }] },
  ]));
}

app.on("second-instance", () => { if (win) { if (win.isMinimized()) win.restore(); win.focus(); } });
app.whenReady().then(() => { setupSession(); setupMenu(); createWindow(); });
app.on("window-all-closed", () => app.quit());
