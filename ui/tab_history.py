"""
ui/tab_history.py
Tab lịch sử tải xuống.
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

from core import history as hist
from . import theme as T
from .widgets import styled_btn


class HistoryTab(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=T.BG, **kw)
        self._build()
        self.refresh()

    def _build(self):
        top = tk.Frame(self, bg=T.BG)
        top.pack(fill="x", padx=16, pady=(14, 8))

        tk.Label(top, text="Lịch sử tải xuống", font=T.FONT_BOLD,
                 fg=T.MAUVE, bg=T.BG).pack(side="left")

        styled_btn(top, "🔄 Làm mới", self.refresh,
                   color=T.BLUE, fg=T.BG).pack(side="right", ipadx=6, ipady=2)
        styled_btn(top, "🗑 Xóa lịch sử", self._confirm_clear,
                   color=T.RED, fg=T.BG).pack(side="right", padx=(0, 8), ipadx=6, ipady=2)

        # Search
        search_row = tk.Frame(self, bg=T.SURFACE, padx=8, pady=6)
        search_row.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(search_row, text="🔍", bg=T.SURFACE, fg=T.SUBTEXT, font=T.FONT).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self.refresh())
        tk.Entry(search_row, textvariable=self._search_var, bg=T.SURFACE2,
                 fg=T.TEXT, insertbackground=T.TEXT, relief="flat",
                 font=T.FONT).pack(side="left", fill="x", expand=True, ipady=4, padx=(6,0))

        # Treeview
        tree_frame = tk.Frame(self, bg=T.BG)
        tree_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        cols = ("date", "title", "format", "quality", "path")
        self._tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            style="Custom.Treeview", selectmode="browse",
        )
        self._tree.heading("date",    text="Thời gian")
        self._tree.heading("title",   text="Tiêu đề")
        self._tree.heading("format",  text="Định dạng")
        self._tree.heading("quality", text="Chất lượng")
        self._tree.heading("path",    text="Thư mục lưu")

        self._tree.column("date",    width=130, anchor="center", stretch=False)
        self._tree.column("title",   width=320, anchor="w")
        self._tree.column("format",  width=70,  anchor="center", stretch=False)
        self._tree.column("quality", width=80,  anchor="center", stretch=False)
        self._tree.column("path",    width=250, anchor="w")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

        # Context menu
        self._menu = tk.Menu(self, tearoff=0, bg=T.SURFACE, fg=T.TEXT,
                             activebackground=T.OVERLAY, activeforeground=T.TEXT,
                             font=T.FONT_SMALL)
        self._menu.add_command(label="🌐 Mở URL trên YouTube", command=self._open_url)
        self._menu.add_command(label="📂 Mở thư mục", command=self._open_folder)
        self._menu.add_separator()
        self._menu.add_command(label="🗑 Xóa mục này", command=self._delete_entry)

        self._tree.bind("<Button-3>", self._show_menu)
        self._tree.bind("<Double-1>", lambda _: self._open_url())

        self._history_data: list[dict] = []

    def refresh(self):
        for iid in self._tree.get_children():
            self._tree.delete(iid)
        query = self._search_var.get().lower() if hasattr(self, "_search_var") else ""
        data = hist.load_history()
        self._history_data = data
        for i, entry in enumerate(data):
            if query and query not in entry.get("title", "").lower() and query not in entry.get("url", "").lower():
                continue
            self._tree.insert("", "end", iid=str(i), values=(
                entry.get("date", "—"),
                entry.get("title", "—")[:60],
                entry.get("format", "—").upper(),
                entry.get("quality", "—"),
                entry.get("save_path", "—"),
            ))

    def _get_selected_entry(self) -> dict | None:
        sel = self._tree.selection()
        if not sel:
            return None
        idx = int(sel[0])
        if idx < len(self._history_data):
            return self._history_data[idx]
        return None

    def _show_menu(self, event):
        iid = self._tree.identify_row(event.y)
        if iid:
            self._tree.selection_set(iid)
            self._menu.tk_popup(event.x_root, event.y_root)

    def _open_url(self):
        entry = self._get_selected_entry()
        if entry:
            webbrowser.open(entry.get("url", ""))

    def _open_folder(self):
        entry = self._get_selected_entry()
        if entry:
            path = entry.get("save_path", "")
            if os.path.exists(path):
                os.startfile(path)
            else:
                messagebox.showwarning("Lỗi", f"Thư mục không tồn tại:\n{path}")

    def _delete_entry(self):
        entry = self._get_selected_entry()
        if not entry:
            return
        data = hist.load_history()
        try:
            data.remove(entry)
        except ValueError:
            pass
        import json
        hist_file = os.path.join(os.path.dirname(__file__), "..", "data", "history.json")
        with open(hist_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.refresh()

    def _confirm_clear(self):
        if messagebox.askyesno("Xác nhận", "Xóa toàn bộ lịch sử tải xuống?"):
            hist.clear_history()
            self.refresh()
