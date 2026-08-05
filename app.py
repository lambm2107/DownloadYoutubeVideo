"""
app.py — YouTube Downloader
Điểm khởi động chính của ứng dụng.
"""
from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk


# ── Kiểm tra và cài dependency ────────────────────────────────────────────────

REQUIRED = ["yt_dlp", "PIL", "requests"]

def _missing() -> list[str]:
    missing = []
    for pkg in REQUIRED:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    return missing

def _install_missing(pkgs: list[str]):
    pip_names = {"yt_dlp": "yt-dlp", "PIL": "Pillow", "requests": "requests"}
    for pkg in pkgs:
        pip_pkg = pip_names.get(pkg, pkg)
        print(f"Đang cài {pip_pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_pkg])


missing = _missing()
if missing:
    print(f"Cần cài: {missing}")
    try:
        _install_missing(missing)
    except Exception as e:
        print(f"Lỗi cài đặt: {e}")
        sys.exit(1)


# ── Import sau khi đảm bảo dependency ────────────────────────────────────────

from core.downloader import DownloadManager
from ui.widgets import configure_ttk_styles
from ui import theme as T
from ui.tab_single   import SingleTab
from ui.tab_playlist import PlaylistTab
from ui.tab_batch    import BatchTab
from ui.tab_history  import HistoryTab


# ── Main App ──────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader")
        self.geometry("860x640")
        self.minsize(780, 580)
        self.configure(bg=T.BG)

        # Icon (bỏ qua nếu không có file)
        try:
            self.iconbitmap("icon.ico")
        except Exception:
            pass

        configure_ttk_styles()

        # Shared download manager
        self._manager = DownloadManager(on_task_update=lambda _: None)

        self._build_header()
        self._build_tabs()

    def _build_header(self):
        header = tk.Frame(self, bg=T.BG, pady=12)
        header.pack(fill="x", padx=20)

        tk.Label(
            header,
            text="▶  YouTube Downloader",
            font=("Segoe UI", 20, "bold"),
            fg=T.MAUVE, bg=T.BG,
        ).pack(side="left")

        tk.Label(
            header,
            text="Tải video, audio & playlist từ YouTube",
            font=T.FONT_SMALL,
            fg=T.SUBTEXT, bg=T.BG,
        ).pack(side="left", padx=(16, 0), pady=(6, 0))

    def _build_tabs(self):
        nb = ttk.Notebook(self, style="TNotebook")
        nb.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        def refresh_history():
            history_tab.refresh()

        single_tab   = SingleTab(nb, self._manager, on_history_update=refresh_history)
        playlist_tab = PlaylistTab(nb, self._manager, on_history_update=refresh_history)
        batch_tab    = BatchTab(nb, self._manager, on_history_update=refresh_history)
        history_tab  = HistoryTab(nb)

        nb.add(single_tab,   text="  🎬 Video đơn  ")
        nb.add(playlist_tab, text="  📋 Playlist  ")
        nb.add(batch_tab,    text="  📦 Hàng loạt  ")
        nb.add(history_tab,  text="  🕘 Lịch sử  ")

        # Refresh history tab khi chuyển sang
        def on_tab_change(event):
            selected = nb.index(nb.select())
            if selected == 3:
                history_tab.refresh()

        nb.bind("<<NotebookTabChanged>>", on_tab_change)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
