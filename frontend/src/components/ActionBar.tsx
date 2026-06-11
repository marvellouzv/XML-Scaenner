import { Activity, Copy, Download, LoaderCircle, PauseCircle, PlayCircle, RefreshCcw, ScanText } from "lucide-react";
import { useEffect, useState } from "react";
import { useExportMutation, usePauseUrlTestMutation, useStartScanMutation, useStartUrlTestMutation } from "../hooks/useSitemapQuery";
import { useSitemapStore } from "../store/useSitemapStore";
import { Button } from "./ui/button";
import { Toast } from "./ui/toast";

interface Props {
  layout?: "row" | "column";
}

export function ActionBar({ layout = "row" }: Props) {
  const { urls, sessionId, status } = useSitemapStore();
  const exportMutation = useExportMutation();
  const scanMutation = useStartScanMutation();
  const testMutation = useStartUrlTestMutation();
  const pauseTestMutation = usePauseUrlTestMutation();
  const [toastText, setToastText] = useState("");
  const [showToast, setShowToast] = useState(false);

  const hasTitleResults = urls.some((row) => row.scan_status === "done" || row.scan_status === "error" || Boolean(row.title));

  useEffect(() => {
    if (!showToast) {
      return;
    }
    const timer = window.setTimeout(() => setShowToast(false), 2000);
    return () => window.clearTimeout(timer);
  }, [showToast]);

  const copyUrls = async () => {
    const text = urls.map((item) => item.url).join("\n");
    await navigator.clipboard.writeText(text);
    setToastText(`✓ Скопировано ${urls.length.toLocaleString("ru-RU")} URL`);
    setShowToast(true);
  };

  const exportData = async () => {
    if (!sessionId) {
      return;
    }
    const { blob, filename } = await exportMutation.mutateAsync();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);
  };

  const startScan = async () => {
    await scanMutation.mutateAsync();
  };

  const startTest = async () => {
    await testMutation.mutateAsync();
  };

  const pauseTest = async () => {
    await pauseTestMutation.mutateAsync();
    setToastText("Тестирование URL приостановлено");
    setShowToast(true);
  };

  const hasPendingTestEntries = urls.some((row) => row.test_status === "pending");
  const hasStartedTest = urls.some((row) => row.test_status === "done" || row.test_status === "error");
  const isResumeAvailable = status !== "testing" && hasStartedTest && hasPendingTestEntries;
  const isTestingRunning = status === "testing";

  return (
    <>
      <div className={layout === "column" ? "flex flex-col gap-2" : "flex flex-wrap items-center gap-2"}>
        <Button variant="secondary" onClick={copyUrls} disabled={urls.length === 0} className={layout === "column" ? "w-full justify-start" : ""}>
          <Copy className="mr-2 h-4 w-4" /> COPY
        </Button>
        <Button
          variant="secondary"
          onClick={exportData}
          disabled={!sessionId || exportMutation.isPending}
          className={layout === "column" ? "w-full justify-start" : ""}
        >
          {exportMutation.isPending ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
          EXPORT
        </Button>
        {isTestingRunning ? (
          <Button
            variant="secondary"
            onClick={pauseTest}
            disabled={!sessionId || pauseTestMutation.isPending}
            className={layout === "column" ? "w-full justify-start border-amber-500/60 bg-amber-100/80 text-amber-900 hover:bg-amber-200 dark:bg-amber-900/30 dark:text-amber-200" : "border-amber-500/60 bg-amber-100/80 text-amber-900 hover:bg-amber-200 dark:bg-amber-900/30 dark:text-amber-200"}
          >
            {pauseTestMutation.isPending ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : <PauseCircle className="mr-2 h-4 w-4" />}
            TEST PAUSE
          </Button>
        ) : (
          <Button
            onClick={startTest}
            disabled={!sessionId || urls.length === 0 || testMutation.isPending || status === "scanning"}
            className={
              isResumeAvailable
                ? layout === "column"
                  ? "w-full justify-start border-green-500/60 bg-green-100/80 text-green-900 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-200"
                  : "border-green-500/60 bg-green-100/80 text-green-900 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-200"
                : layout === "column"
                  ? "w-full justify-start"
                  : ""
            }
          >
            {testMutation.isPending ? (
              <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />
            ) : isResumeAvailable ? (
              <PlayCircle className="mr-2 h-4 w-4" />
            ) : (
              <Activity className="mr-2 h-4 w-4" />
            )}
            {isResumeAvailable ? "RESUME TEST" : "TEST URL"}
          </Button>
        )}
        <Button
          onClick={startScan}
          disabled={!sessionId || urls.length === 0 || scanMutation.isPending || status === "scanning" || status === "testing"}
          className={layout === "column" ? "w-full justify-start" : ""}
        >
          {scanMutation.isPending ? (
            <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />
          ) : hasTitleResults ? (
            <RefreshCcw className="mr-2 h-4 w-4" />
          ) : (
            <ScanText className="mr-2 h-4 w-4" />
          )}
          {hasTitleResults ? "ПОВТОРИТЬ" : "SCAN TITLES"}
        </Button>
      </div>
      <Toast message={toastText} show={showToast} />
    </>
  );
}
