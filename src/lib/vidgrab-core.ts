/**
 * Client cho lõi Python (FastAPI + yt-dlp) của VidGrab.
 * Toàn bộ lời gọi đều chạy phía trình duyệt, có fallback khi lõi chưa bật.
 */

export const CORE_URL =
  (import.meta.env["VITE_VIDGRAB_CORE"] as string | undefined) ?? "http://127.0.0.1:8000";

export type CoreFormat = {
  id: string;
  label: string;
  detail: string;
  size: string;
  badge?: string | null;
};

export type CorePlaylistEntry = {
  id: string;
  index: number;
  title: string;
  duration: string;
  size: string;
};

export type CoreAnalysis = {
  kind: "single" | "playlist";
  title: string;
  channel: string;
  duration: string;
  views: string;
  thumbnail?: string | null;
  videoFormats: CoreFormat[];
  audioFormats: CoreFormat[];
  subtitles: { code: string; label: string }[];
  items: CorePlaylistEntry[];
};

export type CoreTask = {
  id: string;
  title: string;
  format: string;
  size: string;
  progress: number;
  status: "downloading" | "done" | "paused" | "error";
  message?: string | null;
  finishedAt?: string | null;
};

export type DownloadPayload = {
  url: string;
  mode: "single" | "playlist";
  kind: "video" | "audio";
  formatId: string;
  subtitles: string[];
  subtitleFormat: string;
  burnIn: boolean;
  zip: boolean;
  items: string[];
};

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${CORE_URL}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(detail || `Lõi Python trả về ${res.status}`);
  }
  return (await res.json()) as T;
}

export type CoreHealth = {
  ok: boolean;
  version: string;
  dir: string;
  workers: number;
};

export type CoreStats = {
  downloadingCount: number;
  totalCount: number;
  dir: string;
};

// Map from taskId → original DownloadPayload (needed for resume)
const _payloadRegistry = new Map<string, DownloadPayload>();

export const core = {
  health: () => call<CoreHealth>("/health"),
  analyze: (url: string, mode: "single" | "playlist") =>
    call<CoreAnalysis>("/analyze", { method: "POST", body: JSON.stringify({ url, mode }) }),
  download: async (payload: DownloadPayload) => {
    const task = await call<CoreTask>("/download", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    _payloadRegistry.set(task.id, payload);
    return task;
  },
  tasks: () => call<CoreTask[]>("/tasks"),
  history: () => call<CoreTask[]>("/history"),
  clearDone: () => call<{ removed: number }>("/tasks/clear-done", { method: "POST" }),
  cancel: (id: string) => {
    _payloadRegistry.delete(id);
    return call<{ ok: boolean }>(`/tasks/${id}`, { method: "DELETE" });
  },
  pause: (id: string) => call<CoreTask>(`/tasks/${id}/pause`, { method: "POST" }),
  resume: (id: string) => {
    const payload = _payloadRegistry.get(id);
    if (!payload) return Promise.reject(new Error("Không tìm thấy dữ liệu tác vụ để tiếp tục"));
    return call<CoreTask>(`/tasks/${id}/resume`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getPayload: (id: string) => _payloadRegistry.get(id) ?? null,
};
