"""
ui/widgets.py
Các widget tái sử dụng.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from . import theme as T


def styled_entry(parent, textvariable=None, **kw) -> tk.Entry:
    return tk.Entry(
        parent,
        textvariable=textvariable,
        bg=T.SURFACE2, fg=T.TEXT,
        insertbackground=T.TEXT,
        relief="flat", bd=0,
        font=T.FONT,
        **kw,
    )


def styled_btn(parent, text, command, color=T.BLUE, fg=T.BG, **kw) -> tk.Button:
    return tk.Button(
        parent, text=text, command=command,
        bg=color, fg=fg,
        font=T.FONT_BOLD,
        activebackground=T.OVERLAY,
        activeforeground=T.TEXT,
        **T.BTN_COMMON, **kw,
    )


def section_label(parent, text: str) -> tk.Label:
    return tk.Label(
        parent, text=text,
        font=T.FONT_BOLD,
        fg=T.BLUE, bg=T.BG,
    )


def info_label(parent, text: str = "", fg=T.SUBTEXT) -> tk.Label:
    return tk.Label(parent, text=text, font=T.FONT_SMALL, fg=fg, bg=T.BG)


def configure_ttk_styles():
    s = ttk.Style()
    s.theme_use("default")

    # Progressbar
    s.configure(
        "Green.Horizontal.TProgressbar",
        troughcolor=T.SURFACE,
        background=T.GREEN,
        thickness=12,
    )

    # Combobox
    s.configure(
        "TCombobox",
        fieldbackground=T.SURFACE2,
        background=T.SURFACE2,
        foreground=T.TEXT,
        selectbackground=T.OVERLAY,
        selectforeground=T.TEXT,
        arrowcolor=T.TEXT,
    )
    s.map("TCombobox", fieldbackground=[("readonly", T.SURFACE2)])

    # Treeview
    s.configure(
        "Custom.Treeview",
        background=T.BG2,
        foreground=T.TEXT,
        fieldbackground=T.BG2,
        rowheight=26,
        font=T.FONT_SMALL,
    )
    s.configure(
        "Custom.Treeview.Heading",
        background=T.SURFACE,
        foreground=T.BLUE,
        font=T.FONT_BOLD,
        relief="flat",
    )
    s.map("Custom.Treeview", background=[("selected", T.OVERLAY)])

    # Notebook tabs
    s.configure(
        "TNotebook",
        background=T.BG,
        borderwidth=0,
    )
    s.configure(
        "TNotebook.Tab",
        background=T.SURFACE,
        foreground=T.SUBTEXT,
        padding=(14, 6),
        font=T.FONT,
    )
    s.map(
        "TNotebook.Tab",
        background=[("selected", T.BG)],
        foreground=[("selected", T.MAUVE)],
    )

    # Scrollbar
    s.configure(
        "Vertical.TScrollbar",
        background=T.OVERLAY,
        troughcolor=T.SURFACE,
        arrowcolor=T.TEXT,
        borderwidth=0,
    )
    s.configure(
        "Horizontal.TScrollbar",
        background=T.OVERLAY,
        troughcolor=T.SURFACE,
        arrowcolor=T.TEXT,
        borderwidth=0,
    )
