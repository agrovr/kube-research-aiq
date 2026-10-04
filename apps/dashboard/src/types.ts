export type ResearchDepth = "auto" | "shallow" | "deep";
export type JobStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";
export type Stage = "survey" | "plan" | "descend" | "draft" | "surface";

export const STAGES: Stage[] = ["survey", "plan", "descend", "draft", "surface"];

export interface ResearchRequest {
  query: string;
  depth: ResearchDepth;
  tenant: string;
  tags: string[];
}

export interface Source {
  id: number;
  title: string;
  url: string | null;
  snippet: string;
  origin: "knowledge" | "web" | string;
  score: number;
}

export interface Section {
  title: string;
  question: string;
  body: string;
  source_ids: number[];
}

export interface JobEvent {
  at: string;
  stage: Stage | null;
  message: string;
  level: "info" | "warn" | "error" | string;
}

export interface ResearchJob {
  id: string;
  request: ResearchRequest;
  title: string;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  finished_at: string | null;
  attempts: number;
  selected_depth: ResearchDepth | null;
  stage: Stage | null;
  progress: number;
  plan: string[];
  sections: Section[];
  summary: string[];
  sources: Source[];
  report: string | null;
  error: string | null;
  events: JobEvent[];
  metadata: {
    writer?: string;
    route_reason?: string;
    stage_seconds?: Partial<Record<Stage, number>>;
    citation_coverage?: number;
    sources_cited?: number;
    [key: string]: unknown;
  };
}

export interface JobListResponse {
  jobs: ResearchJob[];
}

export interface EnqueueResponse {
  job_id: string;
  status: JobStatus;
  message: string;
}

export interface MetaResponse {
  name: string;
  version: string;
  provider: string;
  writer: "offline" | "model";
  retrieval: string[];
  models: { shallow: string; deep: string; planner: string } | null;
  queue: { available: boolean; waiting: number; in_progress: number };
  store: string;
  library_documents: number;
}
