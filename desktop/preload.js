// Small bridge for pages inside the app (the page itself has no Node access).
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("printStudio", {
  savePdf: (suggestedName) => ipcRenderer.invoke("save-pdf", suggestedName),
});
