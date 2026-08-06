import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export type Quality = {
  id: string;
  label: string;
  detail: string;
  size: string;
  badge?: string;
};

export function QualityOption({
  quality,
  selected,
  onSelect,
}: {
  quality: Quality;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(quality.id)}
      aria-pressed={selected}
      className={cn(
        "group flex w-full items-center justify-between gap-4 rounded-xl border px-4 py-3 text-left transition-all",
        selected
          ? "border-primary bg-primary/10 shadow-glow"
          : "border-border bg-surface-2/40 hover:border-primary/50 hover:bg-surface-2",
      )}
    >
      <div className="flex items-center gap-3">
        <span
          className={cn(
            "flex size-5 items-center justify-center rounded-full border transition-colors",
            selected ? "border-primary bg-primary" : "border-muted-foreground/50",
          )}
        >
          {selected && <Check className="size-3 text-primary-foreground" strokeWidth={3} />}
        </span>
        <span>
          <span className="block text-sm font-semibold">{quality.label}</span>
          <span className="block text-xs text-muted-foreground">{quality.detail}</span>
        </span>
      </div>
      <div className="flex items-center gap-2">
        {quality.badge && (
          <span className="rounded-full bg-accent/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-accent">
            {quality.badge}
          </span>
        )}
        <span className="font-mono text-xs text-muted-foreground">{quality.size}</span>
      </div>
    </button>
  );
}
