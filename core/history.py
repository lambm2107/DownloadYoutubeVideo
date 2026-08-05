"""
core/history.py
Lưu & đọc lịch sử tải xuống bằng JSON.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List


HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "history.json")


def _ensure_file():
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def load_history() -> List[dict]:
    _ensure_file()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_entry(title: str, url: str, fmt: str, quality: str, save_path: str):
    _ensure_file()
    history = load_history()
    history.insert(0, {
        "title": title,
        "url": url,
        "format": fmt,
        "quality": quality,
        "save_path": save_path,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    # Giữ tối đa 200 mục
    history = history[:200]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def clear_history():
    _ensure_file()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
