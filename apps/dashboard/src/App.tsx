import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { apiUrl, createJob, getReadiness, listJobs, runJob } from "./api";
import { ClusterIcon, DownloadIcon, PlayIcon, RefreshIcon, SendIcon, TopologyMark } from "./icons";
import type { JobStatus, ReadinessResponse, ResearchDepth, ResearchJob } from "./types";
import "./styles.css";

const samplePrompt =
  "Compare Kubernetes-native deployment strategies for AI research agents and recommend a production architecture.";

const statusOrder: Record<JobStatus, number> = {
  running: 0,
  queued: 1,
  succeeded: 2,
  failed: 3
};

const statusLabels: Record<JobStatus, string> = {
  queued: "Queued",
  running: "Running",
  succeeded: "Succeeded",
  failed: "Failed"
};

function formatTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    day: "numeric"
  }).format(new Date(value));
}

function splitTags(value: string) {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function statusCount(jobs: ResearchJob[], status: JobStatus) {
  return jobs.filter((job) => job.status === status).length;
}

function App() {
  const [jobs, setJobs] = useState<ResearchJob[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [query, setQuery] = useState(samplePrompt);
  const [tenant, setTenant] = useState("portfolio-demo");
  const [tags, setTags] = useState("kubernetes, aiq, architecture");
  const [depth, setDepth] = useState<ResearchDepth>("deep");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [ready, jobList] = await Promise.all([getReadiness(), listJobs()]);
    const sortedJobs = [...jobList.jobs].sort((a, b) => {
      const statusDelta = statusOrder[a.status] - statusOrder[b.status];
      if (statusDelta !== 0) return statusDelta;
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    });

    setReadiness(ready);
    setJobs(sortedJobs);
    setSelectedId((current) => current ?? sortedJobs[0]?.id ?? null);
  }, []);

  useEffect(() => {
    void refresh().catch((refreshError: unknown) => {
      setError(refreshError instanceof Error ? refreshError.message : "Unable to load jobs");
    });

    const interval = window.setInterval(() => {
      void refresh().catch(() => undefined);
    }, 5000);

    return () => window.clearInterval(interval);
  }, [refresh]);

  const selectedJob = useMemo(
    () => jobs.find((job) => job.id === selectedId) ?? jobs[0] ?? null,
    [jobs, selectedId]
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const created = await createJob({
        query,
        depth,
        tenant,
        tags: splitTags(tags)
      });
      await refresh();
      setSelectedId(created.job_id);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to create job");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleRunNow(jobId: string) {
    setError(null);
    try {
      await runJob(jobId);
      await refresh();
      setSelectedId(jobId);
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Unable to run job");
    }
  }

  return (
    <main className="app-shell">
      <section className="masthead">
        <div className="brand-lockup">
          <span className="brand-icon">
            <ClusterIcon />
          </span>
          <div>
            <p className="eyebrow">Kubernetes-native AI-Q</p>
            <h1>KubeResearch AIQ</h1>
          </div>
        </div>
        <TopologyMark />
        <div className="runtime-strip" aria-label="Runtime status">
          <span data-state={readiness?.queue ? "good" : "warn"}>
            Queue {readiness?.queue ? "online" : "local"}
          </span>
          <span>Store {readiness?.store ?? "checking"}</span>
          <button className="icon-button" type="button" onClick={() => void refresh()} title="Refresh">
            <RefreshIcon />
          </button>
        </div>
      </section>

      <section className="metrics-row" aria-label="Research job metrics">
        <Metric label="Total jobs" value={jobs.length} />
        <Metric label="Running" value={statusCount(jobs, "running")} tone="blue" />
        <Metric label="Queued" value={statusCount(jobs, "queued")} tone="amber" />
        <Metric label="Succeeded" value={statusCount(jobs, "succeeded")} tone="green" />
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="workspace">
        <form className="submit-pane" onSubmit={handleSubmit}>
          <div className="pane-heading">
            <p className="eyebrow">New run</p>
            <h2>Research request</h2>
          </div>

          <label>
            Topic
            <textarea value={query} onChange={(event) => setQuery(event.target.value)} rows={8} />
          </label>

          <div className="field-grid">
            <label>
              Tenant
              <input value={tenant} onChange={(event) => setTenant(event.target.value)} />
            </label>
            <label>
              Tags
              <input value={tags} onChange={(event) => setTags(event.target.value)} />
            </label>
          </div>

          <fieldset className="segmented-control">
            <legend>Depth</legend>
            {(["auto", "shallow", "deep"] as ResearchDepth[]).map((option) => (
              <label key={option} data-active={depth === option}>
                <input
                  type="radio"
                  name="depth"
                  value={option}
                  checked={depth === option}
                  onChange={() => setDepth(option)}
                />
                {option}
              </label>
            ))}
          </fieldset>

          <button className="primary-action" type="submit" disabled={isSubmitting || query.length < 4}>
            <SendIcon />
            {isSubmitting ? "Creating" : "Create job"}
          </button>
        </form>

        <section className="job-pane" aria-label="Research jobs">
          <div className="pane-heading">
            <p className="eyebrow">Queue</p>
            <h2>Research jobs</h2>
          </div>

          <div className="job-list">
            {jobs.length === 0 ? (
              <p className="empty-state">No jobs yet. Create one to start the worker path.</p>
            ) : (
              jobs.map((job) => (
                <button
                  className="job-row"
                  data-selected={selectedJob?.id === job.id}
                  key={job.id}
                  type="button"
                  onClick={() => setSelectedId(job.id)}
                >
                  <span className="status-dot" data-status={job.status} />
                  <span className="job-copy">
                    <strong>{job.request.query}</strong>
                    <span>
                      {statusLabels[job.status]} · {job.selected_depth ?? job.request.depth} ·{" "}
                      {formatTime(job.updated_at)}
                    </span>
                  </span>
                </button>
              ))
            )}
          </div>
        </section>

        <aside className="report-pane" aria-label="Selected report">
          <div className="pane-heading">
            <p className="eyebrow">Inspector</p>
            <h2>{selectedJob ? "Report" : "No selection"}</h2>
          </div>

          {selectedJob ? (
            <ReportInspector job={selectedJob} onRunNow={handleRunNow} />
          ) : (
            <p className="empty-state">Select a job to inspect plan, citations, and output.</p>
          )}
        </aside>
      </section>
    </main>
  );
}

function Metric({ label, value, tone = "neutral" }: { label: string; value: number; tone?: string }) {
  return (
    <div className="metric" data-tone={tone}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ReportInspector({
  job,
  onRunNow
}: {
  job: ResearchJob;
  onRunNow: (jobId: string) => Promise<void>;
}) {
  return (
    <div className="report-body">
      <div className="report-meta">
        <span className="status-pill" data-status={job.status}>
          {statusLabels[job.status]}
        </span>
        <span>{job.id.slice(0, 8)}</span>
      </div>

      {job.status === "queued" ? (
        <button className="secondary-action" type="button" onClick={() => void onRunNow(job.id)}>
          <PlayIcon />
          Run now
        </button>
      ) : null}

      {job.report ? (
        <a className="secondary-action" href={apiUrl(`/v1/research/${job.id}/report.md`)}>
          <DownloadIcon />
          Download Markdown
        </a>
      ) : null}

      <div className="inspector-block">
        <h3>Plan</h3>
        {job.plan.length > 0 ? (
          <ol>
            {job.plan.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        ) : (
          <p>Waiting for the worker to select a path.</p>
        )}
      </div>

      <div className="inspector-block">
        <h3>Report</h3>
        <pre>{job.report ?? job.error ?? "Report output will appear here."}</pre>
      </div>

      <div className="inspector-block">
        <h3>Citations</h3>
        {job.citations.length > 0 ? (
          <ul>
            {job.citations.map((citation) => (
              <li key={citation}>{citation}</li>
            ))}
          </ul>
        ) : (
          <p>No citations captured yet.</p>
        )}
      </div>
    </div>
  );
}

export default App;
