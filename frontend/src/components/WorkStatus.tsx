import { Activity, CheckCircle2, Clock3, FileSearch, LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { SessionStatus } from "../types";

interface Props {
  status: SessionStatus;
  totalUrls: number;
  scanned: number;
}

function statusLabel(status: SessionStatus): string {
  if (status === "idle") {
    return "Ожидание загрузки sitemap";
  }
  if (status === "loading") {
    return "Загрузка sitemap";
  }
  if (status === "loaded") {
    return "Sitemap загружен";
  }
  if (status === "scanning") {
    return "Сканирование title";
  }
  if (status === "testing") {
    return "Проверка URL (TEST URL)";
  }
  if (status === "done") {
    return "Операция завершена";
  }
  return "Ошибка";
}

function statusIcon(status: SessionStatus) {
  if (status === "loading") {
    return <LoaderCircle className="h-4 w-4 animate-spin text-blue-400" />;
  }
  if (status === "scanning" || status === "testing") {
    return <Clock3 className="h-4 w-4 text-amber-400" />;
  }
  if (status === "done") {
    return <CheckCircle2 className="h-4 w-4 text-green-400" />;
  }
  return <Activity className="h-4 w-4 text-muted-foreground" />;
}

export function WorkStatus({ status, totalUrls, scanned }: Props) {
  const [displayedUrls, setDisplayedUrls] = useState(0);

  useEffect(() => {
    if (totalUrls <= displayedUrls) {
      setDisplayedUrls(totalUrls);
      return;
    }

    const diff = totalUrls - displayedUrls;
    const step = Math.max(1, Math.ceil(diff / 25));
    const timer = window.setInterval(() => {
      setDisplayedUrls((prev) => {
        const next = prev + step;
        if (next >= totalUrls) {
          window.clearInterval(timer);
          return totalUrls;
        }
        return next;
      });
    }, 40);

    return () => window.clearInterval(timer);
  }, [displayedUrls, totalUrls]);

  return (
    <div className="grid grid-cols-1 gap-3 rounded-lg border border-border bg-card/70 p-4 md:grid-cols-3">
      <div className="rounded-md border border-border bg-card p-3">
        <div className="mb-1 flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
          <FileSearch className="h-3.5 w-3.5" />
          Найдено URL
        </div>
        <div className="text-2xl font-bold text-foreground">{displayedUrls.toLocaleString("ru-RU")}</div>
      </div>

      <div className="rounded-md border border-border bg-card p-3">
        <div className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">Статус</div>
        <div className="flex items-center gap-2 text-sm text-foreground">
          {statusIcon(status)}
          <span>{statusLabel(status)}</span>
        </div>
      </div>

      <div className="rounded-md border border-border bg-card p-3">
        <div className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">Обработано</div>
        <div className="text-lg font-semibold text-foreground">{scanned.toLocaleString("ru-RU")}</div>
      </div>
    </div>
  );
}
