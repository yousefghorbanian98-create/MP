// MP Studio — preload (context bridge — بدون دسترسی مستقیم به Node در رندرر)
const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("mpStudio", {
  version: "1.0.0",
});
