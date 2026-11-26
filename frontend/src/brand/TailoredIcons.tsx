import React from 'react';

/**
 * Tailored Brand Book v1.2 — 48px-Grid Architectural Icon System
 * Every icon uses a 48x48 viewBox, 3.4px square-cap stroke, miter joins,
 * and an optional single THREAD downward triangle notch on featured icons.
 */
export type BrandIconName =
  | 'radar'
  | 'cv'
  | 'job'
  | 'fit'
  | 'send'
  | 'measure'
  | 'needle'
  | 'scissors'
  | 'tape'
  | 'diff'
  | 'globe'
  | 'credit'
  | 'check'
  | 'save'
  | 'chat'
  | 'filter'
  | 'dashboard'
  | 'pipeline'
  | 'coverLetter'
  | 'archive'
  | 'profile'
  | 'bell'
  | 'settings'
  | 'upload'
  | 'download'
  | 'copy'
  | 'undo'
  | 'swap'
  | 'search'
  | 'plus'
  | 'close'
  | 'back'
  | 'chevronRight'
  | 'chevronDown'
  | 'chevronLeft'
  | 'external'
  | 'eye'
  | 'trash'
  | 'edit'
  | 'lock'
  | 'shield'
  | 'clock'
  | 'collapse'
  | 'expand'
  | 'command'
  | 'alert'
  | 'refresh'
  | 'phone'
  | 'education'
  | 'link'
  | 'calendar'
  | 'hide'
  | 'table'
  | 'board'
  | 'split'
  | 'sliders'
  | 'stop'
  | 'user'
  | 'logout'
  | 'key'
  | 'stitch'
  | 'image';

interface IconSpec {
  paths: React.ReactNode;
  notch?: [number, number];
}

const ICONS: Record<BrandIconName, IconSpec> = {
  // ── 16 Official Brand Book Icons (ds.py lines 346-373) ──
  radar: {
    paths: (
      <>
        <circle cx="21" cy="21" r="13" />
        <path d="M31,31 L43,43" />
      </>
    ),
    notch: [14, 14],
  },
  cv: {
    paths: (
      <>
        <path d="M10,6H30L38,14V42H10Z" />
        <path d="M16,24H32M16,32H32" />
      </>
    ),
    notch: [34, 24],
  },
  job: {
    paths: (
      <>
        <rect x="6" y="16" width="36" height="24" />
        <path d="M17,16V9H31V16M6,28H42" />
      </>
    ),
    notch: [24, 22],
  },
  fit: {
    paths: (
      <>
        <path d="M6,36A18,18 0 0 1 42,36" />
        <path d="M24,36L33,22" />
      </>
    ),
    notch: [24, 36],
  },
  send: {
    paths: (
      <>
        <path d="M5,24L43,7L31,41L23,29Z" />
        <path d="M23,29L43,7" />
      </>
    ),
    notch: [32, 22],
  },
  measure: {
    paths: (
      <>
        <circle cx="24" cy="15" r="8" />
        <path d="M8,43A16,14 0 0 1 40,43" />
      </>
    ),
    notch: [24, 24],
  },
  needle: {
    paths: (
      <>
        <path d="M42,6L12,40" />
        <path d="M12,40L8,44" />
        <ellipse cx="38" cy="10" rx="2" ry="5" transform="rotate(40 38 10)" />
      </>
    ),
    notch: [22, 26],
  },
  scissors: {
    paths: (
      <>
        <circle cx="12" cy="36" r="6" />
        <circle cx="36" cy="36" r="6" />
        <path d="M16,31L38,6M32,31L10,6" />
      </>
    ),
    notch: [24, 22],
  },
  tape: {
    paths: (
      <>
        <rect x="3" y="17" width="42" height="14" />
        <path d="M10,17V24M18,17V22M26,17V24M34,17V22M42,17V24" />
      </>
    ),
    notch: [24, 24],
  },
  diff: {
    paths: (
      <>
        <path d="M8,14H26M8,24H40M8,34H30" />
        <path d="M36,10V20M31,15H41" />
      </>
    ),
    notch: [36, 15],
  },
  globe: {
    paths: (
      <>
        <circle cx="24" cy="24" r="17" />
        <ellipse cx="24" cy="24" rx="7" ry="17" />
        <path d="M7,24H41" />
      </>
    ),
    notch: [24, 24],
  },
  credit: {
    paths: (
      <>
        <circle cx="24" cy="24" r="17" />
        <circle cx="24" cy="24" r="9" strokeDasharray="4 3.5" />
      </>
    ),
    notch: [24, 24],
  },
  check: {
    paths: <path d="M8,26L19,37L40,12" />,
    notch: [24, 36],
  },
  save: {
    paths: <path d="M12,6H36V42L24,32L12,42Z" />,
    notch: [24, 22],
  },
  chat: {
    paths: <path d="M6,8H42V32H22L12,41V32H6Z" />,
    notch: [24, 20],
  },
  filter: {
    paths: <path d="M6,10H42L28,26V40L20,36V26Z" />,
    notch: [24, 18],
  },

  // ── Matching Brand-Pattern Extensions (48px grid, 3.4px butt/miter, notch accent) ──
  dashboard: {
    paths: (
      <>
        <rect x="6" y="6" width="16" height="18" />
        <rect x="26" y="6" width="16" height="12" />
        <rect x="6" y="28" width="16" height="14" />
        <rect x="26" y="22" width="16" height="20" />
      </>
    ),
    notch: [34, 12],
  },
  pipeline: {
    paths: (
      <>
        <rect x="6" y="8" width="10" height="32" />
        <rect x="19" y="8" width="10" height="24" />
        <rect x="32" y="8" width="10" height="16" />
      </>
    ),
    notch: [37, 30],
  },
  coverLetter: {
    paths: (
      <>
        <rect x="6" y="10" width="36" height="28" />
        <path d="M6,12L24,26L42,12" />
      </>
    ),
    notch: [24, 26],
  },
  archive: {
    paths: (
      <>
        <rect x="6" y="8" width="36" height="10" />
        <path d="M9,18V40H39V18" />
        <path d="M18,26H30" />
      </>
    ),
    notch: [24, 13],
  },
  profile: {
    paths: (
      <>
        <rect x="8" y="6" width="32" height="36" />
        <circle cx="24" cy="19" r="5" />
        <path d="M15,34A9,8 0 0 1 33,34" />
      </>
    ),
    notch: [24, 29],
  },
  bell: {
    paths: (
      <>
        <path d="M12,30V20A12,12 0 0 1 36,20V30L40,35H8Z" />
        <path d="M20,38A4,4 0 0 0 28,38" />
      </>
    ),
    notch: [24, 24],
  },
  settings: {
    paths: (
      <>
        <circle cx="24" cy="24" r="7" />
        <path d="M24,6V12M24,36V42M6,24H12M36,24H42M11,11L15,15M33,33L37,37M37,11L33,15M15,33L11,37" />
      </>
    ),
    notch: [24, 24],
  },
  upload: {
    paths: (
      <>
        <path d="M24,32V9M14,18L24,8L34,18" />
        <path d="M8,33V40H40V33" />
      </>
    ),
  },
  download: {
    paths: (
      <>
        <path d="M24,8V31M14,22L24,32L34,22" />
        <path d="M8,34V40H40V34" />
      </>
    ),
  },
  copy: {
    paths: (
      <>
        <rect x="16" y="16" width="24" height="24" />
        <path d="M32,16V8H8V32H16" />
      </>
    ),
  },
  undo: {
    paths: (
      <>
        <path d="M15,12L7,20L15,28" />
        <path d="M8,20H29A11,11 0 0 1 40,31V36" />
      </>
    ),
  },
  swap: {
    paths: (
      <>
        <path d="M8,16H38M31,9L39,16L31,23" />
        <path d="M40,32H10M17,25L9,32L17,39" />
      </>
    ),
  },
  search: {
    paths: (
      <>
        <circle cx="21" cy="21" r="13" />
        <path d="M31,31L42,42" />
      </>
    ),
  },
  plus: {
    paths: <path d="M24,8V40M8,24H40" />,
  },
  close: {
    paths: <path d="M11,11L37,37M37,11L11,37" />,
  },
  back: {
    paths: <path d="M40,24H10M20,13L9,24L20,35" />,
  },
  chevronRight: {
    paths: <path d="M18,10L32,24L18,38" />,
  },
  chevronLeft: {
    paths: <path d="M30,10L16,24L30,38" />,
  },
  chevronDown: {
    paths: <path d="M10,18L24,32L38,18" />,
  },
  external: {
    paths: (
      <>
        <path d="M27,9H39V21" />
        <path d="M39,9L21,27" />
        <path d="M21,11H9V39H37V27" />
      </>
    ),
  },
  eye: {
    paths: (
      <>
        <path d="M4,24C10,14 17,11 24,11C31,11 38,14 44,24C38,34 31,37 24,37C17,37 10,34 4,24Z" />
        <circle cx="24" cy="24" r="5" />
      </>
    ),
  },
  trash: {
    paths: (
      <>
        <path d="M8,13H40" />
        <path d="M18,13V8H30V13" />
        <path d="M12,13L15,41H33L36,13" />
      </>
    ),
  },
  edit: {
    paths: (
      <>
        <path d="M9,39L12,28L33,7L41,15L20,36Z" />
        <path d="M28,12L36,20" />
      </>
    ),
  },
  lock: {
    paths: (
      <>
        <rect x="10" y="21" width="28" height="20" />
        <path d="M16,21V15A8,8 0 0 1 32,15V21" />
      </>
    ),
  },
  shield: {
    paths: <path d="M24,6L40,12V25C40,34 32,40 24,43C16,40 8,34 8,25V12Z" />,
    notch: [24, 24],
  },
  clock: {
    paths: (
      <>
        <circle cx="24" cy="24" r="17" />
        <path d="M24,14V25L32,30" />
      </>
    ),
  },
  collapse: {
    paths: (
      <>
        <path d="M9,8V40" />
        <path d="M39,24H17M25,16L17,24L25,32" />
      </>
    ),
  },
  expand: {
    paths: (
      <>
        <path d="M39,8V40" />
        <path d="M9,24H31M23,16L31,24L23,32" />
      </>
    ),
  },
  command: {
    paths: (
      <>
        <rect x="18" y="18" width="12" height="12" />
        <rect x="8" y="8" width="10" height="10" />
        <rect x="30" y="8" width="10" height="10" />
        <rect x="8" y="30" width="10" height="10" />
        <rect x="30" y="30" width="10" height="10" />
      </>
    ),
  },
  alert: {
    paths: (
      <>
        <path d="M24,7L43,40H5Z" />
        <path d="M24,19V28M24,33V35" />
      </>
    ),
  },
  refresh: {
    paths: (
      <>
        <path d="M38,16A16,16 0 1 0 39,29" />
        <path d="M28,16H39V5" />
      </>
    ),
  },
  phone: {
    paths: (
      <>
        <rect x="13" y="6" width="22" height="36" />
        <path d="M13,12H35M13,35H35" />
      </>
    ),
  },
  education: {
    paths: (
      <>
        <path d="M4,20L24,10L44,20L24,30Z" />
        <path d="M12,24V35C12,38 36,38 36,35V24" />
        <path d="M40,22V35" />
      </>
    ),
  },
  link: {
    paths: (
      <>
        <path d="M20,28L28,20" />
        <path d="M17,19L10,26A7,7 0 0 0 20,36L24,32" />
        <path d="M31,29L38,22A7,7 0 0 0 28,12L24,16" />
      </>
    ),
  },
  calendar: {
    paths: (
      <>
        <rect x="7" y="11" width="34" height="30" />
        <path d="M7,20H41M16,6V14M32,6V14" />
      </>
    ),
  },
  hide: {
    paths: (
      <>
        <path d="M6,24C12,15 18,12 24,12C30,12 36,15 42,24" />
        <path d="M9,9L39,39" />
      </>
    ),
  },
  table: {
    paths: (
      <>
        <rect x="6" y="8" width="36" height="32" />
        <path d="M6,18H42M6,29H42M19,18V40" />
      </>
    ),
  },
  board: {
    paths: (
      <>
        <rect x="6" y="8" width="10" height="28" />
        <rect x="19" y="8" width="10" height="20" />
        <rect x="32" y="8" width="10" height="32" />
      </>
    ),
  },
  split: {
    paths: (
      <>
        <rect x="6" y="8" width="36" height="32" />
        <path d="M21,8V40" />
      </>
    ),
  },
  sliders: {
    paths: (
      <>
        <path d="M7,13H41M7,24H41M7,35H41" />
        <rect x="14" y="9" width="6" height="8" />
        <rect x="28" y="20" width="6" height="8" />
        <rect x="18" y="31" width="6" height="8" />
      </>
    ),
  },
  stop: {
    paths: <rect x="12" y="12" width="24" height="24" />,
  },
  user: {
    paths: (
      <>
        <circle cx="24" cy="16" r="7" />
        <path d="M10,41A14,12 0 0 1 38,41" />
      </>
    ),
  },
  logout: {
    paths: (
      <>
        <path d="M22,8H9V40H22" />
        <path d="M18,24H40M31,15L40,24L31,33" />
      </>
    ),
  },
  key: {
    paths: (
      <>
        <circle cx="16" cy="24" r="8" />
        <path d="M24,24H42M35,24V31M41,24V31" />
      </>
    ),
  },
  stitch: {
    paths: <path d="M6,24H13M19,24H29M35,24H42" />,
    notch: [24, 15],
  },
  image: {
    paths: (
      <>
        <rect x="6" y="8" width="36" height="32" />
        <path d="M6,32L18,20L27,29L33,23L42,32" />
        <circle cx="32" cy="16" r="3" />
      </>
    ),
    notch: [32, 16],
  },
};

export interface TailoredIconProps {
  name: BrandIconName;
  size?: number;
  color?: string;
  accent?: string;
  withNotch?: boolean;
  strokeWidth?: number;
  style?: React.CSSProperties;
  className?: string;
}

export const TailoredIcon: React.FC<TailoredIconProps> = ({
  name,
  size = 18,
  color = 'currentColor',
  accent = 'var(--thread)',
  withNotch = false,
  strokeWidth = 3.4,
  style,
  className,
}) => {
  const spec = ICONS[name] || ICONS.check;
  const pos = spec.notch;
  return (
    <svg
      viewBox="0 0 48 48"
      width={size}
      height={size}
      className={className}
      style={{ display: 'inline-block', flexShrink: 0, ...style }}
      aria-hidden="true"
    >
      <g
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinejoin="miter"
        strokeLinecap="butt"
      >
        {spec.paths}
      </g>
      {withNotch && pos && (
        <path
          d={`M${pos[0] - 5},${pos[1] - 4}H${pos[0] + 5}L${pos[0]},${pos[1] + 5}Z`}
          fill={accent}
          stroke="none"
        />
      )}
    </svg>
  );
};
