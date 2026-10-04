import { currentDepth, maxDepthOf, metres, stageWords, statusWords } from "../format";
import { STAGES, type ResearchJob, type Stage } from "../types";

// Progress at the end of each stage, matching the research service.
const STAGE_END: Record<Stage, number> = { survey: 0.08, plan: 0.18, descend: 0.5, draft: 0.9, surface: 1 };
const TICKS = [0, 50, 200, 500, 1000, 2000, 4000];
const FULL = 4000;

const W = 300;
const H = 440;
const TOP = 18;
const BOTTOM = H - 22;
const LINE_X = 70;
const LABEL_X = 150;

/** Depth to y on a square-root scale, so the shallow 200 m stays readable beside 4,000 m. */
const y = (depth: number) => TOP + (BOTTOM - TOP) * Math.sqrt(Math.min(depth, FULL) / FULL);

function stageState(job: ResearchJob, stage: Stage): "done" | "now" | "next" {
  if (job.status === "succeeded") return "done";
  if (!job.stage) return "next";
  const at = STAGES.indexOf(job.stage);
  const index = STAGES.indexOf(stage);
  if (index < at || (index === at && job.progress >= STAGE_END[stage])) return "done";
  return index === at && job.status === "running" ? "now" : "next";
}

export function Sounding({ job }: { job: ResearchJob }) {
  const floor = maxDepthOf(job);
  const depth = currentDepth(job);
  const lead = y(depth);
  const labelTop = TOP + 14;
  // Labels keep the same places on every dive; leader lines run to each stage's depth.
  const labelGap = (BOTTOM - 30 - labelTop) / (STAGES.length - 1);
  const known = Boolean(job.selected_depth) || job.request.depth !== "auto";
  const live = job.status === "running";

  return (
    <figure className="sounding" aria-label={`Dive at ${metres(depth)} of ${metres(floor)}`}>
      <figcaption>
        <span className="sounding-depth">{metres(depth)}</span>
        <span className="sounding-status" data-status={job.status}>
          {statusWords[job.status]}
          {live && job.stage ? `: ${stageWords[job.stage].doing.toLowerCase()}` : ""}
        </span>
      </figcaption>

      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-hidden="true">
        <defs>
          {/* On a chart, shallow water is tinted and deep water is left white. */}
          <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="var(--shoal)" />
            <stop offset={(y(1000) - TOP) / (BOTTOM - TOP)} stopColor="var(--shoal-faint)" />
            <stop offset="1" stopColor="var(--paper)" />
          </linearGradient>
          <pattern id="seabed" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="7" stroke="var(--contour)" strokeWidth="1.2" />
          </pattern>
        </defs>

        <rect x="0" y={TOP} width={W} height={BOTTOM - TOP} fill="url(#water)" />
        {known ? (
          <>
            <rect x="0" y={y(floor)} width={W} height={H - y(floor)} fill="url(#seabed)" opacity="0.55" />
            <line className="seabed-line" x1="0" x2={W} y1={y(floor)} y2={y(floor)} />
          </>
        ) : null}

        {TICKS.filter((t) => !known || t <= floor).map((tick) => (
          <g key={tick} className="contour">
            <line x1="0" x2={W} y1={y(tick)} y2={y(tick)} />
            <text x="6" y={y(tick) - 4}>{tick.toLocaleString("en-US")}</text>
          </g>
        ))}

        <line className="sounding-line" x1={LINE_X} x2={LINE_X} y1={TOP} y2={lead} />

        {STAGES.map((stage, index) => {
          const at = y(STAGE_END[stage] * floor);
          const ly = labelTop + labelGap * index;
          const state = stageState(job, stage);
          return (
            <g key={stage} className="stage-mark" data-state={state}>
              <circle cx={LINE_X} cy={at} r="3.5" />
              <path d={`M${LINE_X + 6} ${at} C ${LINE_X + 40} ${at}, ${LABEL_X - 40} ${ly}, ${LABEL_X - 8} ${ly}`} />
              <text x={LABEL_X} y={ly + 4}>{stageWords[stage].name}</text>
              {job.metadata.stage_seconds?.[stage] !== undefined ? (
                <text className="stage-time" x={W - 8} y={ly + 4} textAnchor="end">
                  {job.metadata.stage_seconds[stage]!.toFixed(1)} s
                </text>
              ) : null}
            </g>
          );
        })}

        <g className="lead" data-live={live} transform={`translate(${LINE_X} ${lead})`}>
          <path d="M0 -9 L6 2 Q0 9 -6 2 Z" />
        </g>
      </svg>
    </figure>
  );
}
