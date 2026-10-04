import { maxDepthOf, relativeTime, statusWords } from "../format";
import type { ResearchJob } from "../types";

function DepthGlyph({ job }: { job: ResearchJob }) {
  // A miniature sounding: the bar's length is the dive's floor, the fill is how far it got.
  const floor = maxDepthOf(job);
  const length = floor === 4000 ? 1 : 0.34;
  return (
    <span className="depth-glyph" aria-hidden="true">
      <span className="depth-glyph-floor" style={{ height: `${length * 100}%` }}>
        <span className="depth-glyph-fill" style={{ height: `${job.progress * 100}%` }} />
      </span>
    </span>
  );
}

interface DiveLogProps {
  jobs: ResearchJob[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function DiveLog({ jobs, selectedId, onSelect }: DiveLogProps) {
  return (
    <nav className="dive-log" aria-label="Dives">
      <h2>Dives</h2>
      {jobs.length === 0 ? (
        <p className="log-empty">Your dives will be listed here.</p>
      ) : (
        <ul>
          {jobs.map((job) => (
            <li key={job.id}>
              <button
                type="button"
                className="log-entry"
                aria-current={job.id === selectedId ? "true" : undefined}
                onClick={() => onSelect(job.id)}
              >
                <DepthGlyph job={job} />
                <span className="log-text">
                  <span className="log-query">{job.request.query}</span>
                  <span className="log-meta">
                    <span data-status={job.status}>{statusWords[job.status]}</span>
                    <span>{relativeTime(job.created_at)}</span>
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </nav>
  );
}
