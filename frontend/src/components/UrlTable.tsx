import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Clock3, Search, XCircle } from "lucide-react";
import { useMemo, useState } from "react";
import { SitemapUrl } from "../types";
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
  if (row.test_status === "error") {
    return row.test_error ?? "Ошибка без деталей";
  }
  if (row.test_status === "pending") {
    return "В очереди";
  }
  if (row.test_http_status != null) {
    const timing = row.test_response_time_ms != null ? `${row.test_response_time_ms} ms` : "без замера времени";
    return `HTTP ${row.test_http_status} • ${timing}`;
  }
  return "—";
}

export function UrlTable({ rows, loading = false, showTitle, showTest }: Props) {
  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState("__all__");
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState("50");
  const [sortKey, setSortKey] = useState<SortKey>("url");
  const [sortAsc, setSortAsc] = useState(true);

  const sourceOptions = useMemo(() => {
    const unique = Array.from(new Set(rows.map((row) => row.source_sitemap).filter((value): value is string => Boolean(value))));
    unique.sort((a, b) => sourceSitemapLabel(a).localeCompare(sourceSitemapLabel(b)));
    return unique;
  }, [rows]);

  const filteredRows = useMemo(
    () =>
      rows.filter((row) => {
        const matchesSearch = row.url.toLowerCase().includes(search.toLowerCase());
        const matchesSource = sourceFilter === "__all__" || row.source_sitemap === sourceFilter;
        return matchesSearch && matchesSource;
      }),
    [rows, search, sourceFilter]
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

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc((prev) => !prev);
      return;
    }
    setSortKey(key);
    setSortAsc(true);
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

