import type { EnqueueResponse, JobListResponse, MetaResponse, ResearchDepth, ResearchJob } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers }
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d: { msg: string }) => d.msg).join("; ");
    } catch {
      // keep the status line
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const getMeta = () => request<MetaResponse>("/v1/meta");
export const listJobs = () => request<JobListResponse>("/v1/research");
export const getJob = (id: string) => request<ResearchJob>(`/v1/research/${id}`);

export function createJob(input: { query: string; depth: ResearchDepth; tenant: string; tags: string[] }) {
  return request<EnqueueResponse>("/v1/research", { method: "POST", body: JSON.stringify(input) });
}

export const runJob = (id: string) => request<ResearchJob>(`/v1/research/${id}/run`, { method: "POST" });
export const cancelJob = (id: string) => request<ResearchJob>(`/v1/research/${id}/cancel`, { method: "POST" });
export const retryJob = (id: string) => request<EnqueueResponse>(`/v1/research/${id}/retry`, { method: "POST" });

/** Follow a job over server-sent events until it finishes. Returns a function that stops. */
export function followJob(id: string, onJob: (job: ResearchJob) => void, onEnd: () => void): () => void {
  const source = new EventSource(apiUrl(`/v1/research/${id}/events`));
  source.addEventListener("job", (event) => onJob(JSON.parse((event as MessageEvent).data)));
  const end = () => {
    source.close();
    onEnd();
  };
  source.addEventListener("done", end);
  source.addEventListener("gone", end);
  source.onerror = end;
  return () => source.close();
}
