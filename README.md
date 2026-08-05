# YouTube Video Downloader

App tải video YouTube với giao diện đồ họa (GUI), hỗ trợ nhiều định dạng và chất lượng.

## Tính năng

- Tải video YouTube theo URL
- Hỗ trợ định dạng: **MP4**, **MP3**, **WebM**, **M4A**
- Chọn chất lượng: Tốt nhất, 1080p, 720p, 480p, 360p, 240p
- Hiển thị tiến trình tải (thanh progress + tốc độ + ETA)
- Chọn thư mục lưu tùy ý
- Giao diện tối (dark theme)

## Yêu cầu

- Python 3.8+
- `yt-dlp` (tự động cài khi chạy lần đầu)
- `ffmpeg` (cần thiết cho MP3 và merge video/audio)

## Cài đặt & Chạy

```bash
# Cài dependency
pip install -r requirements.txt

# Chạy app
python app.py
```

## Cài ffmpeg (cần cho MP3 và video chất lượng cao)

**Windows:**
1. Tải tại https://ffmpeg.org/download.html
2. Giải nén và thêm vào PATH, hoặc đặt `ffmpeg.exe` cùng thư mục với `app.py`

Hoặc cài nhanh qua `winget`:
```bash
winget install ffmpeg
```

## Ghi chú

App sử dụng thư viện `yt-dlp` — phiên bản cải tiến và được cập nhật thường xuyên hơn `youtube-dl`.
