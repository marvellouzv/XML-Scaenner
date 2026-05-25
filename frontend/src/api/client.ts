import axios from "axios";
import {
  ArchiveListResponse,
  LoadSitemapProgressResponse,
  LoadSitemapResponse,
  LoadSitemapStartResponse,
  ScanProgressResponse
} from "../types";

const api = axios.create({
  baseURL: "/api",
  timeout: 120000
});

export async function startLoadSitemap(url: string): Promise<LoadSitemapStartResponse> {
  const { data } = await api.post<LoadSitemapStartResponse>(
    "/sitemap/load/start",
    { url },
    {
      timeout: 60000
    }
  );
  return data;
}

export async function getLoadSitemapProgress(jobId: string): Promise<LoadSitemapProgressResponse> {
  const { data } = await api.get<LoadSitemapProgressResponse>("/sitemap/load/progress", {
    params: { job_id: jobId },
    timeout: 60000
  });
  return data;
}

export async function getLoadSitemapResult(jobId: string): Promise<LoadSitemapResponse> {
  const { data } = await api.get<LoadSitemapResponse>("/sitemap/load/result", {
    params: { job_id: jobId },
    timeout: 60000
  });
  return data;
}

export async function loadSitemap(url: string): Promise<LoadSitemapResponse> {
  const { data } = await api.post<LoadSitemapResponse>(
    "/sitemap/load",
    { url },
    {
      timeout: 300000
    }
  );
  return data;
}

export async function startTitleScan(sessionId: number): Promise<{ task_id: string; status: "started" }> {
  const { data } = await api.post<{ task_id: string; status: "started" }>(
    "/scan/titles",
    { session_id: sessionId },
    {
      timeout: 60000
    }
  );
  return data;
}

export async function getScanProgress(sessionId: number): Promise<ScanProgressResponse> {
  const { data } = await api.get<ScanProgressResponse>("/scan/progress", {
    params: { session_id: sessionId },
    timeout: 60000
  });
  return data;
}

export async function startUrlTest(sessionId: number): Promise<{ task_id: string; status: "started" }> {
  const { data } = await api.post<{ task_id: string; status: "started" }>(
    "/scan/test-urls",
    { session_id: sessionId },
    {
      timeout: 60000
    }
  );
  return data;
}

export async function getUrlTestProgress(sessionId: number): Promise<ScanProgressResponse> {
  const { data } = await api.get<ScanProgressResponse>("/scan/test-progress", {
    params: { session_id: sessionId },
    timeout: 60000
  });
  return data;
}

function parseFilename(contentDisposition: string | undefined): string {
  if (!contentDisposition) {
    return `sitemap_export_${new Date().toISOString().slice(0, 10)}.xlsx`;
  }
  const match = contentDisposition.match(/filename="?([^"]+)"?/i);
  return match?.[1] ?? `sitemap_export_${new Date().toISOString().slice(0, 10)}.xlsx`;
}

export async function exportSitemap(sessionId: number): Promise<{ blob: Blob; filename: string }> {
  const response = await api.get<Blob>("/sitemap/export", {
    params: { session_id: sessionId },
    responseType: "blob",
    timeout: 300000
  });
  return {
    blob: response.data,
    filename: parseFilename(response.headers["content-disposition"])
  };
}

export async function getSessionData(sessionId: number): Promise<LoadSitemapResponse> {
  const { data } = await api.get<LoadSitemapResponse>("/sitemap/session", { params: { session_id: sessionId } });
  return data;
}

export async function getArchiveSessions(params?: { query?: string; limit?: number; offset?: number }): Promise<ArchiveListResponse> {
  const { data } = await api.get<ArchiveListResponse>("/sitemap/archive", { params });
  return data;
}

export async function restoreArchiveSession(sessionId: number): Promise<LoadSitemapResponse> {
  const { data } = await api.get<LoadSitemapResponse>(`/sitemap/archive/${sessionId}`);
  return data;
}
