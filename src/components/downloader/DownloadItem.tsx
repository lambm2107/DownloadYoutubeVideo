import { CheckCircle2, Download, Pause, Play, X, AlertCircle } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";

export type DownloadRow = {
  id: string;
  title: string;
  format: string;
  size: string;
  progress: number;
  status: "downloading" | "done" | "paused" | "error";
  message?: string | null;
};

const statusMeta: Record<
  DownloadRow["status"],
  { label: string; icon: typeof Download }
> = {
  downloading: { label: "Đang tải", icon: Download },
  done: { label: "Hoàn tất", icon: CheckCircle2 },
  paused: { label: "Tạm dừng", icon: Pause },
  error: { label: "Lỗi", icon: AlertCircle },
};

export function DownloadItem({
  item,
  onPause,
  onResume,
  onCancel,
}: {
  item: DownloadRow;
  onPause?: (id: string) => void;
  onResume?: (id: string) => void;
  onCancel?: (id: string) => void;
}) {
  const meta = statusMeta[item.status];
  const Icon = meta.icon;
  const isDone = item.status === "done";
  const isError = item.status === "error";

  return (
    <li className="rounded-xl border border-border bg-surface-2/40 p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{item.title}</p>
          <p className="mt-1 font-mono text-xs text-muted-foreground">
            {item.format} · {item.size}
          </p>
          {isError && item.message && (
            <p className="mt-1 text-xs text-destructive line-clamp-2">{item.message}</p>
          )}
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <span
            className={
              "flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium " +
              (isDone
                ? "bg-success/15 text-success"
                : isError
                  ? "bg-destructive/15 text-destructive"
                  : item.status === "paused"
                    ? "bg-muted text-muted-foreground"
                    : "bg-primary/15 text-primary")
            }
          >
            <Icon className="size-3.5" />
            {meta.label}
          </span>

          {/* Control buttons — only when online (callbacks provided) */}
          {!isDone && (
            <div className="flex items-center gap-1">
              {item.status === "downloading" && onPause && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-7"
                  title="Tạm dừng"
                  onClick={() => onPause(item.id)}
                >
                  <Pause className="size-3.5" />
                </Button>
              )}
              {item.status === "paused" && onResume && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-7 text-primary"
                  title="Tiếp tục"
                  onClick={() => onResume(item.id)}
                >
                  <Play className="size-3.5" />
                </Button>
              )}
              {onCancel && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-7 text-muted-foreground hover:text-destructive"
                  title="Hủy"
                  onClick={() => onCancel(item.id)}
                >
                  <X className="size-3.5" />
                </Button>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="mt-3 flex items-center gap-3">
        <Progress
          value={item.progress}
          className={
            "h-1.5 " +
            (isError ? "bg-muted [&>div]:bg-destructive" : "bg-muted")
          }
        />
        <span className="w-10 shrink-0 text-right font-mono text-xs text-muted-foreground">
          {item.progress}%
        </span>
      </div>
    </li>
  );
}
