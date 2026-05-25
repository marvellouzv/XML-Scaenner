import { Archive, LoaderCircle, Search, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useArchiveQuery, useRestoreArchiveMutation } from "../hooks/useSitemapQuery";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

interface Props {
  open: boolean;
  onClose: () => void;
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function shortHost(url: string): string {
  try {
    return new URL(url).host;
  } catch {
    return url;
  }
}

export function ArchiveModal({ open, onClose }: Props) {
  const [query, setQuery] = useState("");
  const archiveQuery = useArchiveQuery(query, open);
  const restoreMutation = useRestoreArchiveMutation();

  const items = archiveQuery.data?.items ?? [];
  const total = archiveQuery.data?.total ?? 0;

  const subtitle = useMemo(() => {
    if (query.trim()) {
      return `Найдено ${total.toLocaleString("ru-RU")} сессий по URL: ${query}`;
    }
    return `Всего сессий в архиве: ${total.toLocaleString("ru-RU")}`;
  }, [query, total]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-5xl rounded-xl border border-border bg-card shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="flex items-center gap-2 text-foreground">
            <Archive className="h-4 w-4" />
            <div className="font-semibold">Архив сканирований</div>
          </div>
          <Button variant="secondary" onClick={onClose}>
            <X className="mr-2 h-4 w-4" /> Закрыть
          </Button>
        </div>

        <div className="space-y-3 px-4 py-3">
          <div className="text-sm text-muted-foreground">{subtitle}</div>
          <div className="relative max-w-lg">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-9"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Поиск по URL в сессиях архива"
            />
          </div>

          <div className="max-h-[65vh] overflow-auto rounded-lg border border-border">
            <table className="min-w-full text-sm">
              <thead className="bg-muted text-foreground">
                <tr>
                  <th className="px-3 py-2 text-left">Дата</th>
                  <th className="px-3 py-2 text-left">Сайт</th>
                  <th className="px-3 py-2 text-left">Сводка</th>
                  <th className="px-3 py-2 text-left">Совпадений URL</th>
                  <th className="px-3 py-2 text-left">Действие</th>
                </tr>
              </thead>
              <tbody>
                {archiveQuery.isLoading ? (
                  <tr>
                    <td className="px-3 py-6 text-muted-foreground" colSpan={5}>
                      <span className="inline-flex items-center gap-2">
                        <LoaderCircle className="h-4 w-4 animate-spin" /> Загрузка архива...
                      </span>
                    </td>
                  </tr>
                ) : null}

                {!archiveQuery.isLoading && items.length === 0 ? (
                  <tr>
                    <td className="px-3 py-6 text-muted-foreground" colSpan={5}>
                      Сессии не найдены
                    </td>
                  </tr>
                ) : null}

                {items.map((item) => (
                  <tr key={item.session_id} className="border-t border-border">
                    <td className="px-3 py-2 text-foreground">{formatDate(item.created_at)}</td>
                    <td className="max-w-[300px] truncate px-3 py-2 text-muted-foreground" title={item.sitemap_url}>
                      {shortHost(item.sitemap_url)}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">
                      URL: {item.total_urls.toLocaleString("ru-RU")} · Title ok/err: {item.title_done}/{item.title_errors} · Test ok/err: {item.test_done}/
                      {item.test_errors}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">{item.query_matches.toLocaleString("ru-RU")}</td>
                    <td className="px-3 py-2">
                      <Button
                        onClick={async () => {
                          await restoreMutation.mutateAsync(item.session_id);
                          onClose();
                        }}
                        disabled={restoreMutation.isPending}
                      >
                        {restoreMutation.isPending ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : null}
                        Восстановить
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
