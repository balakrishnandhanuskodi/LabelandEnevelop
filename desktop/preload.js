// Small bridge for pages inside the app (the page itself has no Node access).
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("printStudio", {
  // Opens the print dialog pre-set to A4, no margins (printer or "Microsoft Print to PDF").
  print: () => ipcRenderer.invoke("print-page"),
});
