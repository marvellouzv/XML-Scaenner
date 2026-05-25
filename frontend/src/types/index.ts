export type ScanStatus = "pending" | "done" | "error";
export type SessionStatus = "idle" | "loading" | "loaded" | "scanning" | "testing" | "done" | "error";

export interface SitemapUrl {
  id: number;
  url: string;
  lastmod?: string | null;
  changefreq?: string | null;
  priority?: string | null;
  source_sitemap?: string | null;
  title?: string | null;
  scan_status?: ScanStatus | null;
  scan_error?: string | null;
  test_status?: ScanStatus | null;
  test_error?: string | null;
  test_http_status?: number | null;
  test_response_time_ms?: number | null;
}

export interface LoadSitemapResponse {
  session_id: number;
  urls: SitemapUrl[];
  total: number;
}

export interface LoadSitemapStartResponse {
  job_id: string;
  status: "started";
}

export interface LoadSitemapProgressResponse {
  job_id: string;
  status: "running" | "done" | "error";
  found: number;
  total?: number | null;
  session_id?: number | null;
  error?: string | null;
}

export interface ScanProgressResponse {
  total: number;
  scanned: number;
  errors: number;
  error_breakdown: Record<string, number>;
  status: "running" | "done";
  runtime_phase?: string | null;
  runtime_message?: string | null;
  runtime_decision?: string | null;
  runtime_round?: number | null;
  runtime_total_rounds?: number | null;
  runtime_concurrency?: number | null;
  runtime_delay?: number | null;
  runtime_pending_urls?: number | null;
  mode?: "titles" | "test_urls";
}

export interface ArchiveSessionItem {
  session_id: number;
  sitemap_url: string;
  created_at: string;
  status: string;
  total_urls: number;
  title_done: number;
  title_errors: number;
  test_done: number;
  test_errors: number;
  query_matches: number;
}

export interface ArchiveListResponse {
  items: ArchiveSessionItem[];
  total: number;
}
