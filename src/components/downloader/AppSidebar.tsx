import { ArrowDownToLine, ListChecks, Settings, History, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export type ViewId = "download" | "queue" | "history" | "settings";

type NavItem = { id: ViewId; label: string; icon: LucideIcon };

const items: NavItem[] = [
  { id: "download", label: "Tải xuống", icon: ArrowDownToLine },
  { id: "queue", label: "Hàng đợi", icon: ListChecks },
  { id: "history", label: "Lịch sử", icon: History },
  { id: "settings", label: "Cài đặt", icon: Settings },
];

export function AppSidebar({
  active,
  onChange,
  queueBadge = 0,
  speedLabel,
  freeLabel,
}: {
  active: ViewId;
  onChange: (id: ViewId) => void;
  queueBadge?: number;
  speedLabel?: string;
  freeLabel?: string;
}) {
  return (
    <nav
      aria-label="Điều hướng ứng dụng"
      className="flex shrink-0 flex-row gap-1 border-b border-border bg-surface/50 p-2 md:w-52 md:flex-col md:border-b-0 md:border-r md:p-3"
    >
      <div className="mb-2 hidden items-center gap-2 px-2 pt-1 md:flex">
        <span className="flex size-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <ArrowDownToLine className="size-4" />
        </span>
        <span className="text-sm font-semibold tracking-tight">VidGrab</span>
      </div>

      {items.map((it) => {
        const badge = it.id === "queue" && queueBadge > 0 ? queueBadge : null;
        return (
          <button
            key={it.id}
            type="button"
            onClick={() => onChange(it.id)}
            aria-current={active === it.id ? "page" : undefined}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs font-medium transition-colors md:flex-none md:justify-start md:text-sm",
              active === it.id
                ? "bg-surface-2 text-foreground shadow-glow"
                : "text-muted-foreground hover:bg-surface-2/60 hover:text-foreground",
            )}
          >
            <it.icon className="size-4" />
            <span className="hidden sm:inline">{it.label}</span>
            {badge !== null && (
              <span className="ml-auto hidden rounded-full bg-primary px-1.5 text-[10px] font-semibold text-primary-foreground md:inline">
                {badge}
              </span>
            )}
          </button>
        );
      })}

      <div className="mt-auto hidden rounded-lg border border-border bg-surface-2/40 p-2.5 text-[11px] text-muted-foreground md:block">
        <span className="flex items-center gap-1.5">
          <span className="size-1.5 rounded-full bg-success" />
          {speedLabel ?? "Sẵn sàng"}
        </span>
        <span className="mt-1 block">{freeLabel ?? "—"}</span>
      </div>
    </nav>
  );
}
