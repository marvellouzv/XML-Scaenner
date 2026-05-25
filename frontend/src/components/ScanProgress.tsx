import { Progress } from "./ui/progress";

interface Props {
  mode: "titles" | "test_urls";
  total: number;
  scanned: number;
  errors: number;
  errorBreakdown: Record<string, number>;
  runtimePhase: string | null;
  runtimeMessage: string | null;
  runtimeDecision: string | null;
  runtimeRound: number | null;
  runtimeTotalRounds: number | null;
  runtimeConcurrency: number | null;
  runtimeDelay: number | null;
  runtimePendingUrls: number | null;
}

function buildErrorTooltip(errorBreakdown: Record<string, number>): string {
  const entries = Object.entries(errorBreakdown);
  if (entries.length === 0) {
    return "Ошибок нет";
  }
  return entries
    .sort((a, b) => b[1] - a[1])
    .map(([errorType, count]) => `${count} — ${errorType}`)
    .join("\n");
}

export function ScanProgress({
  mode,
  total,
  scanned,
  errors,
  errorBreakdown,
  runtimePhase,
  runtimeMessage,
  runtimeDecision,
  runtimeRound,
  runtimeTotalRounds,
  runtimeConcurrency,
  runtimeDelay,
  runtimePendingUrls
}: Props) {
  const progressLabel = mode === "test_urls" ? "Проверено" : "Просканировано";
  const cardTitle = mode === "test_urls" ? "Статус проверки URL" : "Статус сканера";
  const percent = total > 0 ? (scanned / total) * 100 : 0;
  const scannedOnly = Math.max(0, scanned - errors);
  const scannedPercent = total > 0 ? (scannedOnly / total) * 100 : 0;
  const errorPercent = total > 0 ? (errors / total) * 100 : 0;
  const errorTooltip = buildErrorTooltip(errorBreakdown);

  return (
    <div className="mt-3 space-y-3 rounded-lg border border-border bg-card/60 p-3">
      <div className="text-sm text-foreground">
        {progressLabel}: {scanned.toLocaleString("ru-RU")} / {total.toLocaleString("ru-RU")}
      </div>
      <Progress value={percent} />
      <div className="space-y-2">
        <div className="text-xs text-muted-foreground">Полоска ошибок (наведите на красный сегмент)</div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
          <div className="flex h-full w-full">
            <div className="h-full bg-blue-500" style={{ width: `${scannedPercent}%` }} />
            <div className="h-full bg-red-500" style={{ width: `${errorPercent}%` }} title={errorTooltip} />
          </div>
        </div>
        <div className="text-xs text-muted-foreground">Ошибки: {errors.toLocaleString("ru-RU")}</div>
      </div>
      <div className="space-y-1 rounded-md border border-border bg-card p-3 text-xs text-muted-foreground">
        <div className="font-semibold text-foreground">{cardTitle}</div>
        <div>
          Фаза: <span className="text-foreground">{runtimePhase ?? "—"}</span>
        </div>
        <div>
          Раунд: <span className="text-foreground">{runtimeRound ?? "—"} / {runtimeTotalRounds ?? "—"}</span>
        </div>
        <div>
          Параллелизм: <span className="text-foreground">{runtimeConcurrency ?? "—"}</span>
        </div>
        <div>
          Пауза перед запросом: <span className="text-foreground">{runtimeDelay != null ? `${runtimeDelay.toFixed(2)}с` : "—"}</span>
        </div>
        <div>
          В очереди URL: <span className="text-foreground">{runtimePendingUrls ?? "—"}</span>
        </div>
        <div>
          Действие: <span className="text-foreground">{runtimeMessage ?? "—"}</span>
        </div>
        <div>
          Решение: <span className="text-foreground">{runtimeDecision ?? "—"}</span>
        </div>
      </div>
    </div>
  );
}
