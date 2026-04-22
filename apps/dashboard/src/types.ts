export type ResearchDepth = "auto" | "shallow" | "deep";
export type JobStatus = "queued" | "running" | "succeeded" | "failed";

export interface ResearchRequest {
  query: string;
  depth: ResearchDepth;
  tenant: string;
  tags: string[];
}

export interface ResearchJob {
  id: string;
  request: ResearchRequest;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  selected_depth: ResearchDepth | null;
  plan: string[];
  report: string | null;
  citations: string[];
  error: string | null;
  metadata: Record<string, unknown>;
}

export interface JobListResponse {
  jobs: ResearchJob[];
}

export interface EnqueueResponse {
  job_id: string;
  status: JobStatus;
  message: string;
}

export interface ReadinessResponse {
  status: string;
  queue: boolean;
  store: string;
  provider?: string;
}
