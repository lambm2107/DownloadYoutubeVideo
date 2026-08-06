import { ListVideo } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type PlaylistItem = {
  id: string;
  index: number;
  title: string;
  duration: string;
  size: string;
};

export const playlistItems: PlaylistItem[] = [
  {
    id: "p1",
    index: 1,
    title: "Giới thiệu series: chọn bàn và ghế",
    duration: "08:12",
    size: "268 MB",
  },
  { id: "p2", index: 2, title: "Bố trí ánh sáng cho góc quay", duration: "11:35", size: "382 MB" },
  { id: "p3", index: 3, title: "Đi dây gọn gàng dưới mặt bàn", duration: "09:47", size: "311 MB" },
  {
    id: "p4",
    index: 4,
    title: "Thiết lập âm thanh: micro và tiêu âm",
    duration: "14:03",
    size: "460 MB",
  },
  {
    id: "p5",
    index: 5,
    title: "Tối ưu màn hình và độ cao mắt nhìn",
    duration: "07:29",
    size: "241 MB",
  },
  {
    id: "p6",
    index: 6,
    title: "Tổng kết và danh sách thiết bị",
    duration: "06:18",
    size: "203 MB",
  },
];

export function PlaylistPanel({
  selected,
  onToggle,
  onSelectAll,
  onClear,
  items = playlistItems,
}: {
  selected: string[];
  onToggle: (id: string) => void;
  onSelectAll: () => void;
  onClear: () => void;
  items?: PlaylistItem[];
}) {
  const allSelected = selected.length === items.length;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border bg-surface-2/40 px-4 py-3">
        <span className="flex items-center gap-2 text-xs text-muted-foreground">
          <ListVideo className="size-4 text-primary" />
          Đã chọn {selected.length}/{items.length} video
        </span>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs"
            onClick={allSelected ? onClear : onSelectAll}
          >
            {allSelected ? "Bỏ chọn tất cả" : "Chọn tất cả"}
          </Button>
        </div>
      </div>

      <ul className="max-h-72 space-y-2 overflow-y-auto pr-1">
        {items.map((item) => {
          const checked = selected.includes(item.id);
          return (
            <li key={item.id}>
              <label
                className={cn(
                  "flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 transition-all",
                  checked
                    ? "border-primary bg-primary/10"
                    : "border-border bg-surface-2/40 hover:border-primary/50",
                )}
              >
                <Checkbox
                  checked={checked}
                  onCheckedChange={() => onToggle(item.id)}
                  aria-label={item.title}
                />
                <span className="w-5 shrink-0 font-mono text-xs text-muted-foreground">
                  {String(item.index).padStart(2, "0")}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium">{item.title}</span>
                  <span className="block font-mono text-xs text-muted-foreground">
                    {item.duration} · {item.size}
                  </span>
                </span>
              </label>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
