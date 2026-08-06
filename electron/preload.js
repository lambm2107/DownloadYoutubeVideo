"use strict";

/**
 * Electron Preload Script
 * Expose một số API native an toàn cho renderer (React UI).
 * contextIsolation = true nên phải dùng contextBridge.
 */

const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  // ── Điều khiển cửa sổ (TitleBar) ──────────────────────────────────────
  minimize: () => ipcRenderer.send("window:minimize"),
  maximize: () => ipcRenderer.send("window:maximize"),
  close: () => ipcRenderer.send("window:close"),
  isMaximized: () => ipcRenderer.invoke("window:isMaximized"),

  // ── File system ────────────────────────────────────────────────────────
  openFolder: (folderPath) => ipcRenderer.invoke("shell:openFolder", folderPath),
  chooseFolder: () => ipcRenderer.invoke("dialog:chooseFolder"),

  // ── Platform info ──────────────────────────────────────────────────────
  platform: process.platform,
});
