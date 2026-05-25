import { create } from "zustand";
import { SitemapUrl, SessionStatus } from "../types";

interface ProgressState {
  total: number;
  scanned: number;
  errors: number;
  errorBreakdown: Record<string, number>;
  runtimePhase: string | null;
  runtimeMessage: string | null;
  runtimeDecision: string | null;
  runtimeRound: number | null;
  runtimeTotalRounds: number | null;
  runtimeConcurrency: number | null;
  runtimeDelay: number | null;
  runtimePendingUrls: number | null;
}

interface SitemapState {
  sessionId: number | null;
  loadJobId: string | null;
  loadingFoundCount: number;
  urls: SitemapUrl[];
  status: SessionStatus;
  error: string | null;
  progress: ProgressState;
  setLoadJob: (jobId: string) => void;
  setLoadingFoundCount: (found: number) => void;
  setSession: (sessionId: number, urls: SitemapUrl[]) => void;
  setUrls: (urls: SitemapUrl[]) => void;
  setStatus: (status: SessionStatus) => void;
  setError: (error: string | null) => void;
  setProgress: (progress: ProgressState) => void;
  reset: () => void;
}

const initialProgress: ProgressState = {
  total: 0,
  scanned: 0,
  errors: 0,
  errorBreakdown: {},
  runtimePhase: null,
  runtimeMessage: null,
  runtimeDecision: null,
  runtimeRound: null,
  runtimeTotalRounds: null,
  runtimeConcurrency: null,
  runtimeDelay: null,
  runtimePendingUrls: null
};

export const useSitemapStore = create<SitemapState>((set) => ({
  sessionId: null,
  loadJobId: null,
  loadingFoundCount: 0,
  urls: [],
  status: "idle",
  error: null,
  progress: initialProgress,
  setLoadJob: (loadJobId) => set({ loadJobId, status: "loading", error: null, loadingFoundCount: 0, urls: [], sessionId: null }),
  setLoadingFoundCount: (loadingFoundCount) => set({ loadingFoundCount }),
  setSession: (sessionId, urls) =>
    set({ sessionId, urls, loadJobId: null, loadingFoundCount: urls.length, status: "loaded", error: null, progress: initialProgress }),
  setUrls: (urls) => set({ urls }),
  setStatus: (status) => set({ status }),
  setError: (error) => set({ error }),
  setProgress: (progress) => set({ progress }),
  reset: () => set({ sessionId: null, loadJobId: null, loadingFoundCount: 0, urls: [], status: "idle", error: null, progress: initialProgress })
}));
