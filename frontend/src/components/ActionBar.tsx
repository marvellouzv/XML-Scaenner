import { Activity, Copy, Download, LoaderCircle, RefreshCcw, ScanText } from "lucide-react";
import { useEffect, useState } from "react";
import { useExportMutation, useStartScanMutation, useStartUrlTestMutation } from "../hooks/useSitemapQuery";
import { useSitemapStore } from "../store/useSitemapStore";
import { Button } from "./ui/button";
import { Toast } from "./ui/toast";

export function ActionBar() {
  const { urls, sessionId, status } = useSitemapStore();
  const exportMutation = useExportMutation();
  const scanMutation = useStartScanMutation();
  const testMutation = useStartUrlTestMutation();
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

  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="secondary" onClick={copyUrls} disabled={urls.length === 0}>
          <Copy className="mr-2 h-4 w-4" /> COPY
        </Button>
        <Button variant="secondary" onClick={exportData} disabled={!sessionId || exportMutation.isPending}>
          {exportMutation.isPending ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
          EXPORT
        </Button>
        <Button
          onClick={startTest}
          disabled={!sessionId || urls.length === 0 || testMutation.isPending || status === "scanning" || status === "testing"}
        >
          {testMutation.isPending ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : <Activity className="mr-2 h-4 w-4" />}
          TEST URL
        </Button>
        <Button
          onClick={startScan}
          disabled={!sessionId || urls.length === 0 || scanMutation.isPending || status === "scanning" || status === "testing"}
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
