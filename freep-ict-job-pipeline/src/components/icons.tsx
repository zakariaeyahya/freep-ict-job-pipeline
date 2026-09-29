function baseProps() {
  return {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.75,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className: "h-4 w-4",
  };
}

export function CalendarIcon() {
  return (
    <svg {...baseProps()}>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M16 3v4M8 3v4M3 10h18" />
    </svg>
  );
}

export function ClockIcon() {
  return (
    <svg {...baseProps()}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}

export function SettingsIcon() {
  return (
    <svg {...baseProps()}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" />
    </svg>
  );
}

export function LinkIcon() {
  return (
    <svg {...baseProps()}>
      <path d="M9 15 15 9" />
      <path d="M10 6 12 4a4 4 0 0 1 6 6l-2 2" />
      <path d="M14 18l-2 2a4 4 0 0 1-6-6l2-2" />
    </svg>
  );
}

export function CheckCircleIcon() {
  return (
    <svg {...baseProps()}>
      <circle cx="12" cy="12" r="9" />
      <path d="M8.5 12.5l2.5 2.5 4.5-5" />
    </svg>
  );
}

export function ConvergeIcon() {
  return (
    <svg {...baseProps()}>
      <circle cx="12" cy="12" r="3" />
      <circle cx="12" cy="12" r="9" strokeDasharray="3 3" />
    </svg>
  );
}

export function BarChartIcon() {
  return (
    <svg {...baseProps()}>
      <path d="M4 20V10M12 20V4M20 20v-7" />
    </svg>
  );
}

export function RouteIcon() {
  return (
    <svg {...baseProps()}>
      <circle cx="6" cy="6" r="2.5" />
      <circle cx="18" cy="18" r="2.5" />
      <path d="M8 6h6a4 4 0 0 1 4 4v4" />
    </svg>
  );
}

export function WarningTriangleIcon() {
  return (
    <svg {...baseProps()}>
      <path d="M12 4 3 20h18L12 4Z" />
      <path d="M12 10v4M12 17h.01" />
    </svg>
  );
}

export function DownloadIcon() {
  return (
    <svg {...baseProps()}>
      <path d="M12 4v11M8 11l4 4 4-4" />
      <path d="M4 19h16" />
    </svg>
  );
}

export function PlayIcon() {
  return (
    <svg {...baseProps()} fill="currentColor" stroke="none">
      <path d="M8 5v14l11-7-11-7Z" />
    </svg>
  );
}

export function MoreIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
      <circle cx="12" cy="5" r="1.5" />
      <circle cx="12" cy="12" r="1.5" />
      <circle cx="12" cy="19" r="1.5" />
    </svg>
  );
}

export function BriefcaseIcon() {
  return (
    <svg {...baseProps()}>
      <rect x="3" y="7" width="18" height="13" rx="2" />
      <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      <path d="M3 12h18" />
    </svg>
  );
}

export function ListIcon() {
  return (
    <svg {...baseProps()}>
      <path d="M8 6h13M8 12h13M8 18h13" />
      <path d="M3 6h.01M3 12h.01M3 18h.01" />
    </svg>
  );
}

export function ShieldCheckIcon() {
  return (
    <svg {...baseProps()}>
      <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3Z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}

export function FileIcon() {
  return (
    <svg {...baseProps()}>
      <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M14 3v5h5" />
    </svg>
  );
}

export function DatabaseIcon() {
  return (
    <svg {...baseProps()}>
      <ellipse cx="12" cy="6" rx="8" ry="3" />
      <path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6" />
      <path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" />
    </svg>
  );
}

export function HistoryIcon() {
  return (
    <svg {...baseProps()}>
      <path d="M3 12a9 9 0 1 0 3-6.7" />
      <path d="M3 4v5h5" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}
