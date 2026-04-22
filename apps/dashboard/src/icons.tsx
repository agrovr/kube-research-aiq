import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

export function SendIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path d="M4 11.5 20 4l-4.5 16-3.2-6.4L4 11.5Z" />
      <path d="m12.3 13.6 3.2-3.9" />
    </svg>
  );
}

export function RefreshIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path d="M20 7v5h-5" />
      <path d="M4 17v-5h5" />
      <path d="M18.2 9A7 7 0 0 0 6.1 7.2L4 12" />
      <path d="M5.8 15A7 7 0 0 0 17.9 16.8L20 12" />
    </svg>
  );
}

export function PlayIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path d="M8 5v14l11-7L8 5Z" />
    </svg>
  );
}

export function DownloadIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path d="M12 4v11" />
      <path d="m7 10 5 5 5-5" />
      <path d="M5 20h14" />
    </svg>
  );
}

export function ClusterIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true" {...props}>
      <path d="M16 3 27.3 9.5v13L16 29 4.7 22.5v-13L16 3Z" />
      <path d="M16 16 27.3 9.5M16 16 4.7 9.5M16 16v13" />
      <circle cx="16" cy="16" r="3.2" />
    </svg>
  );
}

export function TopologyMark() {
  return (
    <svg className="topology-mark" viewBox="0 0 640 180" aria-hidden="true">
      <path d="M24 86h96l52-54h112l48 54h96l56-42h132" />
      <path d="M24 128h140l38-36h92l40 36h92l58-72h132" />
      <g>
        <circle cx="24" cy="86" r="5" />
        <circle cx="120" cy="86" r="5" />
        <circle cx="172" cy="32" r="5" />
        <circle cx="284" cy="32" r="5" />
        <circle cx="332" cy="86" r="5" />
        <circle cx="428" cy="86" r="5" />
        <circle cx="484" cy="44" r="5" />
        <circle cx="616" cy="44" r="5" />
        <circle cx="164" cy="128" r="5" />
        <circle cx="202" cy="92" r="5" />
        <circle cx="294" cy="92" r="5" />
        <circle cx="426" cy="128" r="5" />
        <circle cx="616" cy="56" r="5" />
      </g>
    </svg>
  );
}
