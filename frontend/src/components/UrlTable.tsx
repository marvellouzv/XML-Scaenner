import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Clock3, Search, XCircle } from "lucide-react";
import { MouseEvent, useMemo, useState } from "react";
import { SitemapUrl } from "../types";
import { useRetestUrlsMutation } from "../hooks/useSitemapQuery";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Skeleton } from "./ui/skeleton";

type SortKey = "url" | "lastmod" | "source_sitemap" | "title" | "url_test";

interface Props {
  rows: SitemapUrl[];
  loading?: boolean;
  showTitle: boolean;
  showTest: boolean;
}

function statusIcon(status?: string | null) {
  if (status === "done") {
    return <CheckCircle2 className="h-4 w-4 text-green-400" />;
  }
  if (status === "error") {
    return <XCircle className="h-4 w-4 text-red-400" />;
  }
  return <Clock3 className="h-4 w-4 text-muted-foreground" />;
}

function titleCellText(row: SitemapUrl): string {
  if (row.scan_status === "error") {
    return row.scan_error ?? "Ошибка без деталей";
  }
  if (row.scan_status === "pending") {
    return "В очереди на переобход";
  }
  return row.title ?? "—";
}

function sourceSitemapLabel(sourceSitemap?: string | null): string {
  if (!sourceSitemap) {
    return "—";
  }
  try {
    const parsed = new URL(sourceSitemap);
    const parts = parsed.pathname.split("/").filter(Boolean);
    return parts.length > 0 ? (parts[parts.length - 1] ?? sourceSitemap) : sourceSitemap;
  } catch {
    return sourceSitemap;
  }
}

function testSortValue(row: SitemapUrl): string {
  if (row.test_http_status != null) {
    return `${row.test_http_status.toString().padStart(4, "0")}_${row.test_response_time_ms ?? 0}`;
  }
  if (row.test_status === "error") {
    return `9999_${row.test_error ?? ""}`;
  }
  if (row.test_status === "pending") {
    return "0000_pending";
  }
  return "0000_none";
}

function testCellText(row: SitemapUrl): string {
  const documentTypeLabel = (() => {
    if (row.test_document_type === "html") {
      return "HTML";
    }
    if (row.test_document_type === "file") {
      return "Файл";
    }
    if (row.test_document_type === "empty") {
      return "Пустая";
    }
    if (row.test_document_type === "unknown") {
      return "Неизвестно";
    }
    return null;
  })();

  if (row.test_status === "error") {
    return row.test_error ?? "Ошибка без деталей";
  }
  if (row.test_status === "pending") {
    return "В очереди";
  }
  if (row.test_http_status != null) {
    const timing = row.test_response_time_ms != null ? `${row.test_response_time_ms} ms` : "без замера времени";
    return documentTypeLabel ? `HTTP ${row.test_http_status} • ${timing} • ${documentTypeLabel}` : `HTTP ${row.test_http_status} • ${timing}`;
  }
  return "—";
}

export function UrlTable({ rows, loading = false, showTitle, showTest }: Props) {
  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState("__all__");
  const [errorFilter, setErrorFilter] = useState("__all__");
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [lastSelectedId, setLastSelectedId] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState("50");
  const [sortKey, setSortKey] = useState<SortKey>("url");
  const [sortAsc, setSortAsc] = useState(true);
  const retestMutation = useRetestUrlsMutation();

  const sourceOptions = useMemo(() => {
    const unique = Array.from(new Set(rows.map((row) => row.source_sitemap).filter((value): value is string => Boolean(value))));
    unique.sort((a, b) => sourceSitemapLabel(a).localeCompare(sourceSitemapLabel(b)));
    return unique;
  }, [rows]);

  const errorOptions = useMemo(() => {
    const unique = new Set<string>();
    for (const row of rows) {
      if (row.test_status === "error") {
        unique.add((row.test_error || "Ошибка без деталей").trim());
      }
      if (row.scan_status === "error") {
        unique.add((row.scan_error || "Ошибка без деталей").trim());
      }
    }
    return Array.from(unique).sort((a, b) => a.localeCompare(b));
  }, [rows]);

  const filteredRows = useMemo(
    () =>
      rows.filter((row) => {
        const matchesSearch = row.url.toLowerCase().includes(search.toLowerCase());
        const matchesSource = sourceFilter === "__all__" || row.source_sitemap === sourceFilter;
        const rowErrors = [
          row.test_status === "error" ? (row.test_error || "Ошибка без деталей").trim() : null,
          row.scan_status === "error" ? (row.scan_error || "Ошибка без деталей").trim() : null
        ].filter((value): value is string => Boolean(value));

        const matchesError =
          errorFilter === "__all__"
            ? true
            : errorFilter === "__has_error"
              ? rowErrors.length > 0
              : errorFilter === "__no_error"
                ? rowErrors.length === 0
                : rowErrors.includes(errorFilter);
        return matchesSearch && matchesSource && matchesError;
      }),
    [rows, search, sourceFilter, errorFilter]
  );

  const sortedRows = useMemo(() => {
    const copy = [...filteredRows];
    copy.sort((a, b) => {
      if (sortKey === "url_test") {
        const left = testSortValue(a);
        const right = testSortValue(b);
        return sortAsc ? left.localeCompare(right) : right.localeCompare(left);
      }
      const left = (a[sortKey] ?? "").toString();
      const right = (b[sortKey] ?? "").toString();
      return sortAsc ? left.localeCompare(right) : right.localeCompare(left);
    });
    return copy;
  }, [filteredRows, sortAsc, sortKey]);

  const pageSize = Number(perPage);
  const totalPages = Math.max(1, Math.ceil(sortedRows.length / pageSize));
  const pageRows = sortedRows.slice((page - 1) * pageSize, page * pageSize);
  const pageRowsById = useMemo(() => {
    const map = new Map<number, number>();
    pageRows.forEach((row, index) => map.set(row.id, index));
    return map;
  }, [pageRows]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc((prev) => !prev);
      return;
    }
    setSortKey(key);
    setSortAsc(true);
  };

  const selectedOnPageCount = pageRows.filter((row) => selectedIds.includes(row.id)).length;
  const isAllPageSelected = pageRows.length > 0 && selectedOnPageCount === pageRows.length;

  const toggleSelectAllOnPage = () => {
    if (isAllPageSelected) {
      setSelectedIds((prev) => prev.filter((id) => !pageRows.some((row) => row.id === id)));
      return;
    }
    setSelectedIds((prev) => Array.from(new Set([...prev, ...pageRows.map((row) => row.id)])));
  };

  const toggleSelectRow = (rowId: number, event: MouseEvent<HTMLInputElement>) => {
    const shiftPressed = event.shiftKey;
    if (shiftPressed && lastSelectedId != null && pageRowsById.has(lastSelectedId) && pageRowsById.has(rowId)) {
      const start = pageRowsById.get(lastSelectedId) ?? 0;
      const end = pageRowsById.get(rowId) ?? 0;
      const from = Math.min(start, end);
      const to = Math.max(start, end);
      const rangeIds = pageRows.slice(from, to + 1).map((row) => row.id);
      setSelectedIds((prev) => Array.from(new Set([...prev, ...rangeIds])));
      setLastSelectedId(rowId);
      return;
    }

    setSelectedIds((prev) => (prev.includes(rowId) ? prev.filter((id) => id !== rowId) : [...prev, rowId]));
    setLastSelectedId(rowId);
  };

  const selectedFilteredIds = filteredRows.map((row) => row.id).filter((id) => selectedIds.includes(id));

  const handleRetest = async () => {
    if (!selectedFilteredIds.length) {
      return;
    }
    await retestMutation.mutateAsync(selectedFilteredIds);
    setSelectedIds([]);
    setLastSelectedId(null);
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-muted-foreground">Найдено: {filteredRows.length.toLocaleString("ru-RU")} URL</div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              className="w-72 pl-9"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Поиск по URL"
            />
          </div>
          <Select
            value={sourceFilter}
            onValueChange={(value) => {
              setSourceFilter(value);
              setPage(1);
            }}
          >
            <div className="w-[260px]">
              <SelectTrigger>
                <SelectValue placeholder="Все sitemap файлы" />
              </SelectTrigger>
            </div>
            <SelectContent>
              <SelectItem value="__all__">Все sitemap файлы</SelectItem>
              {sourceOptions.map((source) => (
                <SelectItem key={source} value={source}>
                  {sourceSitemapLabel(source)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={errorFilter}
            onValueChange={(value) => {
              setErrorFilter(value);
              setPage(1);
            }}
          >
            <div className="w-[280px]">
              <SelectTrigger>
                <SelectValue placeholder="Все ошибки" />
              </SelectTrigger>
            </div>
            <SelectContent>
              <SelectItem value="__all__">Все ошибки</SelectItem>
              <SelectItem value="__has_error">Только с ошибками</SelectItem>
              <SelectItem value="__no_error">Без ошибок</SelectItem>
              {errorOptions.map((errorText) => (
                <SelectItem key={errorText} value={errorText}>
                  {errorText}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="secondary"
            onClick={handleRetest}
            disabled={selectedFilteredIds.length === 0 || retestMutation.isPending}
          >
            RETEST ({selectedFilteredIds.length.toLocaleString("ru-RU")})
          </Button>
          <Select value={perPage} onValueChange={(value) => setPerPage(value)}>
            <SelectTrigger>
              <SelectValue placeholder="50" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="50">50</SelectItem>
              <SelectItem value="100">100</SelectItem>
              <SelectItem value="200">200</SelectItem>
              <SelectItem value="500">500</SelectItem>
              <SelectItem value="1000">1000</SelectItem>
              <SelectItem value="5000">5000</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, idx) => (
            <Skeleton key={idx} className="h-10 w-full" />
          ))}
        </div>
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="overflow-auto rounded-lg border border-border">
          <table className="min-w-full text-sm">
            <thead className="bg-muted text-foreground">
              <tr>
                <th className="px-3 py-2 text-left">
                  <input type="checkbox" checked={isAllPageSelected} onChange={toggleSelectAllOnPage} />
                </th>
                <th className="px-3 py-2 text-left">#</th>
                <th className="cursor-pointer px-3 py-2 text-left" onClick={() => toggleSort("url")}>
                  URL
                </th>
                <th className="cursor-pointer px-3 py-2 text-left" onClick={() => toggleSort("lastmod")}>
                  Last Modified
                </th>
                <th className="cursor-pointer px-3 py-2 text-left" onClick={() => toggleSort("source_sitemap")}>
                  Sitemap File
                </th>
                {showTest ? (
                  <th className="cursor-pointer px-3 py-2 text-left" onClick={() => toggleSort("url_test")}>
                    URL Test
                  </th>
                ) : null}
                <AnimatePresence>
                  {showTitle ? (
                    <motion.th
                      initial={{ x: 40, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      exit={{ x: 40, opacity: 0 }}
                      className="cursor-pointer px-3 py-2 text-left"
                      onClick={() => toggleSort("title")}
                    >
                      Title
                    </motion.th>
                  ) : null}
                </AnimatePresence>
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row, index) => (
                <tr key={row.id} className={row.scan_status === "error" ? "bg-red-100/60 dark:bg-red-950/30" : "border-t border-border"}>
                  <td className="px-3 py-2">
                    <input type="checkbox" checked={selectedIds.includes(row.id)} onClick={(event) => toggleSelectRow(row.id, event)} readOnly />
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">{(page - 1) * pageSize + index + 1}</td>
                  <td className="max-w-[620px] truncate px-3 py-2 text-foreground">
                    <a
                      href={row.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-700 underline-offset-2 hover:underline dark:text-blue-400"
                      title={row.url}
                    >
                      {row.url}
                    </a>
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">{row.lastmod ?? "—"}</td>
                  <td className="max-w-[260px] truncate px-3 py-2 text-muted-foreground" title={row.source_sitemap ?? ""}>
                    {sourceSitemapLabel(row.source_sitemap)}
                  </td>
                  {showTest ? (
                    <td className="max-w-[280px] px-3 py-2 text-muted-foreground">
                      <div className="flex items-center gap-2">
                        {statusIcon(row.test_status)}
                        <span className={`truncate ${row.test_status === "error" ? "text-red-700 dark:text-red-300" : ""}`} title={row.test_error ?? ""}>
                          {testCellText(row)}
                        </span>
                      </div>
                    </td>
                  ) : null}
                  {showTitle ? (
                    <td className="max-w-[360px] px-3 py-2 text-muted-foreground">
                      <div className="flex items-center gap-2">
                        {statusIcon(row.scan_status)}
                        <span
                          className={`truncate ${row.scan_status === "error" ? "text-red-700 dark:text-red-300" : ""}`}
                          title={row.scan_status === "error" ? row.scan_error ?? "" : ""}
                        >
                          {titleCellText(row)}
                        </span>
                      </div>
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </motion.div>
      )}

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))} className="rounded px-2 py-1 hover:bg-muted disabled:opacity-40">
          Назад
        </button>
        <span>
          Страница {page} / {totalPages}
        </span>
        <button
          disabled={page >= totalPages}
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          className="rounded px-2 py-1 hover:bg-muted disabled:opacity-40"
        >
          Вперед
        </button>
      </div>
    </div>
  );
}

