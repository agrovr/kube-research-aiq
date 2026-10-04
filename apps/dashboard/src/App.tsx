import { useCallback, useEffect, useMemo, useState } from "react";
import { cancelJob, createJob, followJob, getMeta, listJobs, retryJob, runJob } from "./api";
import { AskBar } from "./components/AskBar";
import { DiveLog } from "./components/DiveLog";
import { Reader } from "./components/Reader";
import { Sounding } from "./components/Sounding";
import { Timeline } from "./components/Timeline";
import { isLive } from "./format";
import { LeadMark } from "./icons";
import type { MetaResponse, ResearchDepth, ResearchJob } from "./types";
import "./styles.css";

function errorText(error: unknown, fallback: string) {
  return error instanceof Error && error.message ? error.message : fallback;
}

function Readout({ meta, jobs }: { meta: MetaResponse | null; jobs: ResearchJob[] }) {
  if (!meta) return <p className="readout">Connecting to the research service…</p>;
  const diving = jobs.filter((j) => j.status === "running").length;
  const waiting = jobs.filter((j) => j.status === "queued").length;
  const web = meta.retrieval.find((r) => r.startsWith("web:"));
  return (
    <dl className="readout">
      <div>
        <dt>Diving</dt>
        <dd>{diving}</dd>
      </div>
      <div>
        <dt>Waiting</dt>
        <dd>{waiting}</dd>
      </div>
      <div>
        <dt>Queue</dt>
        <dd data-good={meta.queue.available}>{meta.queue.available ? "Redis" : "In the API"}</dd>
      </div>
      <div>
        <dt>Sources</dt>
        <dd>
          {meta.library_documents} briefs{web ? ` and ${web.slice(4)}` : ""}
        </dd>
      </div>
      <div>
        <dt>Writer</dt>
        <dd>{meta.writer === "model" && meta.models ? meta.models.deep : "Offline"}</dd>
      </div>
    </dl>
  );
}

export default function App() {
  const [jobs, setJobs] = useState<ResearchJob[]>([]);
  const [meta, setMeta] = useState<MetaResponse | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const upsert = useCallback((job: ResearchJob) => {
    setJobs((current) => {
      const index = current.findIndex((j) => j.id === job.id);
      if (index === -1) return [job, ...current];
      const next = [...current];
      next[index] = job;
      return next;
    });
  }, []);

  const refresh = useCallback(async () => {
    const [list, info] = await Promise.all([listJobs(), getMeta()]);
    setJobs(list.jobs);
    setMeta(info);
    setLoaded(true);
    setError(null);
    setSelectedId((current) => current ?? list.jobs[0]?.id ?? null);
  }, []);

  const anyLive = jobs.some(isLive);

  useEffect(() => {
    const load = () =>
      refresh().catch((e: unknown) => setError(errorText(e, "The research service is not reachable.")));
    void load();
    const timer = window.setInterval(load, anyLive ? 2000 : 8000);
    return () => window.clearInterval(timer);
  }, [refresh, anyLive]);

  const selected = useMemo(
    () => jobs.find((job) => job.id === selectedId) ?? jobs[0] ?? null,
    [jobs, selectedId]
  );

  // Stream the selected dive while it is live; the list poll covers the others.
  const selectedLive = selected ? isLive(selected) : false;
  const selectedJobId = selected?.id;
  useEffect(() => {
    if (!selectedJobId || !selectedLive) return;
    return followJob(selectedJobId, upsert, () => undefined);
  }, [selectedJobId, selectedLive, upsert]);

  async function act(action: () => Promise<unknown>, fallback: string) {
    setError(null);
    try {
      await action();
      await refresh();
    } catch (e) {
      setError(errorText(e, fallback));
    }
  }

  async function dive(query: string, depth: ResearchDepth) {
    setBusy(true);
    setError(null);
    try {
      const created = await createJob({ query, depth, tenant: "console", tags: [] });
      setSelectedId(created.job_id);
      await refresh();
      return true;
    } catch (e) {
      setError(errorText(e, "The dive could not be started."));
      return false;
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header className="masthead">
        <div className="wordmark">
          <LeadMark className="wordmark-mark" />
          <div>
            <h1>KubeResearch AIQ</h1>
            <p>Research agents that dive as deep as the question.</p>
          </div>
        </div>
        <Readout meta={meta} jobs={jobs} />
      </header>

      <AskBar busy={busy} onDive={dive} />

      {error ? (
        <p className="alert" role="alert">
          {error}
        </p>
      ) : null}

      <main className="workspace">
        <DiveLog jobs={jobs} selectedId={selected?.id ?? null} onSelect={setSelectedId} />

        {selected ? (
          <>
            <Reader
              job={selected}
              queueAvailable={meta?.queue.available ?? false}
              onCancel={(id) => void act(() => cancelJob(id), "The dive could not be cancelled.")}
              onRetry={(id) => void act(() => retryJob(id), "The dive could not be restarted.")}
              onRun={(id) => void act(() => runJob(id), "The dive could not be started.")}
            />
            <aside className="instruments" aria-label="Dive instruments">
              <Sounding job={selected} />
              <div className="instrument-notes">
                {selected.metadata.route_reason ? <p className="route">{selected.metadata.route_reason}</p> : null}
                <Timeline job={selected} />
              </div>
            </aside>
          </>
        ) : (
          <section className="empty">
            <h2>{loaded ? "No dives yet" : "Loading dives"}</h2>
            <p>
              Ask a question above. Shallow dives return one cited answer in seconds; deep dives plan the question,
              gather sources for each part and write a full report.
            </p>
          </section>
        )}
      </main>
    </div>
  );
}
