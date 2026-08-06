"use strict";

/**
 * VidGrab — Electron Main Process
 *
 * Nhiệm vụ:
 *  1. Khởi động Python backend (python-core/main.py hoặc bundled .exe)
 *  2. Tạo cửa sổ BrowserWindow load giao diện React
 *  3. Dọn dẹp khi thoát
 */

const { app, BrowserWindow, ipcMain, shell, dialog } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const http = require("http");
const fs = require("fs");

// ─── Cấu hình ───────────────────────────────────────────────────────────────

const API_PORT = 8000;
const IS_DEV = process.env.NODE_ENV === "development" || !app.isPackaged;
const ROOT = IS_DEV
  ? path.join(__dirname, "..")
  : path.join(process.resourcesPath, "app");

// ─── Đường dẫn ──────────────────────────────────────────────────────────────

function getPythonExe() {
  if (app.isPackaged) {
    // Khi đóng gói: dùng python-core.exe đã bundle
    const bundled = path.join(process.resourcesPath, "python-core.exe");
    if (fs.existsSync(bundled)) return { exe: bundled, args: [], useBundled: true };
  }
  // Dev mode hoặc không có bundled exe: dùng Python từ venv
  const venvPy = path.join(ROOT, "python-core", ".venv", "Scripts", "python.exe");
  if (fs.existsSync(venvPy)) return { exe: venvPy, args: [path.join(ROOT, "python-core", "main.py")], useBundled: false };
  // Fallback: python từ PATH
  return { exe: "python", args: [path.join(ROOT, "python-core", "main.py")], useBundled: false };
}

function getFrontendPath() {
  if (IS_DEV) {
    return path.join(ROOT, "dist-desktop", "index.desktop.html");
  }
  return path.join(process.resourcesPath, "dist-desktop", "index.desktop.html");
}

// ─── Python backend ──────────────────────────────────────────────────────────

let pythonProcess = null;

function startPythonBackend() {
  const { exe, args, useBundled } = getPythonExe();
  const env = {
    ...process.env,
    PORT: String(API_PORT),
    VIDGRAB_DIR: path.join(require("os").homedir(), "Downloads", "VidGrab"),
  };

  console.log(`[backend] Khởi động: ${exe} ${args.join(" ")}`);

  pythonProcess = spawn(exe, args, {
    env,
    cwd: path.join(ROOT, useBundled ? "." : "python-core"),
    stdio: IS_DEV ? "pipe" : "ignore",
    windowsHide: true,
  });

  if (IS_DEV && pythonProcess.stdout) {
    pythonProcess.stdout.on("data", (d) => process.stdout.write(`[py] ${d}`));
    pythonProcess.stderr.on("data", (d) => process.stderr.write(`[py] ${d}`));
  }

  pythonProcess.on("error", (err) => {
    console.error("[backend] Lỗi khởi động:", err.message);
  });

  pythonProcess.on("exit", (code) => {
    if (code !== 0 && code !== null) {
      console.warn(`[backend] Thoát với code ${code}`);
    }
  });
}

function stopPythonBackend() {
  if (pythonProcess) {
    console.log("[backend] Dừng Python backend...");
    pythonProcess.kill("SIGTERM");
    pythonProcess = null;
  }
}

// ─── Chờ API sẵn sàng ────────────────────────────────────────────────────────

function waitForApi(port, timeout = 20000) {
  return new Promise((resolve) => {
    const deadline = Date.now() + timeout;
    function attempt() {
      http
        .get(`http://127.0.0.1:${port}/health`, (res) => {
          resolve(res.statusCode === 200);
        })
        .on("error", () => {
          if (Date.now() < deadline) {
            setTimeout(attempt, 300);
          } else {
            resolve(false); // timeout — vẫn mở cửa sổ
          }
        });
    }
    attempt();
  });
}

// ─── Cửa sổ chính ────────────────────────────────────────────────────────────

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 820,
    minWidth: 800,
    minHeight: 600,
    title: "VidGrab",
    // Ẩn thanh tiêu đề mặc định — UI React có TitleBar riêng
    frame: false,
    titleBarStyle: "hidden",
    backgroundColor: "#1a1a2e", // Khớp màu nền CSS --background
    show: false, // Chờ load xong mới hiện
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      // Cho phép load file cục bộ
      webSecurity: false,
    },
    icon: path.join(__dirname, "icon.ico"),
  });

  const htmlPath = getFrontendPath();
  console.log(`[window] Load: ${htmlPath}`);
  mainWindow.loadFile(htmlPath);

  // Hiện cửa sổ khi đã render xong (tránh flash trắng)
  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
    if (IS_DEV) mainWindow.webContents.openDevTools();
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ─── IPC handlers ────────────────────────────────────────────────────────────

function registerIpcHandlers() {
  // Điều khiển cửa sổ (TitleBar buttons)
  ipcMain.on("window:minimize", () => mainWindow?.minimize());
  ipcMain.on("window:maximize", () => {
    if (!mainWindow) return;
    mainWindow.isMaximized() ? mainWindow.restore() : mainWindow.maximize();
  });
  ipcMain.on("window:close", () => mainWindow?.close());

  // Mở thư mục trong Explorer
  ipcMain.handle("shell:openFolder", async (_event, folderPath) => {
    const target = folderPath || path.join(require("os").homedir(), "Downloads", "VidGrab");
    // Đảm bảo thư mục tồn tại
    if (!fs.existsSync(target)) fs.mkdirSync(target, { recursive: true });
    await shell.openPath(target);
    return { ok: true };
  });

  // Chọn thư mục lưu
  ipcMain.handle("dialog:chooseFolder", async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ["openDirectory", "createDirectory"],
      title: "Chọn thư mục lưu video",
    });
    if (result.canceled || result.filePaths.length === 0) return null;
    return result.filePaths[0];
  });

  // Lấy thông tin cửa sổ
  ipcMain.handle("window:isMaximized", () => mainWindow?.isMaximized() ?? false);
}

// ─── App lifecycle ────────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  registerIpcHandlers();
  startPythonBackend();

  // Chờ API tối đa 20s
  console.log("[app] Chờ Python API...");
  const apiReady = await waitForApi(API_PORT, 20000);
  if (apiReady) {
    console.log("[app] API sẵn sàng.");
  } else {
    console.warn("[app] API chưa sẵn sàng, mở cửa sổ trước.");
  }

  createWindow();
});

app.on("window-all-closed", () => {
  stopPythonBackend();
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

app.on("before-quit", () => {
  stopPythonBackend();
});
