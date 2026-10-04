import { Fragment, useEffect, useRef, useState, type ReactNode } from "react";
import { apiUrl } from "../api";
import { duration, hostOf, isLive, stageWords } from "../format";
import type { ResearchJob, Source } from "../types";
import { DownloadIcon, RetryIcon, StopIcon, PlayIcon } from "../icons";

const CITATION = /\[(\d{1,2})\]/g;

function Cited({ text, sources, onCite }: { text: string; sources: Map<number, Source>; onCite: (n: number) => void }) {
  const parts: ReactNode[] = [];
  let last = 0;
  for (const match of text.matchAll(CITATION)) {
    const number = Number(match[1]);
    const source = sources.get(number);
    parts.push(text.slice(last, match.index).replace(/\s+$/, ""));
    parts.push(
      source ? (
        <button key={match.index} className="cite" type="button" title={source.title} onClick={() => onCite(number)}>
          {number}
        </button>
      ) : (
        match[0]
      )
    );
    last = (match.index ?? 0) + match[0].length;
  }
  parts.push(text.slice(last));
  return <>{parts}</>;
}

function Body({ text, sources, onCite }: { text: string; sources: Map<number, Source>; onCite: (n: number) => void }) {
  const lines = text.split("\n").map((line) => line.trim()).filter(Boolean);
  const bullets = lines.filter((line) => line.startsWith("- "));
  if (bullets.length === lines.length && bullets.length > 0) {
    return (
      <ul>
        {bullets.map((line, i) => (
          <li key={i}>
            <Cited text={line.slice(2)} sources={sources} onCite={onCite} />
          </li>
        ))}
      </ul>
    );
  }
  return (
    <>
      {text
        .split(/\n{2,}/)
        .filter((p) => p.trim())
        .map((paragraph, i) => (
          <p key={i}>
            <Cited text={paragraph.trim()} sources={sources} onCite={onCite} />
          </p>
        ))}
    </>
  );
}

interface ReaderProps {
  job: ResearchJob;
  queueAvailable: boolean;
  onCancel: (id: string) => void;
  onRetry: (id: string) => void;
  onRun: (id: string) => void;
}

export function Reader({ job, queueAvailable, onCancel, onRetry, onRun }: ReaderProps) {
  const [active, setActive] = useState<number | null>(null);
  const listRef = useRef<HTMLOListElement>(null);
  const sources = new Map(job.sources.map((s) => [s.id, s]));
  const depth = job.selected_depth ?? job.request.depth;
  const took = duration(job);

  useEffect(() => setActive(null), [job.id]);

  function cite(number: number) {
    setActive(number);
    listRef.current?.querySelector(`[data-source="${number}"]`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  const title = job.title || job.request.query;

  return (
    <article className="reader">
      <header className="reader-head">
        <h2>{title}</h2>
        <p className="reader-query">{job.request.query}</p>
        <dl className="reader-facts">
          <div>
            <dt>Dive</dt>
            <dd>{depth === "auto" ? "Choosing" : depth === "deep" ? "Deep" : "Shallow"}</dd>
          </div>
          <div>
            <dt>Sources</dt>
            <dd>{job.sources.length}</dd>
          </div>
          {took ? (
            <div>
              <dt>Time</dt>
              <dd>{took}</dd>
            </div>
          ) : null}
          {job.metadata.writer ? (
            <div>
              <dt>Written</dt>
              <dd>{job.metadata.writer === "offline" ? "From sources" : "By model"}</dd>
            </div>
          ) : null}
        </dl>
        <div className="reader-actions">
          {job.report ? (
            <a className="button" href={apiUrl(`/v1/research/${job.id}/report.md`)}>
              <DownloadIcon /> Download Markdown
            </a>
          ) : null}
          {job.status === "queued" && !queueAvailable ? (
            <button className="button" type="button" onClick={() => onRun(job.id)}>
              <PlayIcon /> Start dive
            </button>
          ) : null}
          {isLive(job) ? (
            <button className="button quiet" type="button" onClick={() => onCancel(job.id)}>
              <StopIcon /> Cancel dive
            </button>
          ) : null}
          {job.status === "failed" || job.status === "cancelled" ? (
            <button className="button" type="button" onClick={() => onRetry(job.id)}>
              <RetryIcon /> Dive again
            </button>
          ) : null}
        </div>
      </header>

      {job.error ? <p className="reader-error">{job.error}</p> : null}

      {job.summary.length > 0 ? (
        <section className="findings">
          <h3>Key findings</h3>
          <ul>
            {job.summary.map((item, i) => (
              <li key={i}>
                <Cited text={item} sources={sources} onCite={cite} />
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {job.sections.map((section) => (
        <section key={section.title} className="report-section" data-pending={!section.body}>
          <h3>{section.title}</h3>
          <p className="question">{section.question}</p>
          {section.body ? (
            <Body text={section.body} sources={sources} onCite={cite} />
          ) : (
            <p className="pending">
              {job.stage && isLive(job) ? `${stageWords[job.stage].doing}…` : "Not written."}
            </p>
          )}
        </section>
      ))}

      {job.sections.length === 0 && isLive(job) ? (
        <p className="pending">The plan appears here once the question has been surveyed.</p>
      ) : null}

      {job.sources.length > 0 ? (
        <section className="sources">
          <h3>Sources</h3>
          <ol ref={listRef}>
            {job.sources.map((source) => (
              <li key={source.id} data-source={source.id} data-active={active === source.id}>
                <span className="source-number">{source.id}</span>
                <div>
                  <p className="source-title">
                    {source.url ? (
                      <a href={source.url} target="_blank" rel="noreferrer">
                        {source.title}
                      </a>
                    ) : (
                      source.title
                    )}
                  </p>
                  <p className="source-origin">
                    {source.origin === "knowledge" ? "Reference library" : "Web search"}
                    {hostOf(source.url) ? <Fragment>, {hostOf(source.url)}</Fragment> : null}
                  </p>
                  <p className="source-snippet">{source.snippet}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      {job.metadata.writer === "offline" && job.report ? (
        <p className="reader-note">
          Written offline: every sentence is taken from the source it cites. Connect a model to have reports written
          in prose.
        </p>
      ) : null}
    </article>
  );
}
