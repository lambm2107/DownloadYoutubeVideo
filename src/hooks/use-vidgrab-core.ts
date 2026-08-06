import { useCallback, useEffect, useRef, useState } from "react";
import { core, type CoreAnalysis, type CoreTask, type CoreHealth } from "@/lib/vidgrab-core";

export type CoreStatus = "checking" | "online" | "offline";

/** Theo dõi lõi Python: trạng thái kết nối, kết quả phân tích và hàng đợi tải. */
export function useVidgrabCore() {
  const [status, setStatus] = useState<CoreStatus>("checking");
  const [health, setHealth] = useState<CoreHealth | null>(null);
  const [analysis, setAnalysis] = useState<CoreAnalysis | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tasks, setTasks] = useState<CoreTask[]>([]);
  const [history, setHistory] = useState<CoreTask[]>([]);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let alive = true;

    const ping = async () => {
      try {
        const h = await core.health();
        if (!alive) return;
        setStatus("online");
        setHealth(h);
        const [t, hist] = await Promise.all([core.tasks(), core.history()]);
        if (!alive) return;
        setTasks(t);
        setHistory(hist);
      } catch {
        if (alive) {
          setStatus("offline");
          setHealth(null);
        }
      }
    };

    void ping();
    timer.current = setInterval(ping, 1500);
    return () => {
      alive = false;
      if (timer.current) clearInterval(timer.current);
    };
  }, []);

  const analyze = useCallback(async (url: string, mode: "single" | "playlist") => {
    setAnalyzing(true);
    setError(null);
    try {
      setAnalysis(await core.analyze(url, mode));
    } catch (e) {
      setAnalysis(null);
      setError(e instanceof Error ? e.message : "Không phân tích được liên kết");
    } finally {
      setAnalyzing(false);
    }
  }, []);

  const pauseTask = useCallback(async (id: string) => {
    try {
      await core.pause(id);
    } catch (e) {
      console.error("Lỗi khi tạm dừng:", e);
    }
  }, []);

  const resumeTask = useCallback(async (id: string) => {
    try {
      await core.resume(id);
    } catch (e) {
      console.error("Lỗi khi tiếp tục:", e);
    }
  }, []);

  const cancelTask = useCallback(async (id: string) => {
    try {
      await core.cancel(id);
      setTasks((prev) => prev.filter((t) => t.id !== id));
    } catch (e) {
      console.error("Lỗi khi hủy:", e);
    }
  }, []);

  return {
    status,
    health,
    analysis,
    analyzing,
    error,
    tasks,
    history,
    analyze,
    setError,
    pauseTask,
    resumeTask,
    cancelTask,
  };
}
