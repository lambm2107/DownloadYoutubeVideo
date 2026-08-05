"""
core/downloader.py
Xử lý tất cả logic tải xuống dùng yt-dlp.
"""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional
import yt_dlp


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class VideoInfo:
    url: str
    title: str = ""
    duration: int = 0          # giây
    thumbnail: str = ""        # URL ảnh
    uploader: str = ""
    view_count: int = 0
    formats: list = field(default_factory=list)
    is_playlist: bool = False
    playlist_count: int = 0
    entries: list = field(default_factory=list)   # danh sách video trong playlist


@dataclass
class DownloadTask:
    url: str
    title: str
    fmt: str           # "mp4" | "mp3" | "webm" | "m4a"
    quality: str       # "best" | "1080" | "720" | ...
    save_path: str
    status: str = "pending"   # pending | downloading | done | error
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    error: str = ""
    file_path: str = ""


# ── Helper: build yt-dlp options ──────────────────────────────────────────────

def build_ydl_opts(
    save_path: str,
    fmt: str,
    quality: str,
    progress_hook: Callable,
    extra_opts: dict | None = None,
) -> dict:
    """Tạo options dict cho yt-dlp."""

    postprocessors = []

    if fmt == "mp3":
        ydl_format = "bestaudio/best"
        postprocessors.append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        })
    elif fmt == "m4a":
        ydl_format = "bestaudio[ext=m4a]/bestaudio/best"
    elif fmt == "webm":
        ydl_format = "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best"
    else:
        # mp4
        q_map = {
            "best":  "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "2160":  "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]",
            "1440":  "bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440]",
            "1080":  "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
            "720":   "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
            "480":   "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
            "360":   "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]",
            "240":   "bestvideo[height<=240][ext=mp4]+bestaudio[ext=m4a]/best[height<=240]",
        }
        ydl_format = q_map.get(quality, q_map["best"])
        postprocessors.append({"key": "FFmpegVideoConvertor", "preferedformat": "mp4"})

    opts = {
        "format": ydl_format,
        "outtmpl": os.path.join(save_path, "%(title)s.%(ext)s"),
        "postprocessors": postprocessors,
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4" if fmt == "mp4" else None,
    }

    if extra_opts:
        opts.update(extra_opts)

    return opts


# ── Fetching info ─────────────────────────────────────────────────────────────

def fetch_info(url: str) -> VideoInfo:
    """Lấy thông tin video/playlist mà không tải xuống."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        raw = ydl.extract_info(url, download=False)

    info = VideoInfo(url=url)

    if raw.get("_type") == "playlist":
        info.is_playlist = True
        info.title = raw.get("title", "Playlist")
        entries = raw.get("entries", [])
        info.playlist_count = len(entries)
        info.entries = [
            {
                "url": e.get("url") or e.get("webpage_url") or f"https://www.youtube.com/watch?v={e.get('id')}",
                "title": e.get("title", f"Video {i+1}"),
                "duration": e.get("duration", 0),
                "thumbnail": e.get("thumbnail", ""),
            }
            for i, e in enumerate(entries) if e
        ]
        if entries:
            info.thumbnail = entries[0].get("thumbnail", "")
    else:
        info.title = raw.get("title", "")
        info.duration = raw.get("duration", 0)
        info.thumbnail = raw.get("thumbnail", "")
        info.uploader = raw.get("uploader", "")
        info.view_count = raw.get("view_count", 0)

    return info


# ── Download manager ──────────────────────────────────────────────────────────

class DownloadManager:
    """Quản lý hàng đợi tải, hỗ trợ tải song song."""

    MAX_WORKERS = 3

    def __init__(self, on_task_update: Callable[[DownloadTask], None]):
        self.on_task_update = on_task_update
        self._queue: list[DownloadTask] = []
        self._lock = threading.Lock()
        self._active = 0
        self._semaphore = threading.Semaphore(self.MAX_WORKERS)

    def add_task(self, task: DownloadTask):
        with self._lock:
            self._queue.append(task)
        threading.Thread(target=self._run_task, args=(task,), daemon=True).start()

    def _run_task(self, task: DownloadTask):
        self._semaphore.acquire()
        try:
            task.status = "downloading"
            self.on_task_update(task)

            def hook(d):
                if d["status"] == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                    downloaded = d.get("downloaded_bytes", 0)
                    speed = d.get("speed", 0) or 0
                    eta = d.get("eta", 0) or 0
                    if total > 0:
                        task.progress = downloaded / total * 100
                    task.speed = f"{speed/1024/1024:.1f} MB/s" if speed else "..."
                    task.eta = f"{int(eta)}s" if eta else "..."
                    self.on_task_update(task)
                elif d["status"] == "finished":
                    task.file_path = d.get("filename", "")

            opts = build_ydl_opts(task.save_path, task.fmt, task.quality, hook)
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([task.url])

            task.status = "done"
            task.progress = 100.0
            self.on_task_update(task)

        except Exception as e:
            task.status = "error"
            task.error = str(e)
            self.on_task_update(task)
        finally:
            self._semaphore.release()
