"""
ui/tab_playlist.py
Tab tải playlist YouTube – hiển thị danh sách video, chọn video muốn tải.
"""
from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from core.downloader import DownloadTask, DownloadManager, fetch_info
from core import history as hist
from . import theme as T
from .widgets import styled_entry, styled_btn, section_label


class PlaylistTab(tk.Frame):
    def __init__(self, parent, manager: DownloadManager, on_history_update: Callable, **kw):
        super().__init__(parent, bg=T.BG, **kw)
        self._manager = manager
        self._on_history_update = on_history_update
        self._entries: list[dict] = []
        self._task_map: dict[int, DownloadTask] = {}  # index → task

        self._url_var   = tk.StringVar()
        self._fmt_var   = tk.StringVar(value="mp4")
        self._qual_var  = tk.StringVar(value="best")
        self._save_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self._status_var = tk.StringVar(value="Nhập URL playlist và nhấn 🔍 để tải danh sách")

        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        top = tk.Frame(self, bg=T.BG)
        top.pack(fill="x", padx=16, pady=(14, 0))

        # URL
        section_label(top, "URL Playlist YouTube").pack(anchor="w")
        url_row = tk.Frame(top, bg=T.SURFACE, padx=8, pady=6)
        url_row.pack(fill="x", pady=(4, 8))
        styled_entry(url_row, textvariable=self._url_var).pack(side="left", fill="x", expand=True, ipady=5)
        self._url_var.trace_add("write", lambda *_: None)
        styled_btn(url_row, "🔍 Tải danh sách", self._fetch_playlist,
                   color=T.BLUE, fg=T.BG).pack(side="left", padx=(8, 0), ipadx=6)

        # Opts row
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
        styled_entry(path_row, textvariable=self._save_path).pack(side="left", fill="x", expand=True, ipady=4)
        styled_btn(path_row, "📁", self._choose_dir, color=T.PEACH, fg=T.BG, width=3).pack(side="left", padx=(6,0))

        # Status
        tk.Label(top, textvariable=self._status_var, font=T.FONT_SMALL,
                 fg=T.SUBTEXT, bg=T.BG).pack(anchor="w")

        # Action buttons
        act_row = tk.Frame(top, bg=T.BG)
        act_row.pack(anchor="w", pady=(6, 0))
        styled_btn(act_row, "☑ Chọn tất cả", self._select_all, color=T.SURFACE2, fg=T.TEXT).pack(side="left", ipadx=6)
        styled_btn(act_row, "☐ Bỏ chọn", self._deselect_all, color=T.SURFACE2, fg=T.TEXT).pack(side="left", padx=(6,0), ipadx=6)
        self._dl_btn = styled_btn(act_row, "⬇ Tải các video đã chọn", self._download_selected,
                                  color=T.GREEN, fg=T.BG)
        self._dl_btn.pack(side="left", padx=(12, 0), ipadx=6, ipady=4)

        # Treeview
        tree_frame = tk.Frame(self, bg=T.BG)
        tree_frame.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        cols = ("check", "idx", "title", "duration", "status")
        self._tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            style="Custom.Treeview", selectmode="browse",
        )
        self._tree.heading("check",    text="✔")
        self._tree.heading("idx",      text="#")
        self._tree.heading("title",    text="Tiêu đề")
        self._tree.heading("duration", text="Thời lượng")
        self._tree.heading("status",   text="Trạng thái")

        self._tree.column("check",    width=30,  anchor="center", stretch=False)
        self._tree.column("idx",      width=40,  anchor="center", stretch=False)
        self._tree.column("title",    width=420, anchor="w")
        self._tree.column("duration", width=80,  anchor="center", stretch=False)
        self._tree.column("status",   width=130, anchor="center", stretch=False)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

        self._tree.bind("<Button-1>", self._on_click)
        self._checked: set[str] = set()   # iid của các row được chọn

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

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _choose_dir(self):
        p = filedialog.askdirectory(initialdir=self._save_path.get())
        if p:
            self._save_path.set(p)

    def _set_status(self, msg, color=T.SUBTEXT):
        self._status_var.set(msg)

    def _fmt_duration(self, secs) -> str:
        if not secs:
            return "—"
        m, s = divmod(int(secs), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    # ── Checkbox logic ────────────────────────────────────────────────────────

    def _on_click(self, event):
        region = self._tree.identify_region(event.x, event.y)
        if region == "cell":
            col = self._tree.identify_column(event.x)
            if col == "#1":  # cột check
                iid = self._tree.identify_row(event.y)
                if iid:
                    self._toggle(iid)

    def _toggle(self, iid: str):
        vals = list(self._tree.item(iid, "values"))
        if iid in self._checked:
            self._checked.discard(iid)
            vals[0] = "☐"
        else:
            self._checked.add(iid)
            vals[0] = "☑"
        self._tree.item(iid, values=vals)

    def _select_all(self):
        for iid in self._tree.get_children():
            vals = list(self._tree.item(iid, "values"))
            vals[0] = "☑"
            self._tree.item(iid, values=vals)
            self._checked.add(iid)

    def _deselect_all(self):
        for iid in self._tree.get_children():
            vals = list(self._tree.item(iid, "values"))
            vals[0] = "☐"
            self._tree.item(iid, values=vals)
        self._checked.clear()

    # ── Fetch playlist ────────────────────────────────────────────────────────

    def _fetch_playlist(self):
        url = self._url_var.get().strip()
        if not url:
            messagebox.showwarning("Thiếu URL", "Vui lòng nhập URL playlist!")
            return
        self._set_status("🔍 Đang tải danh sách...", T.SKY)
        for iid in self._tree.get_children():
            self._tree.delete(iid)
        self._checked.clear()
        self._entries.clear()
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url: str):
        try:
            info = fetch_info(url)
            self.after(0, self._populate_tree, info)
        except Exception as e:
            self.after(0, self._set_status, f"✖ Lỗi: {e}", T.RED)

    def _populate_tree(self, info):
        if info.is_playlist:
            self._entries = info.entries
            for i, entry in enumerate(self._entries):
                dur = self._fmt_duration(entry.get("duration", 0))
                iid = self._tree.insert("", "end", iid=str(i),
                    values=("☐", i+1, entry["title"], dur, "Chờ"))
                self._checked.add(iid)
                # Auto check all
                vals = list(self._tree.item(iid, "values"))
                vals[0] = "☑"
                self._tree.item(iid, values=vals)
            self._set_status(f"✔ Tìm thấy {len(self._entries)} video trong playlist", T.GREEN)
        else:
            # Single video added to list
            self._entries = [{
                "url": info.url, "title": info.title,
                "duration": info.duration, "thumbnail": info.thumbnail,
            }]
            dur = self._fmt_duration(info.duration)
            iid = self._tree.insert("", "end", iid="0",
                values=("☑", 1, info.title, dur, "Chờ"))
            self._checked.add("0")
            self._set_status("✔ Đã thêm 1 video", T.GREEN)

    # ── Download selected ─────────────────────────────────────────────────────

    def _download_selected(self):
        if not self._checked:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn ít nhất 1 video!")
            return
        save_path = self._save_path.get()
        if not os.path.exists(save_path):
            messagebox.showwarning("Lỗi", "Thư mục lưu không hợp lệ!")
            return

        fmt     = self._fmt_var.get()
        quality = self._qual_var.get()
        count = 0

        for iid in sorted(self._checked, key=lambda x: int(x)):
            idx = int(iid)
            if idx >= len(self._entries):
                continue
            entry = self._entries[idx]
            task = DownloadTask(
                url=entry["url"], title=entry["title"],
                fmt=fmt, quality=quality, save_path=save_path,
            )
            self._task_map[idx] = task
            self._manager.add_task(task)
            count += 1

        self._set_status(f"⬇ Đang tải {count} video...", T.PEACH)
        self._dl_btn.configure(state="disabled")
        self.after(500, self._poll_all)

    def _poll_all(self):
        all_done = True
        for idx, task in self._task_map.items():
            iid = str(idx)
            if not self._tree.exists(iid):
                continue
            vals = list(self._tree.item(iid, "values"))

            if task.status == "downloading":
                all_done = False
                vals[4] = f"⬇ {task.progress:.0f}%"
            elif task.status == "done":
                vals[4] = "✅ Xong"
                hist.save_entry(task.title, task.url, task.fmt, task.quality, task.save_path)
            elif task.status == "error":
                vals[4] = "✖ Lỗi"
            else:
                all_done = False
                vals[4] = "⏳ Chờ"

            self._tree.item(iid, values=vals)

        if not all_done:
            self.after(500, self._poll_all)
        else:
            self._set_status("✅ Hoàn tất tất cả!", T.GREEN)
            self._dl_btn.configure(state="normal")
            self._on_history_update()
