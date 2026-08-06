import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  ArrowDownToLine,
  Captions,
  Clipboard,
  Eye,
  Film,
  FolderArchive,
  ListVideo,
  Link2,
  Loader2,
  Music4,
  Timer,
  Video,
  FolderOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { QualityOption, type Quality } from "@/components/downloader/QualityOption";
import { DownloadItem, type DownloadRow } from "@/components/downloader/DownloadItem";
import { SubtitleOptions, subtitleTracks } from "@/components/downloader/SubtitleOptions";
import { PlaylistPanel, playlistItems } from "@/components/downloader/PlaylistPanel";
import { AppSidebar, type ViewId } from "@/components/downloader/AppSidebar";
import { TitleBar } from "@/components/downloader/TitleBar";
import { useVidgrabCore } from "@/hooks/use-vidgrab-core";
import { core, CORE_URL } from "@/lib/vidgrab-core";
import thumb from "@/assets/video-thumb.jpg";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "VidGrab — Ứng dụng tải video, playlist và phụ đề YouTube" },
      {
        name: "description",
        content:
          "Ứng dụng tải video YouTube: dán link, chọn độ phân giải tới 4K, tách MP3, tải phụ đề nhiều ngôn ngữ và tải cả playlist.",
      },
      { property: "og:title", content: "VidGrab — Ứng dụng tải video, playlist và phụ đề YouTube" },
      {
        property: "og:description",
        content: "Dán link YouTube, chọn MP4 4K hoặc MP3, tải phụ đề SRT/VTT và tải hàng loạt cả playlist.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

const videoQualities: Quality[] = [
  { id: "2160", label: "2160p · 4K", detail: "MP4 · H.264 · 60fps", size: "1.82 GB", badge: "Cao nhất" },
  { id: "1440", label: "1440p · 2K", detail: "MP4 · H.264 · 60fps", size: "912 MB" },
  { id: "1080", label: "1080p Full HD", detail: "MP4 · H.264 · 30fps", size: "418 MB", badge: "Phổ biến" },
  { id: "720", label: "720p HD", detail: "MP4 · H.264 · 30fps", size: "196 MB" },
  { id: "360", label: "360p", detail: "MP4 · tiết kiệm dữ liệu", size: "74 MB" },
];

const audioQualities: Quality[] = [
  { id: "mp3-320", label: "MP3 · 320 kbps", detail: "Chất lượng studio", size: "11.4 MB", badge: "Tốt nhất" },
  { id: "mp3-192", label: "MP3 · 192 kbps", detail: "Cân bằng", size: "6.8 MB" },
  { id: "m4a", label: "M4A · 256 kbps", detail: "Gốc từ YouTube", size: "9.1 MB" },
];

const mockDownloads: DownloadRow[] = [
  {
    id: "1",
    title: "Lo-fi Coding Session — 3 giờ nhạc tập trung",
    format: "MP3 320kbps",
    size: "11.4 MB",
    progress: 100,
    status: "done",
  },
  {
    id: "2",
    title: "Hướng dẫn dựng phòng làm việc tại nhà 2026",
    format: "MP4 1080p + phụ đề VI",
    size: "418 MB",
    progress: 64,
    status: "downloading",
  },
  {
    id: "3",
    title: "Playlist: Setup phòng làm việc (6 video)",
    format: "MP4 1080p · ZIP",
    size: "1.86 GB",
    progress: 23,
    status: "paused",
  },
];

const mockHistory = [
  { id: "h1", title: "Review bàn phím cơ 2026", meta: "MP4 1080p · 312 MB · Hôm qua" },
  { id: "h2", title: "Podcast: Làm việc sâu", meta: "MP3 320kbps · 88 MB · 2 ngày trước" },
  { id: "h3", title: "Playlist: Nhạc tập trung (12 video)", meta: "MP3 · 402 MB · Tuần trước" },
];

function Index() {
  const [view, setView] = useState<ViewId>("download");
  const [url, setUrl] = useState("https://www.youtube.com/watch?v=aBc123XyZ");
  const [mode, setMode] = useState<"single" | "playlist">("single");
  const [videoQ, setVideoQ] = useState("1080");
  const [audioQ, setAudioQ] = useState("mp3-320");
  const [subs, setSubs] = useState<string[]>(["vi"]);
  const [subFormat, setSubFormat] = useState("srt");
  const [burnIn, setBurnIn] = useState(false);
  const [selectedItems, setSelectedItems] = useState<string[]>(playlistItems.map((i) => i.id));
  const [zip, setZip] = useState(true);
  const [autoStart, setAutoStart] = useState(true);
  const [notify, setNotify] = useState(true);
  const [tab, setTab] = useState("video");
  const [saveFolder, setSaveFolder] = useState("");

  const {
    status: coreStatus,
    health,
    analysis,
    analyzing,
    error: coreError,
    tasks,
    history: coreHistory,
    analyze,
    pauseTask,
    resumeTask,
    cancelTask,
  } = useVidgrabCore();
  const online = coreStatus === "online";

  // Sync save folder from health response
  const displayFolder = saveFolder || health?.dir || "/Downloads/VidGrab";

  const toggle = (list: string[], value: string) =>
    list.includes(value) ? list.filter((v) => v !== value) : [...list, value];

  const isPlaylist = mode === "playlist";

  const videoList = analysis?.videoFormats.length ? (analysis.videoFormats as Quality[]) : videoQualities;
  const audioList = analysis?.audioFormats.length ? (analysis.audioFormats as Quality[]) : audioQualities;
  const listItems = analysis?.items.length ? analysis.items : playlistItems;
  const preview = {
    title:
      analysis?.title ??
      (isPlaylist ? "Playlist: Setup phòng làm việc tại nhà" : "Hướng dẫn dựng phòng làm việc tại nhà 2026"),
    channel: analysis?.channel ?? "Studio Ánh Sáng",
    views: analysis?.views ?? "1,2 Tr lượt xem",
    duration: analysis?.duration ?? (isPlaylist ? "57:24 tổng" : "12:48"),
    badge: analysis
      ? analysis.kind === "playlist"
        ? `${analysis.items.length} video`
        : analysis.duration
      : isPlaylist
        ? "6 video"
        : "12:48",
    thumbnail: analysis?.thumbnail ?? thumb,
  };

  const queue: DownloadRow[] = useMemo(
    () =>
      online
        ? tasks.map((t) => ({
            id: t.id,
            title: t.title,
            format: t.format,
            size: t.size,
            progress: t.progress,
            status: t.status,
            message: t.message,
          }))
        : mockDownloads,
    [online, tasks],
  );

  const historyRows = online
    ? coreHistory.map((h) => ({
        id: h.id,
        title: h.title,
        meta: `${h.format} · ${h.size}${h.finishedAt ? ` · ${h.finishedAt.replace("T", " ")}` : ""}`,
      }))
    : mockHistory;

  const activeDownloads = queue.filter((q) => q.status === "downloading").length;
  const queueBadge = queue.filter((q) => q.status === "downloading" || q.status === "paused").length;

  const startDownload = async () => {
    if (!online) return;
    const isAudio = tab === "audio";
    await core.download({
      url,
      mode,
      kind: isAudio ? "audio" : "video",
      formatId: isAudio ? audioQ : videoQ,
      subtitles: subs,
      subtitleFormat: subFormat,
      burnIn,
      zip,
      items: isPlaylist
        ? selectedItems.map((id) => String(listItems.find((i) => i.id === id)?.index ?? id))
        : [],
    });
    setView("queue");
  };

  const pasteFromClipboard = async () => {
    try {
      setUrl(await navigator.clipboard.readText());
    } catch {
      /* trình duyệt chặn clipboard */
    }
  };

  const openFolder = async (folderPath?: string | null) => {
    const target = folderPath ?? displayFolder;
    if (!target) return;
    // Nếu chạy trong Electron: dùng native shell
    if (window.electronAPI) {
      await window.electronAPI.openFolder(target);
    } else {
      // Fallback web: gọi endpoint Python
      window.open(`${CORE_URL}/open-folder?path=${encodeURIComponent(target)}`, "_blank");
    }
  };

  return (
    <main className="flex min-h-screen items-stretch bg-background p-0 md:items-center md:justify-center md:p-6">
      <div className="glass-panel flex h-screen w-full flex-col overflow-hidden rounded-none md:h-[86vh] md:max-w-6xl md:rounded-2xl">
        <TitleBar title="VidGrab — Trình tải video" />

        <div className="flex min-h-0 flex-1 flex-col md:flex-row">
          <AppSidebar
            active={view}
            onChange={setView}
            queueBadge={queueBadge}
            speedLabel={online ? "Lõi Python sẵn sàng" : "Chưa kết nối"}
            freeLabel={health?.dir ? `Thư mục: …${health.dir.slice(-20)}` : "—"}
          />

          <div className="min-h-0 flex-1 overflow-y-auto p-4 md:p-6">
            {view === "download" && (
              <div className="mx-auto max-w-3xl space-y-4">
                {/* URL input block */}
                <div className="rounded-xl border border-border bg-surface-2/40 p-2.5">
                  <div className="mb-2.5 flex gap-1 rounded-xl bg-surface-2/60 p-1">
                    {(
                      [
                        { id: "single", label: "Video đơn", icon: Video },
                        { id: "playlist", label: "Playlist", icon: ListVideo },
                      ] as const
                    ).map((m) => (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => setMode(m.id)}
                        aria-pressed={mode === m.id}
                        className={
                          "flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-all " +
                          (mode === m.id
                            ? "bg-primary text-primary-foreground shadow-glow"
                            : "text-muted-foreground hover:text-foreground")
                        }
                      >
                        <m.icon className="size-3.5" />
                        {m.label}
                      </button>
                    ))}
                  </div>

                  <div className="flex flex-col gap-2.5 sm:flex-row">
                    <div className="relative flex-1">
                      <Link2 className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        aria-label="Liên kết video YouTube"
                        placeholder={
                          isPlaylist ? "Dán liên kết playlist YouTube..." : "Dán liên kết YouTube tại đây..."
                        }
                        className="h-12 border-transparent bg-surface-2/60 pl-10 pr-24 font-mono text-sm focus-visible:border-primary"
                      />
                      <button
                        type="button"
                        onClick={() => void pasteFromClipboard()}
                        className="absolute right-2 top-1/2 flex -translate-y-1/2 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                      >
                        <Clipboard className="size-3.5" />
                        Dán
                      </button>
                    </div>
                    <Button
                      size="lg"
                      disabled={analyzing || !online}
                      onClick={() => void analyze(url, mode)}
                      className="h-12 gap-2 px-6 shadow-glow"
                    >
                      {analyzing ? <Loader2 className="size-4 animate-spin" /> : <ArrowDownToLine className="size-4" />}
                      {analyzing ? "Đang phân tích" : "Phân tích"}
                    </Button>
                  </div>

                  {!online && (
                    <p className="mt-2 px-1 text-xs text-muted-foreground">
                      Chưa kết nối lõi Python — đang hiển thị dữ liệu mẫu. Chạy{" "}
                      <code className="font-mono">python python-core/main.py</code> để bật.
                    </p>
                  )}
                  {coreError && <p className="mt-2 px-1 text-xs text-destructive">{coreError}</p>}
                </div>

                {/* Video preview + format selection block */}
                <div className="overflow-hidden rounded-2xl border border-border bg-surface/60">
                  <div className="grid gap-0 md:grid-cols-[280px_1fr]">
                    <div className="relative">
                      <img
                        src={preview.thumbnail}
                        alt="Ảnh xem trước video được phân tích"
                        width={1280}
                        height={720}
                        className="h-44 w-full object-cover md:h-full"
                      />
                      <span className="absolute bottom-2 right-2 rounded-md bg-background/85 px-1.5 py-0.5 font-mono text-[11px]">
                        {preview.badge}
                      </span>
                    </div>

                    <div className="p-5">
                      <h2 className="text-base font-semibold leading-snug">{preview.title}</h2>

                      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                        <span>{preview.channel}</span>
                        <span className="flex items-center gap-1"><Eye className="size-3.5" /> {preview.views}</span>
                        <span className="flex items-center gap-1"><Timer className="size-3.5" /> {preview.duration}</span>
                      </div>

                      <Tabs
                        value={tab}
                        onValueChange={setTab}
                        defaultValue={isPlaylist ? "playlist" : "video"}
                        className="mt-5"
                      >
                        <TabsList className={"grid w-full bg-surface-2/60 " + (isPlaylist ? "grid-cols-4" : "grid-cols-3")}>
                          <TabsTrigger value="video" className="gap-1.5 text-xs">
                            <Film className="size-3.5" /> Video
                          </TabsTrigger>
                          <TabsTrigger value="audio" className="gap-1.5 text-xs">
                            <Music4 className="size-3.5" /> Âm thanh
                          </TabsTrigger>
                          <TabsTrigger value="subs" className="gap-1.5 text-xs">
                            <Captions className="size-3.5" /> Phụ đề
                          </TabsTrigger>
                          {isPlaylist && (
                            <TabsTrigger value="playlist" className="gap-1.5 text-xs">
                              <ListVideo className="size-3.5" /> Danh sách
                            </TabsTrigger>
                          )}
                        </TabsList>

                        <TabsContent value="video" className="mt-3 space-y-2">
                          {videoList.map((q) => (
                            <QualityOption key={q.id} quality={q} selected={videoQ === q.id} onSelect={setVideoQ} />
                          ))}
                        </TabsContent>

                        <TabsContent value="audio" className="mt-3 space-y-2">
                          {audioList.map((q) => (
                            <QualityOption key={q.id} quality={q} selected={audioQ === q.id} onSelect={setAudioQ} />
                          ))}
                        </TabsContent>

                        <TabsContent value="subs" className="mt-3">
                          <SubtitleOptions
                            selected={subs}
                            onToggle={(code) => setSubs((s) => toggle(s, code))}
                            format={subFormat}
                            onFormatChange={setSubFormat}
                            burnIn={burnIn}
                            onBurnInChange={setBurnIn}
                            tracks={analysis?.subtitles.length ? analysis.subtitles : subtitleTracks}
                          />
                        </TabsContent>

                        {isPlaylist && (
                          <TabsContent value="playlist" className="mt-3">
                            <PlaylistPanel
                              items={listItems}
                              selected={selectedItems}
                              onToggle={(id) => setSelectedItems((s) => toggle(s, id))}
                              onSelectAll={() => setSelectedItems(listItems.map((i) => i.id))}
                              onClear={() => setSelectedItems([])}
                            />
                          </TabsContent>
                        )}
                      </Tabs>

                      {isPlaylist && (
                        <label className="mt-3 flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-border bg-surface-2/40 px-4 py-3">
                          <span className="flex items-center gap-2">
                            <FolderArchive className="size-4 text-primary" />
                            <span>
                              <span className="block text-sm font-medium">Nén thành một tệp ZIP</span>
                              <span className="block text-xs text-muted-foreground">Gói toàn bộ video đã chọn vào một lần tải</span>
                            </span>
                          </span>
                          <Switch checked={zip} onCheckedChange={setZip} />
                        </label>
                      )}

                      <Button
                        onClick={() => void startDownload()}
                        disabled={!online}
                        className="mt-4 h-11 w-full gap-2 shadow-glow"
                      >
                        <ArrowDownToLine className="size-4" />
                        {isPlaylist ? `Tải ${selectedItems.length} video đã chọn` : "Tải xuống ngay"}
                      </Button>

                      {subs.length > 0 && (
                        <p className="mt-2 text-center text-xs text-muted-foreground">
                          Kèm {subs.length} phụ đề · <span className="uppercase">{subFormat}</span>
                          {burnIn ? " · ghép sẵn vào video" : ""}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {view === "queue" && (
              <div className="mx-auto max-w-3xl">
                <div className="mb-2.5 flex items-end justify-between">
                  <h2 className="text-sm font-semibold">Hàng đợi tải xuống</h2>
                  <button
                    onClick={() => void core.clearDone().catch(() => undefined)}
                    className="text-xs text-muted-foreground transition-colors hover:text-foreground"
                  >
                    Xóa mục đã xong
                  </button>
                </div>
                <ul className="space-y-2.5">
                  {queue.length === 0 && (
                    <li className="rounded-xl border border-border bg-surface-2/40 px-4 py-6 text-center text-xs text-muted-foreground">
                      Hàng đợi trống
                    </li>
                  )}
                  {queue.map((d) => (
                    <DownloadItem
                      key={d.id}
                      item={d}
                      onPause={online ? pauseTask : undefined}
                      onResume={online ? resumeTask : undefined}
                      onCancel={online ? cancelTask : undefined}
                    />
                  ))}
                </ul>
              </div>
            )}

            {view === "history" && (
              <div className="mx-auto max-w-3xl">
                <h2 className="mb-2.5 text-sm font-semibold">Lịch sử tải xuống</h2>
                <ul className="divide-y divide-border overflow-hidden rounded-xl border border-border bg-surface/60">
                  {historyRows.length === 0 && (
                    <li className="px-4 py-6 text-center text-xs text-muted-foreground">Chưa có lịch sử</li>
                  )}
                  {historyRows.map((h) => (
                    <li key={h.id} className="flex items-center justify-between gap-3 px-4 py-3">
                      <span>
                        <span className="block text-sm font-medium">{h.title}</span>
                        <span className="block text-xs text-muted-foreground">{h.meta}</span>
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="gap-1.5 text-xs"
                        onClick={() => openFolder(health?.dir)}
                      >
                        <FolderOpen className="size-3.5" />
                        Mở thư mục
                      </Button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {view === "settings" && (
              <div className="mx-auto max-w-3xl space-y-2.5">
                <h2 className="mb-2.5 text-sm font-semibold">Cài đặt</h2>

                <div className="rounded-xl border border-border bg-surface/60 px-4 py-3">
                  <span className="block text-sm font-medium">Thư mục lưu</span>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    Đặt biến môi trường <code className="font-mono">VIDGRAB_DIR</code> khi chạy server để thay đổi.
                  </p>
                  <div className="mt-2 flex gap-2">
                    <Input
                      readOnly
                      value={displayFolder}
                      aria-label="Thư mục lưu hiện tại"
                      className="h-9 bg-surface-2/60 font-mono text-xs"
                    />
                    <Button
                      variant="secondary"
                      size="sm"
                      className="gap-1.5"
                      onClick={() => openFolder(health?.dir)}
                    >
                      <FolderOpen className="size-3.5" />
                      Mở
                    </Button>
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-surface/60 px-4 py-3">
                  <span className="block text-sm font-medium">Thông tin lõi Python</span>
                  {online && health ? (
                    <ul className="mt-2 space-y-1 font-mono text-xs text-muted-foreground">
                      <li>Phiên bản: {health.version}</li>
                      <li>Luồng tải tối đa: {health.workers}</li>
                      <li className="break-all">Thư mục: {health.dir}</li>
                    </ul>
                  ) : (
                    <p className="mt-1 text-xs text-muted-foreground">
                      Chưa kết nối — chạy <code className="font-mono">python python-core/main.py</code>
                    </p>
                  )}
                </div>

                <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-border bg-surface/60 px-4 py-3">
                  <span>
                    <span className="block text-sm font-medium">Tự động bắt đầu tải</span>
                    <span className="block text-xs text-muted-foreground">Bắt đầu ngay khi thêm vào hàng đợi</span>
                  </span>
                  <Switch checked={autoStart} onCheckedChange={setAutoStart} />
                </label>

                <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-border bg-surface/60 px-4 py-3">
                  <span>
                    <span className="block text-sm font-medium">Thông báo khi hoàn tất</span>
                    <span className="block text-xs text-muted-foreground">Hiển thị thông báo hệ thống</span>
                  </span>
                  <Switch checked={notify} onCheckedChange={setNotify} />
                </label>
              </div>
            )}
          </div>
        </div>

        <div className="flex h-8 shrink-0 items-center justify-between border-t border-border bg-surface-2/50 px-3 text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className={"size-1.5 rounded-full " + (online ? "bg-success" : "bg-muted-foreground")} />
            {online ? "Lõi Python sẵn sàng" : "Chưa kết nối lõi Python"}
          </span>
          <span>
            {activeDownloads} tác vụ đang chạy · VidGrab {health?.version ?? "1.4.0"}
          </span>
        </div>
      </div>
    </main>
  );
}
