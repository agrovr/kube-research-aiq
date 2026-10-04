import type { JobStatus, ResearchJob, Stage } from "./types";

export const statusWords: Record<JobStatus, string> = {
  queued: "Waiting",
  running: "Diving",
  succeeded: "Surfaced",
  failed: "Failed",
  cancelled: "Cancelled"
};

export const stageWords: Record<Stage, { name: string; doing: string }> = {
  survey: { name: "Survey", doing: "Reading the question" },
  plan: { name: "Plan", doing: "Breaking it into questions" },
  descend: { name: "Descend", doing: "Gathering sources" },
  draft: { name: "Draft", doing: "Writing with citations" },
  surface: { name: "Surface", doing: "Assembling the report" }
};

/** Deep dives bottom out at 4,000 m, shallow ones at 200 m. */
export function maxDepthOf(job: ResearchJob): number {
  const depth = job.selected_depth ?? job.request.depth;
  return depth === "deep" ? 4000 : 200;
}

export function currentDepth(job: ResearchJob): number {
  return Math.round(job.progress * maxDepthOf(job));
}

export function metres(value: number): string {
  return `${value.toLocaleString("en-US")} m`;
}

export function relativeTime(value: string, now = Date.now()): string {
  const seconds = Math.max(0, Math.round((now - new Date(value).getTime()) / 1000));
  if (seconds < 45) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(new Date(value));
}

export function clockTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(
    new Date(value)
  );
}

export function duration(job: ResearchJob): string | null {
  if (!job.started_at) return null;
  const end = job.finished_at ? new Date(job.finished_at).getTime() : Date.now();
  const seconds = (end - new Date(job.started_at).getTime()) / 1000;
  return seconds < 60 ? `${seconds.toFixed(1)} s` : `${Math.floor(seconds / 60)} min ${Math.round(seconds % 60)} s`;
}

export function hostOf(url: string | null): string | null {
  if (!url) return null;
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return null;
  }
}

export const isLive = (job: ResearchJob) => job.status === "queued" || job.status === "running";
