import { clockTime } from "../format";
import type { ResearchJob } from "../types";

export function Timeline({ job }: { job: ResearchJob }) {
  const events = [...job.events].reverse();
  return (
    <section className="timeline" aria-label="Dive log">
      <h3>Log</h3>
      <ol>
        {events.map((event, index) => (
          <li key={`${event.at}-${index}`} data-level={event.level}>
            <time dateTime={event.at}>{clockTime(event.at)}</time>
            <span>{event.message}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
