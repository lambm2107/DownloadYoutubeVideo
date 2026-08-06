import { Captions, Languages } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

export type SubtitleTrack = {
  code: string;
  label: string;
  auto?: boolean;
};

export const subtitleTracks: SubtitleTrack[] = [
  { code: "vi", label: "Tiếng Việt" },
  { code: "en", label: "English" },
  { code: "ja", label: "日本語", auto: true },
  { code: "ko", label: "한국어", auto: true },
  { code: "fr", label: "Français", auto: true },
];

export function SubtitleOptions({
  selected,
  onToggle,
  format,
  onFormatChange,
  burnIn,
  onBurnInChange,
  tracks = subtitleTracks,
}: {
  selected: string[];
  onToggle: (code: string) => void;
  format: string;
  onFormatChange: (value: string) => void;
  burnIn: boolean;
  onBurnInChange: (value: boolean) => void;
  tracks?: SubtitleTrack[];
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 rounded-xl border border-border bg-surface-2/40 px-4 py-3">
        <Languages className="size-4 text-primary" />
        <span className="text-xs text-muted-foreground">
          {selected.length > 0
            ? `Đã chọn ${selected.length} ngôn ngữ phụ đề`
            : "Chọn ngôn ngữ phụ đề muốn tải"}
        </span>
      </div>

      <div className="space-y-2">
        {tracks.map((track) => {
          const checked = selected.includes(track.code);
          return (
            <label
              key={track.code}
              className={cn(
                "flex cursor-pointer items-center justify-between gap-4 rounded-xl border px-4 py-3 transition-all",
                checked
                  ? "border-primary bg-primary/10"
                  : "border-border bg-surface-2/40 hover:border-primary/50",
              )}
            >
              <span className="flex items-center gap-3">
                <Checkbox
                  checked={checked}
                  onCheckedChange={() => onToggle(track.code)}
                  aria-label={track.label}
                />
                <span>
                  <span className="block text-sm font-semibold">{track.label}</span>
                  <span className="block text-xs text-muted-foreground">
                    {track.auto ? "Tự động tạo" : "Do tác giả tải lên"}
                  </span>
                </span>
              </span>
              <span className="font-mono text-xs uppercase text-muted-foreground">
                {track.code}
              </span>
            </label>
          );
        })}
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <div className="rounded-xl border border-border bg-surface-2/40 px-4 py-3">
          <span className="mb-2 flex items-center gap-1.5 text-xs text-muted-foreground">
            <Captions className="size-3.5" /> Định dạng tệp
          </span>
          <Select value={format} onValueChange={onFormatChange}>
            <SelectTrigger className="h-9 border-border bg-surface text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="srt">SRT · phổ biến nhất</SelectItem>
              <SelectItem value="vtt">WebVTT</SelectItem>
              <SelectItem value="txt">TXT · chỉ văn bản</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-border bg-surface-2/40 px-4 py-3">
          <span>
            <span className="block text-sm font-medium">Ghép phụ đề vào video</span>
            <span className="block text-xs text-muted-foreground">Xuất bản MP4 có sẵn phụ đề</span>
          </span>
          <Switch checked={burnIn} onCheckedChange={onBurnInChange} />
        </label>
      </div>
    </div>
  );
}
