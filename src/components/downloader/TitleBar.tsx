import { Minus, Square, X } from "lucide-react";

// Electron API exposed via preload.js (undefined khi chạy trên web)
declare global {
  interface Window {
    electronAPI?: {
      minimize: () => void;
      maximize: () => void;
      close: () => void;
      isMaximized: () => Promise<boolean>;
      openFolder: (path?: string) => Promise<{ ok: boolean }>;
      chooseFolder: () => Promise<string | null>;
      platform: string;
    };
  }
}

const api = typeof window !== "undefined" ? window.electronAPI : undefined;

export function TitleBar({ title }: { title: string }) {
  return (
    <div
      className="flex h-10 shrink-0 select-none items-center justify-between border-b border-border bg-surface-2/60 px-3"
      // Permite arrastar a janela pela barra de título
      style={{ WebkitAppRegion: "drag" } as React.CSSProperties}
    >
      <div className="flex items-center gap-2" style={{ WebkitAppRegion: "no-drag" } as React.CSSProperties}>
        <button
          type="button"
          title="Đóng"
          onClick={() => api?.close()}
          className="flex size-3 items-center justify-center rounded-full bg-destructive/80 transition-opacity hover:opacity-80"
          aria-label="Đóng cửa sổ"
        >
          {api && <X className="size-2 opacity-0 group-hover:opacity-100" />}
        </button>
        <button
          type="button"
          title="Thu nhỏ"
          onClick={() => api?.minimize()}
          className="flex size-3 items-center justify-center rounded-full bg-accent/80 transition-opacity hover:opacity-80"
          aria-label="Thu nhỏ cửa sổ"
        >
          {api && <Minus className="size-2 opacity-0" />}
        </button>
        <button
          type="button"
          title="Phóng to"
          onClick={() => api?.maximize()}
          className="flex size-3 items-center justify-center rounded-full bg-success/80 transition-opacity hover:opacity-80"
          aria-label="Phóng to cửa sổ"
        >
          {api && <Square className="size-2 opacity-0" />}
        </button>
      </div>

      <span className="text-xs font-medium text-muted-foreground">{title}</span>

      {/* Khoảng trống cân đối bên phải */}
      <div className="w-[52px]" />
    </div>
  );
}
