import { Archive, Moon, RefreshCw, Sun } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ActionBar } from "./components/ActionBar";
import { ArchiveModal } from "./components/ArchiveModal";
import { ScanProgress } from "./components/ScanProgress";
import { SitemapInput } from "./components/SitemapInput";
import { UrlTable } from "./components/UrlTable";
import { WorkStatus } from "./components/WorkStatus";
import { Button } from "./components/ui/button";
import { Card } from "./components/ui/card";
import { useLoadProgressQuery, useLoadResultQuery, useScanProgressQuery, useSessionQuery, useTestProgressQuery } from "./hooks/useSitemapQuery";
import { useSitemapStore } from "./store/useSitemapStore";

function useTheme() {
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    const stored = window.localStorage.getItem("theme");
    return stored === "light" ? "light" : "dark";
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("theme", theme);
  }, [theme]);

  return { theme, toggle: () => setTheme((prev) => (prev === "dark" ? "light" : "dark")) };
}

export default function App() {
  const theme = useTheme();
  const [archiveOpen, setArchiveOpen] = useState(false);
  const { urls, status, error, progress, sessionId, loadJobId, loadingFoundCount, setProgress, setStatus, setError, setUrls, setSession, setLoadingFoundCount } =
    useSitemapStore();

  const loadProgressQuery = useLoadProgressQuery(status === "loading");
  const loadResultQuery = useLoadResultQuery(loadJobId, Boolean(loadProgressQuery.data && loadProgressQuery.data.status === "done"));
  const progressQuery = useScanProgressQuery(status === "scanning");
  const testProgressQuery = useTestProgressQuery(status === "testing");
  const sessionQuery = useSessionQuery(sessionId, status === "done");

  useEffect(() => {
    if (!loadProgressQuery.data) {
      return;
    }
    setLoadingFoundCount(loadProgressQuery.data.found);
    if (loadProgressQuery.data.status === "error") {
      setStatus("error");
      setError(loadProgressQuery.data.error ?? "Ошибка загрузки sitemap");
    }
  }, [loadProgressQuery.data, setError, setLoadingFoundCount, setStatus]);

  useEffect(() => {
    if (!loadResultQuery.data) {
      return;
    }
    setSession(loadResultQuery.data.session_id, loadResultQuery.data.urls);
  }, [loadResultQuery.data, setSession]);

  useEffect(() => {
    if (loadResultQuery.error) {
      setStatus("error");
      setError((loadResultQuery.error as Error).message);
    }
  }, [loadResultQuery.error, setError, setStatus]);

  useEffect(() => {
    if (!progressQuery.data) {
      return;
    }
    setProgress({
      total: progressQuery.data.total,
      scanned: progressQuery.data.scanned,
      errors: progressQuery.data.errors,
      errorBreakdown: progressQuery.data.error_breakdown,
      runtimePhase: progressQuery.data.runtime_phase ?? null,
      runtimeMessage: progressQuery.data.runtime_message ?? null,
      runtimeDecision: progressQuery.data.runtime_decision ?? null,
      runtimeRound: progressQuery.data.runtime_round ?? null,
      runtimeTotalRounds: progressQuery.data.runtime_total_rounds ?? null,
      runtimeConcurrency: progressQuery.data.runtime_concurrency ?? null,
      runtimeDelay: progressQuery.data.runtime_delay ?? null,
      runtimePendingUrls: progressQuery.data.runtime_pending_urls ?? null
    });
    if (progressQuery.data.status === "done") {
      setStatus("done");
    }
  }, [progressQuery.data, setProgress, setStatus]);

  useEffect(() => {
    if (!testProgressQuery.data) {
      return;
    }
    setProgress({
      total: testProgressQuery.data.total,
      scanned: testProgressQuery.data.scanned,
      errors: testProgressQuery.data.errors,
      errorBreakdown: testProgressQuery.data.error_breakdown,
      runtimePhase: testProgressQuery.data.runtime_phase ?? null,
      runtimeMessage: testProgressQuery.data.runtime_message ?? null,
      runtimeDecision: testProgressQuery.data.runtime_decision ?? null,
      runtimeRound: testProgressQuery.data.runtime_round ?? null,
      runtimeTotalRounds: testProgressQuery.data.runtime_total_rounds ?? null,
      runtimeConcurrency: testProgressQuery.data.runtime_concurrency ?? null,
      runtimeDelay: testProgressQuery.data.runtime_delay ?? null,
      runtimePendingUrls: testProgressQuery.data.runtime_pending_urls ?? null
    });
    if (testProgressQuery.data.status === "done") {
      setStatus("done");
    }
  }, [setProgress, setStatus, testProgressQuery.data]);

  useEffect(() => {
    if (sessionQuery.data) {
      setUrls(sessionQuery.data.urls);
    }
  }, [sessionQuery.data, setUrls]);

  const showTitleColumn = useMemo(
    () => status === "scanning" || urls.some((row) => row.scan_status === "done" || row.scan_status === "error" || Boolean(row.title)),
    [status, urls]
  );
  const showTestColumn = useMemo(
    () =>
      status === "testing" ||
      urls.some((row) => row.test_status === "done" || row.test_status === "error" || row.test_http_status != null || Boolean(row.test_error)),
    [status, urls]
  );
  const currentProgressMode = status === "testing" ? "test_urls" : "titles";

  const shellBackground =
    theme.theme === "dark"
      ? "radial-gradient(circle_at_20%_0%,#1d4ed822,transparent_40%),radial-gradient(circle_at_90%_10%,#0ea5e91a,transparent_35%),linear-gradient(180deg,#09090b,#0f172a_40%,#09090b)"
      : "radial-gradient(circle_at_20%_0%,#2563eb14,transparent_40%),radial-gradient(circle_at_90%_10%,#0284c714,transparent_35%),linear-gradient(180deg,#f8fafc,#eef2ff_40%,#f8fafc)";

  return (
    <div className="min-h-screen px-6 py-10 text-foreground" style={{ background: shellBackground }}>
      <div className="mx-auto max-w-[1280px] space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">Sitemap XML Scanner</h1>
            <p className="mt-1 text-sm text-muted-foreground">Загрузка sitemap, сканирование title и экспорт в Excel</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={() => setArchiveOpen(true)}>
              <Archive className="mr-2 h-4 w-4" />
              Архив
            </Button>
            <Button variant="secondary" onClick={theme.toggle}>
              {theme.theme === "dark" ? <Sun className="mr-2 h-4 w-4" /> : <Moon className="mr-2 h-4 w-4" />}
              {theme.theme === "dark" ? "Light" : "Dark"}
            </Button>
          </div>
        </header>

        <Card className="p-4">
          <SitemapInput />
        </Card>

        <WorkStatus status={status} totalUrls={status === "loading" ? loadingFoundCount : urls.length} scanned={progress.scanned} />

        {error ? (
          <Card className="flex items-center justify-between border-red-500/50 bg-red-100/70 p-4 dark:bg-red-950/30">
            <div className="text-sm text-red-700 dark:text-red-200">{error}</div>
            <Button
              variant="danger"
              onClick={() => {
                setError(null);
                if (status === "error" && sessionId) {
                  setStatus("loaded");
                }
              }}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Повтор
            </Button>
          </Card>
        ) : null}

        <Card className="space-y-4 p-4">
          <ActionBar />
          {status === "scanning" || status === "testing" || status === "done" ? (
            <ScanProgress
              mode={currentProgressMode}
              total={progress.total}
              scanned={progress.scanned}
              errors={progress.errors}
              errorBreakdown={progress.errorBreakdown}
              runtimePhase={progress.runtimePhase}
              runtimeMessage={progress.runtimeMessage}
              runtimeDecision={progress.runtimeDecision}
              runtimeRound={progress.runtimeRound}
              runtimeTotalRounds={progress.runtimeTotalRounds}
              runtimeConcurrency={progress.runtimeConcurrency}
              runtimeDelay={progress.runtimeDelay}
              runtimePendingUrls={progress.runtimePendingUrls}
            />
          ) : null}
        </Card>

        <Card className="p-4">
          {urls.length === 0 && status !== "loading" ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex h-64 flex-col items-center justify-center text-center">
              <div className="mb-4 h-16 w-16 rounded-full border border-dashed border-border bg-card/80" />
              <div className="text-muted-foreground">Введите URL sitemap и нажмите LOAD</div>
            </motion.div>
          ) : (
            <UrlTable rows={urls} loading={status === "loading"} showTitle={showTitleColumn} showTest={showTestColumn} />
          )}
        </Card>
      </div>
      <ArchiveModal open={archiveOpen} onClose={() => setArchiveOpen(false)} />
    </div>
  );
}
