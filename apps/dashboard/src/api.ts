import type { EnqueueResponse, JobListResponse, ReadinessResponse, ResearchDepth } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers
    },
    ...init
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getReadiness(): Promise<ReadinessResponse> {
  return request<ReadinessResponse>("/readyz");
}

export function listJobs(): Promise<JobListResponse> {
  return request<JobListResponse>("/v1/research");
}

export function createJob(input: {
  query: string;
  depth: ResearchDepth;
  tenant: string;
  tags: string[];
}): Promise<EnqueueResponse> {
  return request<EnqueueResponse>("/v1/research", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function runJob(jobId: string) {
  return request(`/v1/research/${jobId}/run`, { method: "POST" });
}
