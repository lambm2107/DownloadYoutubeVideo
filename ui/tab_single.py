"""
ui/tab_single.py
Tab tải video đơn lẻ với xem trước thumbnail.
"""
from __future__ import annotations

import io
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable

import requests
from PIL import Image, ImageTk

from core.downloader import DownloadTask, DownloadManager, fetch_info, VideoInfo
from core import history as hist
from . import theme as T
from .widgets import styled_entry, styled_btn, section_label, info_label


class SingleTab(tk.Frame):
    def __init__(self, parent, manager: DownloadManager, on_history_update: Callable, **kw):
        super().__init__(parent, bg=T.BG, **kw)
        self._manager = manager
        self._on_history_update = on_history_update
        self._info: VideoInfo | None = None
        self._thumb_img = None  # giữ ref tránh GC

        self._save_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self._url_var   = tk.StringVar()
        self._fmt_var   = tk.StringVar(value="mp4")
        self._qual_var  = tk.StringVar(value="best")
        self._status_var = tk.StringVar(value="Nhập URL và nhấn 🔍 để lấy thông tin video")
        self._progress_var = tk.DoubleVar(value=0.0)

        self._build()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        # === Cột trái: form ===
        left = tk.Frame(self, bg=T.BG)
        left.pack(side="left", fill="both", expand=True, padx=(16, 8), pady=16)

        # URL row
        section_label(left, "URL Video YouTube").pack(anchor="w")
        url_row = tk.Frame(left, bg=T.SURFACE, padx=8, pady=6)
        url_row.pack(fill="x", pady=(4, 0))

        self._url_entry = styled_entry(url_row, textvariable=self._url_var)
        self._url_entry.pack(side="left", fill="x", expand=True, ipady=5)
        self._url_entry.bind("<Return>", lambda _: self._fetch_info())

        styled_btn(url_row, "🔍", self._fetch_info, color=T.BLUE, width=3).pack(side="left", padx=(6, 0))
        styled_btn(url_row, "✕", lambda: self._url_var.set(""), color=T.SURFACE2, fg=T.RED, width=2).pack(side="left", padx=(4, 0))

        # Format & quality
        opts_frame = tk.Frame(left, bg=T.BG)
        opts_frame.pack(fill="x", pady=(12, 0))

        self._build_combo(opts_frame, "Định dạng", self._fmt_var,
                          [("mp4", "🎬 MP4 (Video)"), ("mp3", "🎵 MP3 (Audio)"),
                           ("m4a", "🎵 M4A (Audio)"), ("webm", "🎬 WebM (Video)")],
                          side="left")

        self._build_combo(opts_frame, "Chất lượng", self._qual_var,
                          [("best", "✨ Tốt nhất"), ("2160", "4K 2160p"), ("1440", "2K 1440p"),
                           ("1080", "Full HD 1080p"), ("720", "HD 720p"),
                           ("480", "480p"), ("360", "360p"), ("240", "240p")],
                          side="left", padx=(12, 0))

        # Save path
        section_label(left, "Thư mục lưu").pack(anchor="w", pady=(12, 0))
        path_row = tk.Frame(left, bg=T.SURFACE, padx=8, pady=6)
        path_row.pack(fill="x", pady=(4, 0))
        styled_entry(path_row, textvariable=self._save_path).pack(side="left", fill="x", expand=True, ipady=4)
        styled_btn(path_row, "📁", self._choose_dir, color=T.PEACH, fg=T.BG, width=3).pack(side="left", padx=(6, 0))

        # Progress
        prog_frame = tk.Frame(left, bg=T.BG)
        prog_frame.pack(fill="x", pady=(16, 0))

        self._prog_bar = ttk.Progressbar(
            prog_frame, variable=self._progress_var,
            maximum=100, style="Green.Horizontal.TProgressbar",
        )
        self._prog_bar.pack(fill="x")

        self._status_lbl = tk.Label(
            prog_frame, textvariable=self._status_var,
            font=T.FONT_SMALL, fg=T.SUBTEXT, bg=T.BG,
        )
        self._status_lbl.pack(anchor="w", pady=(4, 0))

        # Download button
        btn_row = tk.Frame(left, bg=T.BG)
        btn_row.pack(pady=(14, 0))

        self._dl_btn = styled_btn(
            btn_row, "⬇  Tải Xuống", self._start_download,
            color=T.GREEN, fg=T.BG, width=18,
        )
        self._dl_btn.pack(side="left", ipady=8, padx=(0, 10))

        styled_btn(btn_row, "📂 Mở thư mục", self._open_folder,
                   color=T.SURFACE2, fg=T.TEXT, width=14).pack(side="left", ipady=8)

        # === Cột phải: thumbnail + info ===
        right = tk.Frame(self, bg=T.SURFACE, width=220)
        right.pack(side="right", fill="y", padx=(0, 16), pady=16)
        right.pack_propagate(False)

        self._thumb_lbl = tk.Label(right, bg=T.SURFACE, text="", cursor="hand2")
        self._thumb_lbl.pack(pady=(12, 6), padx=10)
        self._thumb_lbl.bind("<Button-1>", lambda _: self._open_url())

        self._video_title = tk.Label(
            right, text="—", font=T.FONT_BOLD,
            fg=T.TEXT, bg=T.SURFACE, wraplength=200, justify="center",
        )
        self._video_title.pack(padx=8)

        self._video_meta = tk.Label(
            right, text="", font=T.FONT_SMALL,
            fg=T.SUBTEXT, bg=T.SURFACE, wraplength=200, justify="center",
        )
        self._video_meta.pack(padx=8, pady=(4, 0))

        self._playlist_lbl = tk.Label(
            right, text="", font=T.FONT_SMALL,
            fg=T.MAUVE, bg=T.SURFACE,
        )
        self._playlist_lbl.pack(pady=(4, 0))

        # Placeholder thumb
        self._set_placeholder_thumb()

    def _build_combo(self, parent, label: str, var: tk.StringVar, items: list,
                     side="left", padx=(0, 0)):
        f = tk.Frame(parent, bg=T.BG)
        f.pack(side=side, fill="x", expand=True, padx=padx)
        tk.Label(f, text=label, font=T.FONT_SMALL, fg=T.SUBTEXT, bg=T.BG).pack(anchor="w")
        values_display = [v for _, v in items]
        values_key     = [k for k, _ in items]
        combo = ttk.Combobox(f, textvariable=var, values=values_display, state="readonly", font=T.FONT)
        combo.pack(fill="x")
        # Map display → key
        def on_select(event, combo=combo, keys=values_key, displays=values_display):
            idx = displays.index(combo.get()) if combo.get() in displays else 0
            var.set(keys[idx])
        combo.bind("<<ComboboxSelected>>", on_select)
        combo.set(values_display[0])
        var.set(values_key[0])
        return combo

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_placeholder_thumb(self):
        img = Image.new("RGB", (200, 112), color="#313244")
        tk_img = ImageTk.PhotoImage(img)
        self._thumb_lbl.configure(image=tk_img, text="")
        self._thumb_img = tk_img

    def _set_status(self, msg: str, color: str = T.SUBTEXT):
        self._status_var.set(msg)
        self._status_lbl.configure(fg=color)

    def _choose_dir(self):
        path = filedialog.askdirectory(initialdir=self._save_path.get())
        if path:
            self._save_path.set(path)

    def _open_folder(self):
        path = self._save_path.get()
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showwarning("Lỗi", "Thư mục không tồn tại!")

    def _open_url(self):
        if self._info:
            import webbrowser
            webbrowser.open(self._info.url)

    def _load_thumbnail(self, url: str):
        try:
            resp = requests.get(url, timeout=10)
            img = Image.open(io.BytesIO(resp.content))
            img = img.resize((200, 112), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            self._thumb_lbl.configure(image=tk_img, text="")
            self._thumb_img = tk_img
        except Exception:
            pass

    # ── Fetch info ────────────────────────────────────────────────────────────

    def _fetch_info(self):
        url = self._url_var.get().strip()
        if not url:
            messagebox.showwarning("Thiếu URL", "Vui lòng nhập URL video YouTube!")
            return
        self._set_status("🔍 Đang lấy thông tin...", T.SKY)
        self._video_title.configure(text="Đang tải...")
        self._video_meta.configure(text="")
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url: str):
        try:
            info = fetch_info(url)
            self._info = info
            self.after(0, self._update_info_ui, info)
        except Exception as e:
            self.after(0, self._set_status, f"✖ Lỗi: {e}", T.RED)
            self.after(0, self._video_title.configure, {"text": "Không thể lấy thông tin"})

    def _update_info_ui(self, info: VideoInfo):
        if info.is_playlist:
            self._video_title.configure(text=f"📋 {info.title}")
            self._playlist_lbl.configure(text=f"{info.playlist_count} videos trong playlist")
            self._video_meta.configure(text="")
            self._set_status(f"Playlist: {info.playlist_count} video", T.MAUVE)
        else:
            self._video_title.configure(text=info.title)
            mins, secs = divmod(info.duration, 60)
            views = f"{info.view_count:,}" if info.view_count else "—"
            meta = f"⏱ {mins:02d}:{secs:02d}  |  👁 {views}\n📺 {info.uploader}"
            self._video_meta.configure(text=meta)
            self._playlist_lbl.configure(text="")
            self._set_status("✔ Sẵn sàng tải xuống", T.GREEN)

        if info.thumbnail:
            threading.Thread(target=self._load_thumbnail, args=(info.thumbnail,), daemon=True).start()

    # ── Download ──────────────────────────────────────────────────────────────

    def _start_download(self):
        url = self._url_var.get().strip()
        if not url:
            messagebox.showwarning("Thiếu URL", "Vui lòng nhập URL!")
            return

        save_path = self._save_path.get()
        if not os.path.exists(save_path):
            messagebox.showwarning("Lỗi", "Thư mục lưu không hợp lệ!")
            return

        fmt     = self._fmt_var.get()
        quality = self._qual_var.get()
        title   = self._info.title if self._info else url

        self._dl_btn.configure(state="disabled", text="⏳ Đang tải...", bg=T.OVERLAY)
        self._progress_var.set(0)
        self._set_status("Đang bắt đầu...", T.PEACH)

        task = DownloadTask(url=url, title=title, fmt=fmt, quality=quality, save_path=save_path)
        self._manager.add_task(task)

        # Poll task status
        self.after(300, self._poll_task, task)

    def _poll_task(self, task: DownloadTask):
        self._progress_var.set(task.progress)
        if task.status == "downloading":
            self._set_status(
                f"⬇ {task.progress:.1f}%  |  {task.speed}  |  ETA: {task.eta}",
                T.GREEN,
            )
            self.after(300, self._poll_task, task)

        elif task.status == "done":
            self._progress_var.set(100)
            self._set_status("✅ Tải xuống hoàn tất!", T.GREEN)
            self._dl_btn.configure(state="normal", text="⬇  Tải Xuống", bg=T.GREEN)
            hist.save_entry(task.title, task.url, task.fmt, task.quality, task.save_path)
            self._on_history_update()
            messagebox.showinfo("Hoàn tất", f'Đã tải xong!\n"{task.title}"')

        elif task.status == "error":
            self._set_status(f"✖ Lỗi: {task.error[:60]}", T.RED)
            self._dl_btn.configure(state="normal", text="⬇  Tải Xuống", bg=T.GREEN)
            messagebox.showerror("Lỗi", task.error)

        else:
            self.after(300, self._poll_task, task)
