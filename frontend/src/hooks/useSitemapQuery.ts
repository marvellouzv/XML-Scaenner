import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import {
  exportSitemap,
  getArchiveSessions,
  getLoadSitemapProgress,
  getLoadSitemapResult,
  getScanProgress,
  getUrlTestProgress,
  restoreArchiveSession,
  getSessionData,
  startLoadSitemap,
  startTitleScan,
  startUrlTest
} from "../api/client";
import { useSitemapStore } from "../store/useSitemapStore";

function getApiErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Неизвестная ошибка";
}

export function useLoadSitemapMutation() {
  const { setLoadJob, setError, setStatus } = useSitemapStore();
  return useMutation({
    mutationFn: startLoadSitemap,
    onMutate: () => {
      setStatus("loading");
      setError(null);
    },
    onSuccess: (data) => {
      setLoadJob(data.job_id);
    },
    onError: (error: unknown) => {
      setStatus("error");
      setError(getApiErrorMessage(error));
    }
  });
}

export function useLoadProgressQuery(enabled: boolean) {
  const { loadJobId } = useSitemapStore();
  return useQuery({
    queryKey: ["load-progress", loadJobId],
    queryFn: async () => {
      if (!loadJobId) {
        throw new Error("Load job id missing");
      }
      return getLoadSitemapProgress(loadJobId);
    },
    enabled: Boolean(loadJobId && enabled),
    refetchInterval: 300,
    retry: 5,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 10000)
  });
}

export function useLoadResultQuery(jobId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ["load-result", jobId],
    queryFn: async () => {
      if (!jobId) {
        throw new Error("Load job id missing");
      }
      return getLoadSitemapResult(jobId);
    },
    enabled: Boolean(jobId && enabled),
    retry: false
  });
}

export function useStartScanMutation() {
  const { sessionId, setStatus, setError } = useSitemapStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      if (!sessionId) {
        throw new Error("Сначала загрузите sitemap");
      }
      return startTitleScan(sessionId);
    },
    onMutate: () => {
      setStatus("scanning");
      setError(null);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scan-progress", sessionId] });
    },
    onError: (error: unknown) => {
      setStatus("error");
      setError(getApiErrorMessage(error));
    }
  });
}

export function useScanProgressQuery(enabled: boolean) {
  const { sessionId } = useSitemapStore();

  return useQuery({
    queryKey: ["scan-progress", sessionId],
    queryFn: async () => {
      if (!sessionId) {
        throw new Error("Session ID missing");
      }
      return getScanProgress(sessionId);
    },
    enabled: Boolean(sessionId && enabled),
    refetchInterval: 2000,
    retry: 5,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 10000)
  });
}

export function useStartUrlTestMutation() {
  const { sessionId, setStatus, setError } = useSitemapStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      if (!sessionId) {
        throw new Error("Сначала загрузите sitemap");
      }
      return startUrlTest(sessionId);
    },
    onMutate: () => {
      setStatus("testing");
      setError(null);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["test-progress", sessionId] });
    },
    onError: (error: unknown) => {
      setStatus("error");
      setError(getApiErrorMessage(error));
    }
  });
}

export function useTestProgressQuery(enabled: boolean) {
  const { sessionId } = useSitemapStore();

  return useQuery({
    queryKey: ["test-progress", sessionId],
    queryFn: async () => {
      if (!sessionId) {
        throw new Error("Session ID missing");
      }
      return getUrlTestProgress(sessionId);
    },
    enabled: Boolean(sessionId && enabled),
    refetchInterval: 2000,
    retry: 5,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 10000)
  });
}

export function useExportMutation() {
  const { sessionId } = useSitemapStore();
  return useMutation({
    mutationFn: async () => {
      if (!sessionId) {
        throw new Error("Нет session_id для экспорта");
      }
      return exportSitemap(sessionId);
    }
  });
}

export function useSessionQuery(sessionId: number | null, enabled: boolean) {
  return useQuery({
    queryKey: ["session-data", sessionId],
    queryFn: async () => {
      if (!sessionId) {
        throw new Error("Session ID missing");
      }
      return getSessionData(sessionId);
    },
    enabled: Boolean(sessionId && enabled)
  });
}

export function useArchiveQuery(query: string, enabled: boolean) {
  return useQuery({
    queryKey: ["archive-sessions", query],
    queryFn: async () => getArchiveSessions({ query: query.trim() || undefined, limit: 100, offset: 0 }),
    enabled
  });
}

export function useRestoreArchiveMutation() {
  const { setSession, setStatus, setError } = useSitemapStore();
  return useMutation({
    mutationFn: async (sessionId: number) => restoreArchiveSession(sessionId),
    onMutate: () => {
      setError(null);
    },
    onSuccess: (data) => {
      setSession(data.session_id, data.urls);
      setStatus("loaded");
    },
    onError: (error: unknown) => {
      setStatus("error");
      setError(getApiErrorMessage(error));
    }
  });
}
