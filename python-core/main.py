"""VidGrab Python core.

FastAPI + yt-dlp backend that powers the VidGrab UI.

Run:
    pip install -r requirements.txt
    python main.py            # http://127.0.0.1:8000
"""

from __future__ import annotations

import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import platform
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from yt_dlp import YoutubeDL

DOWNLOAD_DIR = Path(os.environ.get("VIDGRAB_DIR", Path.home() / "Downloads" / "VidGrab"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_WORKERS = int(os.environ.get("VIDGRAB_WORKERS", "3"))

app = FastAPI(title="VidGrab Core", version="1.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #


class AnalyzeRequest(BaseModel):
    url: str
    mode: Literal["single", "playlist"] = "single"


class Format(BaseModel):
    id: str
    label: str
    detail: str
    size: str
    badge: str | None = None


class PlaylistEntry(BaseModel):
    id: str
    index: int
    title: str
    duration: str
    size: str


class AnalyzeResponse(BaseModel):
    kind: Literal["single", "playlist"]
    title: str
    channel: str
    duration: str
    views: str
    thumbnail: str | None = None
    videoFormats: list[Format] = Field(default_factory=list)
    audioFormats: list[Format] = Field(default_factory=list)
    subtitles: list[dict[str, str]] = Field(default_factory=list)
    items: list[PlaylistEntry] = Field(default_factory=list)


class DownloadRequest(BaseModel):
    url: str
    mode: Literal["single", "playlist"] = "single"
    kind: Literal["video", "audio"] = "video"
    formatId: str = "1080"
    subtitles: list[str] = Field(default_factory=list)
    subtitleFormat: str = "srt"
    burnIn: bool = False
    zip: bool = False
    items: list[str] = Field(default_factory=list)


class Task(BaseModel):
    id: str
    title: str
    format: str
    size: str
    progress: int = 0
    status: Literal["downloading", "done", "paused", "error"] = "downloading"
    message: str | None = None
    finishedAt: str | None = None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def human_size(num: float | None) -> str:
    if not num:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024:
            return f"{num:.1f} {unit}".replace(".0 ", " ")
        num /= 1024
    return f"{num:.1f} PB"


def human_time(seconds: float | None) -> str:
    if not seconds:
        return "—"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def human_views(count: int | None) -> str:
    if not count:
        return "—"
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f} Tr lượt xem"
    if count >= 1_000:
        return f"{count / 1_000:.1f} N lượt xem"
    return f"{count} lượt xem"


def build_video_formats(info: dict[str, Any]) -> list[Format]:
    seen: dict[int, Format] = {}
    for f in info.get("formats", []):
        height = f.get("height")
        if not height or f.get("vcodec") == "none":
            continue
        size = f.get("filesize") or f.get("filesize_approx")
        fps = f.get("fps")
        label = {2160: "2160p · 4K", 1440: "1440p · 2K", 1080: "1080p Full HD", 720: "720p HD"}.get(
            height, f"{height}p"
        )
        badge = "Cao nhất" if height >= 2160 else "Phổ biến" if height == 1080 else None
        candidate = Format(
            id=str(height),
            label=label,
            detail=f"{(f.get('ext') or 'mp4').upper()} · {f.get('vcodec', 'h264').split('.')[0]}"
            + (f" · {int(fps)}fps" if fps else ""),
            size=human_size(size),
            badge=badge,
        )
        if height not in seen or seen[height].size == "—":
            seen[height] = candidate
    return [seen[h] for h in sorted(seen, reverse=True)]


def build_audio_formats(info: dict[str, Any]) -> list[Format]:
    best = None
    for f in info.get("formats", []):
        if f.get("acodec") and f.get("acodec") != "none" and f.get("vcodec") == "none":
            if best is None or (f.get("abr") or 0) > (best.get("abr") or 0):
                best = f
    approx = (best or {}).get("filesize") or (best or {}).get("filesize_approx")
    duration = info.get("duration") or 0
    return [
        Format(
            id="mp3-320",
            label="MP3 · 320 kbps",
            detail="Chất lượng studio",
            size=human_size(duration * 40_000),
            badge="Tốt nhất",
        ),
        Format(id="mp3-192", label="MP3 · 192 kbps", detail="Cân bằng", size=human_size(duration * 24_000)),
        Format(id="m4a", label="M4A · gốc", detail="Không chuyển mã", size=human_size(approx)),
    ]


def build_subtitles(info: dict[str, Any]) -> list[dict[str, str]]:
    langs: dict[str, str] = {}
    for source in (info.get("subtitles") or {}, info.get("automatic_captions") or {}):
        for code, tracks in source.items():
            name = (tracks or [{}])[0].get("name") or code
            langs.setdefault(code, name)
    return [{"code": c, "label": n} for c, n in sorted(langs.items())][:40]


def format_selector(req: DownloadRequest) -> str:
    if req.kind == "audio":
        return "bestaudio/best"
    height = "".join(ch for ch in req.formatId if ch.isdigit()) or "1080"
    return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"


# --------------------------------------------------------------------------- #
# Task registry
# --------------------------------------------------------------------------- #

_tasks: dict[str, Task] = {}
_paused: set[str] = set()
_cancelled: set[str] = set()
_history: list[Task] = []
_lock = threading.Lock()
_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)


class Paused(Exception):
    pass


class Cancelled(Exception):
    pass


def _hook(task_id: str):
    def hook(d: dict[str, Any]) -> None:
        with _lock:
            task = _tasks.get(task_id)
            if task is None or task_id in _cancelled:
                raise Cancelled()
            if task_id in _paused:
                task.status = "paused"
                raise Paused()
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done = d.get("downloaded_bytes") or 0
                task.status = "downloading"
                task.progress = int(done / total * 100) if total else task.progress
                if total:
                    task.size = human_size(total)
            elif d.get("status") == "finished":
                task.progress = 100

    return hook


def _run_download(task_id: str, req: DownloadRequest) -> None:
    opts: dict[str, Any] = {
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
        "progress_hooks": [_hook(task_id)],
        "noplaylist": req.mode == "single",
        "format": format_selector(req),
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
    }
    if req.kind == "audio":
        bitrate = "320" if req.formatId.endswith("320") else "192"
        if req.formatId != "m4a":
            opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": bitrate}
            ]
    if req.subtitles:
        opts.update(
            writesubtitles=True,
            writeautomaticsub=True,
            subtitleslangs=req.subtitles,
            subtitlesformat=req.subtitleFormat,
        )
        if req.burnIn:
            opts.setdefault("postprocessors", []).append({"key": "FFmpegEmbedSubtitle"})
    if req.mode == "playlist" and req.items:
        opts["playlist_items"] = ",".join(req.items)

    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([req.url])
    except Paused:
        return
    except Cancelled:
        with _lock:
            _tasks.pop(task_id, None)
        return
    except Exception as exc:  # noqa: BLE001 - surfaced to the UI
        with _lock:
            task = _tasks.get(task_id)
            if task:
                task.status = "error"
                task.message = str(exc)[:200]
        return

    with _lock:
        task = _tasks.get(task_id)
        if task:
            task.status = "done"
            task.progress = 100
            task.finishedAt = datetime.now().isoformat(timespec="seconds")
            _history.insert(0, task.model_copy())


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "version": app.version, "dir": str(DOWNLOAD_DIR), "workers": MAX_WORKERS}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": req.mode == "single",
        "extract_flat": "in_playlist" if req.mode == "playlist" else False,
    }
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(req.url, download=False)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Không phân tích được liên kết: {exc}") from exc

    if info.get("_type") == "playlist":
        entries = [e for e in (info.get("entries") or []) if e]
        total = sum(e.get("duration") or 0 for e in entries)
        return AnalyzeResponse(
            kind="playlist",
            title=info.get("title") or "Playlist",
            channel=info.get("uploader") or info.get("channel") or "—",
            duration=f"{human_time(total)} tổng",
            views=f"{len(entries)} video",
            thumbnail=(entries[0].get("thumbnails") or [{}])[0].get("url") if entries else None,
            items=[
                PlaylistEntry(
                    id=str(e.get("id") or i + 1),
                    index=i + 1,
                    title=e.get("title") or f"Video {i + 1}",
                    duration=human_time(e.get("duration")),
                    size=human_size(e.get("filesize_approx")),
                )
                for i, e in enumerate(entries)
            ],
        )

    return AnalyzeResponse(
        kind="single",
        title=info.get("title") or "Video",
        channel=info.get("uploader") or info.get("channel") or "—",
        duration=human_time(info.get("duration")),
        views=human_views(info.get("view_count")),
        thumbnail=info.get("thumbnail"),
        videoFormats=build_video_formats(info),
        audioFormats=build_audio_formats(info),
        subtitles=build_subtitles(info),
    )


@app.post("/download", response_model=Task)
def download(req: DownloadRequest) -> Task:
    task_id = uuid.uuid4().hex[:8]
    label = (
        f"MP3 {req.formatId.split('-')[-1]}kbps"
        if req.kind == "audio"
        else f"MP4 {req.formatId}p" + (f" + phụ đề {','.join(req.subtitles).upper()}" if req.subtitles else "")
    )
    task = Task(id=task_id, title=req.url, format=label, size="—")
    with _lock:
        _tasks[task_id] = task
    _pool.submit(_run_download, task_id, req)
    return task


@app.get("/tasks", response_model=list[Task])
def tasks() -> list[Task]:
    with _lock:
        return list(_tasks.values())


@app.post("/tasks/{task_id}/pause", response_model=Task)
def pause(task_id: str) -> Task:
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            raise HTTPException(404, "Không tìm thấy tác vụ")
        _paused.add(task_id)
        task.status = "paused"
        return task


@app.post("/tasks/{task_id}/resume", response_model=Task)
def resume(task_id: str, req: DownloadRequest) -> Task:
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            raise HTTPException(404, "Không tìm thấy tác vụ")
        _paused.discard(task_id)
        task.status = "downloading"
    _pool.submit(_run_download, task_id, req)
    return task


@app.delete("/tasks/{task_id}")
def cancel(task_id: str) -> dict[str, bool]:
    with _lock:
        _cancelled.add(task_id)
        _tasks.pop(task_id, None)
    return {"ok": True}


@app.post("/tasks/clear-done")
def clear_done() -> dict[str, int]:
    with _lock:
        done = [t for t in _tasks.values() if t.status == "done"]
        for t in done:
            _tasks.pop(t.id, None)
    return {"removed": len(done)}


@app.get("/history", response_model=list[Task])
def history() -> list[Task]:
    with _lock:
        return list(_history)


@app.get("/open-folder")
def open_folder(path: str | None = None) -> JSONResponse:
    """Open a folder in the system file explorer (best-effort)."""
    target = Path(path or DOWNLOAD_DIR).resolve()
    if not target.exists():
        target = DOWNLOAD_DIR
    try:
        system = platform.system()
        if system == "Windows":
            subprocess.Popen(["explorer", str(target)])
        elif system == "Darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
    except Exception:  # noqa: BLE001
        pass
    return JSONResponse({"ok": True, "path": str(target)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8000")))
