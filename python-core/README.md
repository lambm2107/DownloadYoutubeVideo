# VidGrab Python Core

Lõi xử lý bằng Python (FastAPI + yt-dlp) cho giao diện VidGrab.

## Cài đặt

```bash
cd python-core
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Cần cài thêm **ffmpeg** trên máy (ghép video/âm thanh, tách MP3, ghép phụ đề).

## Chạy

```bash
python main.py        # http://127.0.0.1:8000
```

Biến môi trường:

| Biến | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `VIDGRAB_DIR` | `~/Downloads/VidGrab` | Thư mục lưu tệp |
| `VIDGRAB_WORKERS` | `3` | Số tác vụ tải song song |
| `PORT` | `8000` | Cổng API |

## API

| Method | Đường dẫn | Mô tả |
| --- | --- | --- |
| GET | `/health` | Kiểm tra lõi đang chạy |
| POST | `/analyze` | Phân tích link video/playlist |
| POST | `/download` | Thêm tác vụ tải |
| GET | `/tasks` | Hàng đợi + tiến trình |
| POST | `/tasks/{id}/pause` · `/resume` | Tạm dừng / tiếp tục |
| DELETE | `/tasks/{id}` | Hủy tác vụ |
| POST | `/tasks/clear-done` | Xóa mục đã xong |
| GET | `/history` | Lịch sử tải |

## Kết nối với giao diện

Giao diện đọc địa chỉ lõi từ `VITE_VIDGRAB_CORE` (mặc định `http://127.0.0.1:8000`).
Khi không tìm thấy lõi Python, giao diện tự chuyển sang dữ liệu mẫu để vẫn xem được.
