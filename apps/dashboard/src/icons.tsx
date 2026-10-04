import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function Icon({ children, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" {...props}>
      {children}
    </svg>
  );
}

export const DiveIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M12 3v13" />
    <path d="m7 11 5 5 5-5" />
    <path d="M4 20c2.5 0 2.5-1.5 5-1.5s2.5 1.5 5 1.5 2.5-1.5 5-1.5" />
  </Icon>
);

export const DownloadIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M12 4v11" />
    <path d="m7 10 5 5 5-5" />
    <path d="M5 20h14" />
  </Icon>
);

export const PlayIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M8 5v14l11-7L8 5Z" />
  </Icon>
);

export const StopIcon = (props: IconProps) => (
  <Icon {...props}>
    <rect x="6" y="6" width="12" height="12" rx="1.5" />
  </Icon>
);

export const RetryIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M4 12a8 8 0 1 0 2.4-5.7" />
    <path d="M4 4v4.5h4.5" />
  </Icon>
);

/** The brand mark: a sounding lead on its line, over two contour lines. */
export const LeadMark = (props: IconProps) => (
  <svg viewBox="0 0 32 32" aria-hidden="true" focusable="false" {...props}>
    <path d="M3 22c4.3 0 4.3-2 8.6-2s4.3 2 8.6 2 4.3-2 8.6-2" className="mark-contour" />
    <path d="M3 27c4.3 0 4.3-2 8.6-2s4.3 2 8.6 2 4.3-2 8.6-2" className="mark-contour" />
    <path d="M16 2v9" className="mark-line" />
    <path d="M16 10.5 20 18q-4 4.5-8 0Z" className="mark-lead" />
  </svg>
);
