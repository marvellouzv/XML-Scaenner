import { AlertTriangle, CheckCircle2, FileText, FileWarning, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { SitemapUrl } from "../types";

interface Props {
  sitemapUrl: string | null;
  rows: SitemapUrl[];
}

function shortSitemapFileName(sitemapUrl: string | null): string {
  if (!sitemapUrl) {
    return "—";
  }
  try {
    const parsed = new URL(sitemapUrl);
    const parts = parsed.pathname.split("/").filter(Boolean);
    return parts.length > 0 ? (parts[parts.length - 1] ?? sitemapUrl) : sitemapUrl;
  } catch {
    return sitemapUrl;
  }
}

function buildErrorBreakdown(rows: SitemapUrl[]): Record<string, number> {
  const counters: Record<string, number> = {};
  for (const row of rows) {
    if (row.test_status !== "error") {
      continue;
    }
    const key = row.test_error?.trim() || "Ошибка без деталей";
    counters[key] = (counters[key] ?? 0) + 1;
  }
  return counters;
}

interface ResponseSample {
  id: number;
  url: string;
  responseTimeMs: number;
}

function buildResponseSamples(rows: SitemapUrl[]): ResponseSample[] {
  return rows
    .filter((row) => row.test_document_type !== "empty")
    .map((row) => ({
      id: row.id,
      url: row.url,
      responseTimeMs: row.test_response_time_ms ?? -1
    }))
    .filter((row) => row.responseTimeMs >= 0);
}

function avgNearestSamples(samples: ResponseSample[], avg: number): ResponseSample[] {
  const sortedByDistance = [...samples].sort((a, b) => Math.abs(a.responseTimeMs - avg) - Math.abs(b.responseTimeMs - avg));
  const center = sortedByDistance[0];
  if (!center) {
    return [];
  }

  const above = samples.filter((row) => row.id !== center.id && row.responseTimeMs > avg).sort((a, b) => a.responseTimeMs - b.responseTimeMs).slice(0, 5);
  const below = samples.filter((row) => row.id !== center.id && row.responseTimeMs < avg).sort((a, b) => b.responseTimeMs - a.responseTimeMs).slice(0, 4);

  return [center, ...above, ...below];
}

export function SessionReport({ sitemapUrl, rows }: Props) {
  const [openErrorKey, setOpenErrorKey] = useState<string | null>(null);
  const [openResponseBucket, setOpenResponseBucket] = useState<"min" | "max" | "avg" | null>(null);

  const totalPages = rows.length;
  const healthyPages = rows.filter((row) => row.test_status === "done").length;
  const errorPages = rows.filter((row) => row.test_status === "error").length;
  const emptyPages = rows.filter((row) => row.test_document_type === "empty").length;
  const responseSamples = useMemo(() => buildResponseSamples(rows), [rows]);
  const responseTimes = responseSamples.map((row) => row.responseTimeMs);
  const minResponseMs = responseTimes.length > 0 ? Math.min(...responseTimes) : null;
  const maxResponseMs = responseTimes.length > 0 ? Math.max(...responseTimes) : null;
  const avgResponseMs = responseTimes.length > 0 ? Math.round(responseTimes.reduce((sum, value) => sum + value, 0) / responseTimes.length) : null;
  const errorBreakdown = buildErrorBreakdown(rows);
  const errorEntries = Object.entries(errorBreakdown).sort((a, b) => b[1] - a[1]);

  const minSamples = useMemo(() => [...responseSamples].sort((a, b) => a.responseTimeMs - b.responseTimeMs).slice(0, 10), [responseSamples]);
  const maxSamples = useMemo(() => [...responseSamples].sort((a, b) => b.responseTimeMs - a.responseTimeMs).slice(0, 10), [responseSamples]);
  const avgSamples = useMemo(
    () => (avgResponseMs == null ? [] : avgNearestSamples(responseSamples, avgResponseMs)),
    [avgResponseMs, responseSamples]
  );

  const activeResponseSamples = openResponseBucket === "min" ? minSamples : openResponseBucket === "max" ? maxSamples : openResponseBucket === "avg" ? avgSamples : [];
  const activeResponseTitle =
    openResponseBucket === "min"
      ? "10 страниц с минимальным временем отклика"
      : openResponseBucket === "max"
        ? "10 страниц с максимальным временем отклика"
        : openResponseBucket === "avg"
          ? "10 страниц около среднего (центр, 5 выше, 4 ниже)"
          : "";

  const expandedErrorUrls = useMemo(() => {
    if (!openErrorKey) {
      return [];
    }
    return rows
      .filter((row) => row.test_status === "error" && (row.test_error?.trim() || "Ошибка без деталей") === openErrorKey)
      .map((row) => row.url);
  }, [openErrorKey, rows]);

  return (
    <section className="rounded-lg border border-border bg-card/80 p-4">
      <div className="rounded-md border border-border bg-card p-3">
        <div className="mb-1 flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
          <FileText className="h-3.5 w-3.5" />
          Файл
        </div>
        <div className="truncate text-sm font-semibold text-foreground" title={sitemapUrl ?? ""}>
          {shortSitemapFileName(sitemapUrl)}
        </div>
        {sitemapUrl ? <div className="mt-1 truncate text-xs text-muted-foreground">{sitemapUrl}</div> : null}
      </div>

      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-md border border-border bg-card p-3">
          <div className="mb-1 flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
            <ShieldCheck className="h-3.5 w-3.5" />
            Найдено
          </div>
          <div className="text-lg font-semibold text-foreground">{totalPages.toLocaleString("ru-RU")}</div>
          <div className="text-xs text-muted-foreground">страниц</div>
        </div>

        <div className="rounded-md border border-border bg-card p-3">
          <div className="mb-1 flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
            <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            Рабочие
          </div>
          <div className="text-lg font-semibold text-foreground">{healthyPages.toLocaleString("ru-RU")}</div>
          <div className="text-xs text-muted-foreground">страниц</div>
        </div>

        <div className="rounded-md border border-border bg-card p-3">
          <div className="mb-1 flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
            <AlertTriangle className="h-3.5 w-3.5 text-red-500" />
            Ошибки
          </div>
          <div className="text-lg font-semibold text-foreground">{errorPages.toLocaleString("ru-RU")}</div>
          <div className="text-xs text-muted-foreground">страниц</div>
        </div>
      </div>

      <div className="mt-3 rounded-md border border-border bg-card p-3">
        <div className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">Время ответа страниц</div>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          <button
            type="button"
            onClick={() => setOpenResponseBucket((prev) => (prev === "min" ? null : "min"))}
            className="rounded border border-border bg-muted/50 px-2 py-1.5 text-left transition hover:bg-muted"
          >
            <div className="text-xs text-muted-foreground">Минимум</div>
            <div className="text-sm font-semibold text-foreground">{minResponseMs != null ? `${minResponseMs} ms` : "—"}</div>
          </button>
          <button
            type="button"
            onClick={() => setOpenResponseBucket((prev) => (prev === "max" ? null : "max"))}
            className="rounded border border-border bg-muted/50 px-2 py-1.5 text-left transition hover:bg-muted"
          >
            <div className="text-xs text-muted-foreground">Максимум</div>
            <div className="text-sm font-semibold text-foreground">{maxResponseMs != null ? `${maxResponseMs} ms` : "—"}</div>
          </button>
          <button
            type="button"
            onClick={() => setOpenResponseBucket((prev) => (prev === "avg" ? null : "avg"))}
            className="rounded border border-border bg-muted/50 px-2 py-1.5 text-left transition hover:bg-muted"
          >
            <div className="text-xs text-muted-foreground">Среднее</div>
            <div className="text-sm font-semibold text-foreground">{avgResponseMs != null ? `${avgResponseMs} ms` : "—"}</div>
          </button>
        </div>

        {openResponseBucket ? (
          <div className="mt-3 rounded border border-border bg-muted/30 p-2">
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{activeResponseTitle}</div>
            {activeResponseSamples.length === 0 ? (
              <div className="text-sm text-muted-foreground">Нет данных для отображения.</div>
            ) : (
              <div className="select-text whitespace-pre-wrap break-all rounded border border-border bg-card px-2 py-1.5 font-mono text-sm text-foreground">
                {activeResponseSamples.map((row) => `${row.responseTimeMs} ms\t${row.url}`).join("\n")}
              </div>
            )}
          </div>
        ) : null}
      </div>

      <div className="mt-3 rounded-md border border-border bg-card p-3">
        <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
          <FileWarning className="h-3.5 w-3.5 text-red-500" />
          Страницы с ошибками: {errorPages.toLocaleString("ru-RU")}
        </div>

        {emptyPages > 0 ? (
          <div className="mb-2 flex items-start justify-between gap-3 rounded border border-border bg-muted/50 px-2 py-1.5 text-sm">
            <span className="text-foreground">Пустые страницы</span>
            <span className="shrink-0 font-semibold text-foreground">{emptyPages.toLocaleString("ru-RU")}</span>
          </div>
        ) : null}

        {errorEntries.length === 0 ? (
          <div className="text-sm text-muted-foreground">Ошибки не обнаружены или тестирование еще не запускалось.</div>
        ) : (
          <div className="space-y-1">
            {errorEntries.map(([errorText, count]) => (
              <div key={errorText}>
                <button
                  type="button"
                  onClick={() => setOpenErrorKey((prev) => (prev === errorText ? null : errorText))}
                  className="flex w-full items-start justify-between gap-3 rounded border border-border bg-muted/50 px-2 py-1.5 text-left text-sm transition hover:bg-muted"
                >
                  <span className="text-foreground">{errorText}</span>
                  <span className="shrink-0 font-semibold text-red-700 dark:text-red-300">{count.toLocaleString("ru-RU")}</span>
                </button>

                {openErrorKey === errorText ? (
                  <div className="mt-1 space-y-1 rounded border border-border bg-muted/30 p-2">
                    {expandedErrorUrls.length === 0 ? (
                      <div className="text-sm text-muted-foreground">Нет URL для этой ошибки.</div>
                    ) : (
                      <div className="select-text whitespace-pre-wrap break-all rounded border border-border bg-card px-2 py-1.5 font-mono text-sm text-foreground">
                        {expandedErrorUrls.join("\n")}
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
