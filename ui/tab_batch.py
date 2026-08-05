"""
ui/tab_batch.py
Tab tải hàng loạt – nhập nhiều URL, theo dõi tiến trình từng video.
"""
from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from core.downloader import DownloadTask, DownloadManager
from core import history as hist
from . import theme as T
from .widgets import styled_btn, section_label


class BatchTab(tk.Frame):
    def __init__(self, parent, manager: DownloadManager, on_history_update: Callable, **kw):
        super().__init__(parent, bg=T.BG, **kw)
        self._manager = manager
        self._on_history_update = on_history_update
        self._task_map: dict[str, DownloadTask] = {}  # iid → task

        self._fmt_var   = tk.StringVar(value="mp4")
        self._qual_var  = tk.StringVar(value="best")
        self._save_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self._status_var = tk.StringVar(value="Nhập URL (mỗi URL một dòng) rồi nhấn Thêm vào hàng đợi")

        self._build()

    def _build(self):
        # ── Top controls ──────────────────────────────────────────────────────
        top = tk.Frame(self, bg=T.BG)
        top.pack(fill="x", padx=16, pady=(14, 0))

        opts = tk.Frame(top, bg=T.BG)
        opts.pack(fill="x", pady=(0, 8))

        self._build_combo(opts, "Định dạng", self._fmt_var,
                          [("mp4","🎬 MP4"), ("mp3","🎵 MP3"), ("m4a","🎵 M4A"), ("webm","🎬 WebM")], "left")
        self._build_combo(opts, "Chất lượng", self._qual_var,
                          [("best","✨ Tốt nhất"),("1080","1080p"),("720","720p"),
                           ("480","480p"),("360","360p"),("240","240p")], "left", padx=(12,0))

        # Save path
        path_row = tk.Frame(top, bg=T.SURFACE, padx=8, pady=6)
        path_row.pack(fill="x", pady=(0, 8))
        tk.Entry(path_row, textvariable=self._save_path, bg=T.SURFACE2,
                 fg=T.TEXT, insertbackground=T.TEXT, relief="flat",
                 font=T.FONT).pack(side="left", fill="x", expand=True, ipady=4)
        styled_btn(path_row, "📁", self._choose_dir, color=T.PEACH, fg=T.BG, width=3).pack(side="left", padx=(6,0))

        # URL input area
        section_label(top, "Danh sách URL (mỗi dòng 1 URL)").pack(anchor="w", pady=(4, 2))
        url_frame = tk.Frame(top, bg=T.BG2)
        url_frame.pack(fill="x")

        self._url_text = tk.Text(
            url_frame, height=5, bg=T.BG2, fg=T.TEXT,
            insertbackground=T.TEXT, relief="flat",
            font=T.FONT_MONO, wrap="none",
        )
        url_scroll = ttk.Scrollbar(url_frame, orient="vertical", command=self._url_text.yview)
        self._url_text.configure(yscrollcommand=url_scroll.set)
        url_scroll.pack(side="right", fill="y")
        self._url_text.pack(fill="x")

        # Action row
        act_row = tk.Frame(top, bg=T.BG)
        act_row.pack(anchor="w", pady=(8, 4))

        styled_btn(act_row, "➕ Thêm vào hàng đợi", self._add_to_queue,
                   color=T.BLUE, fg=T.BG).pack(side="left", ipadx=8, ipady=4)
        styled_btn(act_row, "🗑 Xóa đã hoàn thành", self._clear_done,
                   color=T.SURFACE2, fg=T.TEXT).pack(side="left", padx=(8, 0), ipadx=6, ipady=4)
        styled_btn(act_row, "✕ Xóa tất cả", self._clear_all,
                   color=T.SURFACE2, fg=T.RED).pack(side="left", padx=(8, 0), ipadx=6, ipady=4)

        tk.Label(top, textvariable=self._status_var, font=T.FONT_SMALL,
                 fg=T.SUBTEXT, bg=T.BG).pack(anchor="w")

        # ── Queue treeview ────────────────────────────────────────────────────
        tree_frame = tk.Frame(self, bg=T.BG)
        tree_frame.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        cols = ("title", "fmt", "quality", "progress", "speed", "status")
        self._tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            style="Custom.Treeview", selectmode="browse",
        )
        self._tree.heading("title",    text="Tiêu đề / URL")
        self._tree.heading("fmt",      text="Định dạng")
        self._tree.heading("quality",  text="Chất lượng")
        self._tree.heading("progress", text="Tiến trình")
        self._tree.heading("speed",    text="Tốc độ")
        self._tree.heading("status",   text="Trạng thái")

        self._tree.column("title",    width=300, anchor="w")
        self._tree.column("fmt",      width=70,  anchor="center", stretch=False)
        self._tree.column("quality",  width=80,  anchor="center", stretch=False)
        self._tree.column("progress", width=80,  anchor="center", stretch=False)
        self._tree.column("speed",    width=90,  anchor="center", stretch=False)
        self._tree.column("status",   width=110, anchor="center", stretch=False)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self._tree.pack(fill="both", expand=True)

    def _build_combo(self, parent, label, var, items, side, padx=(0,0)):
        f = tk.Frame(parent, bg=T.BG)
        f.pack(side=side, fill="x", expand=True, padx=padx)
        tk.Label(f, text=label, font=T.FONT_SMALL, fg=T.SUBTEXT, bg=T.BG).pack(anchor="w")
        displays = [v for _, v in items]
        keys     = [k for k, _ in items]
        combo = ttk.Combobox(f, textvariable=var, values=displays, state="readonly", font=T.FONT)
        combo.set(displays[0]); var.set(keys[0])
        def on_sel(e, c=combo, ks=keys, ds=displays):
            idx = ds.index(c.get()) if c.get() in ds else 0
            var.set(ks[idx])
        combo.bind("<<ComboboxSelected>>", on_sel)
        combo.pack(fill="x")

    def _choose_dir(self):
        p = filedialog.askdirectory(initialdir=self._save_path.get())
        if p:
            self._save_path.set(p)

    def _add_to_queue(self):
        raw = self._url_text.get("1.0", "end").strip()
        if not raw:
            messagebox.showwarning("Thiếu URL", "Vui lòng nhập ít nhất 1 URL!")
            return
        save_path = self._save_path.get()
        if not os.path.exists(save_path):
            messagebox.showwarning("Lỗi", "Thư mục lưu không hợp lệ!")
            return

        urls = [u.strip() for u in raw.splitlines() if u.strip()]
        fmt     = self._fmt_var.get()
        quality = self._qual_var.get()
        added = 0

        for url in urls:
            if not ("youtube.com" in url or "youtu.be" in url):
                continue
            short_title = url.split("v=")[-1][:20] if "v=" in url else url[-20:]
            iid = f"task_{id(url)}_{added}"
            task = DownloadTask(url=url, title=short_title, fmt=fmt,
                                quality=quality, save_path=save_path)
            self._task_map[iid] = task
            self._tree.insert("", "end", iid=iid,
                values=(url, fmt.upper(), quality, "0%", "—", "⏳ Chờ"))
            self._manager.add_task(task)
            added += 1

        if added:
            self._url_text.delete("1.0", "end")
            self._status_var.set(f"✔ Đã thêm {added} URL vào hàng đợi")
            self.after(500, self._poll_all)
        else:
            messagebox.showwarning("Không hợp lệ", "Không tìm thấy URL YouTube hợp lệ!")

    def _poll_all(self):
        has_active = False
        for iid, task in self._task_map.items():
            if not self._tree.exists(iid):
                continue
            vals = list(self._tree.item(iid, "values"))

            if task.status == "downloading":
                has_active = True
                vals[3] = f"{task.progress:.0f}%"
                vals[4] = task.speed
                vals[5] = f"⬇ {task.progress:.0f}%"
            elif task.status == "done":
                vals[3] = "100%"
                vals[4] = "—"
                vals[5] = "✅ Xong"
                # Update title from task
                if task.title and len(task.title) > 3:
                    vals[0] = task.title[:60]
                hist.save_entry(task.title, task.url, task.fmt, task.quality, task.save_path)
            elif task.status == "error":
                vals[3] = "—"
                vals[4] = "—"
                vals[5] = "✖ Lỗi"
            else:  # pending
                has_active = True
                vals[5] = "⏳ Chờ"

            self._tree.item(iid, values=vals)

        if has_active:
            self.after(500, self._poll_all)
        else:
            done = sum(1 for t in self._task_map.values() if t.status == "done")
            err  = sum(1 for t in self._task_map.values() if t.status == "error")
            self._status_var.set(f"✅ Hoàn tất: {done} thành công, {err} lỗi")
            self._on_history_update()

    def _clear_done(self):
        to_del = [iid for iid, t in self._task_map.items() if t.status in ("done", "error")]
        for iid in to_del:
            if self._tree.exists(iid):
                self._tree.delete(iid)
            del self._task_map[iid]

    def _clear_all(self):
        for iid in list(self._task_map.keys()):
            if self._tree.exists(iid):
                self._tree.delete(iid)
        self._task_map.clear()
        self._status_var.set("Đã xóa tất cả")
