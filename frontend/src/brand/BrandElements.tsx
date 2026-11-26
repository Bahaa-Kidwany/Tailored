import React from 'react';
import { BRAND_SVGS, type BrandVectorAsset } from './brandSvgs';
import { TailoredIcon, type BrandIconName } from './TailoredIcons';

function renderAsset(
  asset: BrandVectorAsset,
  height: number,
  color: string,
  thread: string,
  widthOverride?: number
) {
  const parts = asset.viewBox.split(/\s+/).map(Number);
  const vw = parts[2] || 100;
  const vh = parts[3] || 100;
  const w = widthOverride ?? (height * vw) / vh;
  return (
    <svg
      viewBox={asset.viewBox}
      width={w}
      height={height}
      style={{ display: 'block', flexShrink: 0 }}
      aria-hidden="true"
    >
      {asset.paths.map((p, idx) => (
        <path
          key={idx}
          d={p.d}
          fill={p.fillRole === 'thread' ? thread : color}
          fillRule={p.fillRule}
        />
      ))}
    </svg>
  );
}

export interface BrandLockupProps {
  variant?: 'horizontal' | 'stacked' | 'symbol' | 'wordmark' | 'bilingual';
  mode?: 'thread' | 'knock' | 'solid';
  size?: number;
  color?: string;
  threadColor?: string;
  dir?: 'ltr' | 'rtl';
}

export const BrandLockup: React.FC<BrandLockupProps> = ({
  variant = 'horizontal',
  mode = 'thread',
  size = 28,
  color = 'var(--ink)',
  threadColor = 'var(--thread)',
  dir = 'ltr',
}) => {
  const markAsset =
    mode === 'thread'
      ? BRAND_SVGS.markThread
      : mode === 'knock'
        ? BRAND_SVGS.markKnock
        : BRAND_SVGS.markSolid;

  const enAsset =
    mode === 'thread'
      ? BRAND_SVGS.wordEnThread
      : mode === 'knock'
        ? BRAND_SVGS.wordEnKnock
        : BRAND_SVGS.wordEnSolid;

  const arAsset = mode === 'knock' ? BRAND_SVGS.wordArKnock : BRAND_SVGS.wordArThread;

  if (variant === 'symbol') {
    const resolved = size < 32 ? BRAND_SVGS.markSolid : size < 44 ? BRAND_SVGS.markKnock : markAsset;
    return renderAsset(resolved, size, color, threadColor, size);
  }

  if (variant === 'wordmark') {
    return dir === 'rtl'
      ? renderAsset(arAsset, size * 0.9, color, threadColor)
      : renderAsset(enAsset, size * 0.85, color, threadColor);
  }

  if (variant === 'stacked') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: size * 0.18 }}>
        {renderAsset(markAsset, size, color, threadColor, size)}
        {renderAsset(dir === 'rtl' ? arAsset : enAsset, size * 0.52, color, threadColor)}
      </div>
    );
  }

  if (variant === 'bilingual') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: size * 0.28 }}>
        {renderAsset(markAsset, size * 1.15, color, threadColor, size * 1.15)}
        <div style={{ width: 2, height: size, background: color, opacity: 0.8 }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: size * 0.15 }}>
          {renderAsset(enAsset, size * 0.56, color, threadColor)}
          {renderAsset(arAsset, size * 0.48, color, threadColor)}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: size * 0.28 }}>
      {renderAsset(size < 26 ? BRAND_SVGS.markSolid : markAsset, size, color, threadColor, size)}
      {renderAsset(dir === 'rtl' ? arAsset : enAsset, size * 0.78, color, threadColor)}
    </div>
  );
};

export interface FitDialProps {
  score: number;
  size?: number;
  color?: string;
  showNumber?: boolean;
  label?: string;
}

/**
 * Exact Brand Book Half-Moon Fit Score Dial (ds.py lines 329-342)
 * Score >= 75 -> --green, 50..74 -> --amber, < 50 -> --alarm
 */
export const FitDial: React.FC<FitDialProps> = ({
  score,
  size = 86,
  color = 'var(--ink)',
  showNumber = true,
  label = 'FIT',
}) => {
  const clamped = Math.max(0, Math.min(100, Math.round(score)));
  const accent = clamped >= 75 ? 'var(--green)' : clamped >= 50 ? 'var(--amber)' : 'var(--alarm)';
  const cx = 60;
  const cy = 64;
  const r = 48;

  const ticks = [];
  for (let i = 0; i <= 40; i++) {
    const a = Math.PI * (1 - i / 40);
    const r1 = r - (i % 5 === 0 ? 14 : 8);
    const x1 = cx + r * Math.cos(a);
    const y1 = cy - r * Math.sin(a);
    const x2 = cx + r1 * Math.cos(a);
    const y2 = cy - r1 * Math.sin(a);
    const on = i <= (clamped * 40) / 100;
    ticks.push(
      <path
        key={i}
        d={`M${x1.toFixed(1)},${y1.toFixed(1)}L${x2.toFixed(1)},${y2.toFixed(1)}`}
        stroke={on ? accent : color}
        strokeWidth={i % 5 === 0 ? 2.6 : 1.8}
        opacity={on ? 1 : 0.32}
      />
    );
  }

  return (
    <svg
      viewBox="0 0 120 88"
      width={size}
      height={size * 0.73}
      style={{ display: 'block', flexShrink: 0 }}
      aria-label={`Fit score ${clamped}`}
    >
      {ticks}
      {showNumber && (
        <>
          <text
            x="60"
            y="61"
            textAnchor="middle"
            style={{
              fontFamily: 'var(--font-voice)',
              fontWeight: 600,
              fontSize: 30,
              fill: color,
              fontVariationSettings: "'SOFT' 100, 'opsz' 72",
            }}
          >
            {clamped}
          </text>
          <text
            x="60"
            y="78"
            textAnchor="middle"
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 8.5,
              letterSpacing: '1.5px',
              fill: color,
              opacity: 0.7,
            }}
          >
            {label}
          </text>
        </>
      )}
    </svg>
  );
};

export interface MeasureRulerBarProps {
  value: number;
  width?: number;
  color?: string;
  accent?: string;
}

/**
 * Brand Book Measuring-Tape Ruler Bar (p_type.py line 152)
 */
export const MeasureRulerBar: React.FC<MeasureRulerBarProps> = ({
  value,
  width = 240,
  color = 'var(--ink)',
  accent = 'var(--thread)',
}) => {
  const clamped = Math.max(0, Math.min(100, value));
  const unitPx = 6;
  const count = Math.floor(width / unitPx);
  const paths: string[] = [];
  for (let i = 0; i <= count; i++) {
    const x = i * unitPx;
    const h = i % 10 === 0 ? 11 : i % 5 === 0 ? 7 : 4;
    paths.push(`M${x},0V${h}`);
  }
  return (
    <div style={{ position: 'relative', width: '100%', height: 14 }}>
      <svg viewBox={`0 0 ${width} 14`} width="100%" height="14" preserveAspectRatio="none" style={{ opacity: 0.4 }}>
        <path d={paths.join('')} stroke={color} strokeWidth="1.2" fill="none" />
      </svg>
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          height: 8,
          width: `${clamped}%`,
          background: accent,
          opacity: 0.9,
        }}
      />
    </div>
  );
};

/**
 * Brand Book Pattern Pieces Background SVG (ds.py shape/layplan aesthetic)
 */
export const LayplanPattern: React.FC<{ opacity?: number; color?: string }> = ({
  opacity = 0.14,
  color = 'var(--chalk)',
}) => (
  <svg
    viewBox="0 0 1200 540"
    width="100%"
    height="100%"
    preserveAspectRatio="xMidYMid slice"
    style={{ position: 'absolute', inset: 0, pointerEvents: 'none', opacity }}
    aria-hidden="true"
  >
    <g fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round">
      {/* Front Bodice Piece */}
      <path d="M60,50 L210,50 L210,270 L60,270 Z" />
      <path d="M72,62 L198,62 L198,258 L72,258 Z" strokeDasharray="7 6" stroke="var(--thread)" />
      <path d="M135,100 V215 M129,112 L135,100 L141,112 M129,203 L135,215 L141,203" strokeWidth="1.4" />
      {/* Sleeve Arc */}
      <path d="M310,120 C340,40 420,40 450,120 L450,290 L310,290 Z" />
      <path d="M322,126 C348,54 412,54 438,126 L438,278 L322,278 Z" strokeDasharray="7 6" stroke="var(--thread)" />
      {/* Collar Curve */}
      <path d="M560,60 C640,30 740,85 820,48 C795,120 700,175 600,165 C555,160 538,105 560,60 Z" />
      <ellipse cx="660" cy="112" rx="22" ry="10" />
      {/* Pocket Notch Piece */}
      <path d="M900,80 L1030,80 L1030,190 L965,240 L900,190 Z" />
      <path d="M912,92 L1018,92 L1018,184 L965,226 L912,184 Z" strokeDasharray="7 6" stroke="var(--thread)" />
      {/* Placket & Cuff */}
      <path d="M260,340 L520,340 L485,400 L260,400 Z" />
      <path d="M620,290 L860,290 C845,355 635,355 620,290 Z" />
      <path d="M920,310 L980,310 L980,500 L920,480 Z" />
      {/* Sweeping French Armhole Curve */}
      <path d="M-20,500 C320,515 560,80 1220,95" stroke="var(--thread)" strokeWidth="3.5" />
    </g>
  </svg>
);

export interface EmptyStateProps {
  icon: BrandIconName;
  headline: string;
  subtext: string;
  ctaLabel: string;
  onCta: () => void;
  secondaryLabel?: string;
  onSecondary?: () => void;
}

/**
 * Brand Book Empty State (p_ui.py 06.10):
 * Muted N300 icon with THREAD notch + Plex headline + N500 copy + 1 THREAD diagonal CTA
 */
export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  headline,
  subtext,
  ctaLabel,
  onCta,
  secondaryLabel,
  onSecondary,
}) => (
  <div
    className="t-card"
    style={{
      padding: '44px 32px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      textAlign: 'center',
      gap: 14,
      maxWidth: 460,
      margin: '32px auto',
    }}
  >
    <TailoredIcon name={icon} size={46} color="var(--n300)" accent="var(--thread)" withNotch />
    <div style={{ fontSize: 18, fontWeight: 600 }}>{headline}</div>
    <div style={{ fontSize: 14, color: 'var(--n500)', lineHeight: 1.5, maxWidth: 340 }}>{subtext}</div>
    <div style={{ display: 'flex', gap: 10, marginTop: 6, flexWrap: 'wrap', justifyContent: 'center' }}>
      <button type="button" className="t-btn t-btn--primary t-btn--sm" onClick={onCta}>
        {ctaLabel}
      </button>
      {secondaryLabel && onSecondary && (
        <button type="button" className="t-btn t-btn--outline t-btn--sm" onClick={onSecondary}>
          {secondaryLabel}
        </button>
      )}
    </div>
  </div>
);

export const BrandAlert: React.FC<{
  variant: 'error' | 'warn' | 'info' | 'success';
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}> = ({ variant, title, message, actionLabel, onAction }) => (
  <div className={`t-alert t-alert--${variant === 'info' ? '' : variant}`}>
    <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{title}</div>
    <div style={{ fontSize: 13.5, color: 'var(--n700)', lineHeight: 1.45 }}>{message}</div>
    {actionLabel && onAction && (
      <button
        type="button"
        onClick={onAction}
        style={{
          marginTop: 8,
          background: 'transparent',
          border: 'none',
          padding: 0,
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: 'var(--ink)',
          borderBottom: '2px dashed var(--thread)',
          cursor: 'pointer',
        }}
      >
        {actionLabel}
      </button>
    )}
  </div>
);

/**
 * Brand Book v1.2 Studio Atelier Backdrop (French curves, pattern pieces, craft tools & crossing sweeps)
 * Styled like a subtle dark WhatsApp wallpaper — designed to sit cleanly beneath floating sheets & Coach cards.
 */
export const AtelierFrenchCurveBackdrop: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      inset: 0,
      pointerEvents: 'none',
      overflow: 'hidden',
      zIndex: 0,
    }}
    aria-hidden="true"
  >
    {/* Layer 1: Tiled French Curves, Pattern Pieces & Tailor Tools */}
    <svg
      width="100%"
      height="100%"
      style={{ position: 'absolute', inset: 0, display: 'block' }}
    >
      <defs>
        <pattern
          id="tailoredAtelierTile"
          width="460"
          height="460"
          patternUnits="userSpaceOnUse"
        >
          {/* Primary French Curve Template (ds.py fcurve) */}
          <g
            transform="translate(22 36) rotate(-14) scale(0.36)"
            fill="none"
            stroke="var(--chalk)"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path
              d="M14,122 C40,122 70,52 150,40 C240,26 300,96 392,56 C430,40 470,34 506,30 C470,120 380,196 250,196 C150,196 60,190 28,168 C14,158 8,140 14,122Z"
              strokeWidth="4.2"
              strokeOpacity="0.09"
            />
            <path
              d="M14,122 C40,122 70,52 150,40 C240,26 300,96 392,56 C430,40 470,34 506,30 C470,120 380,196 250,196 C150,196 60,190 28,168 C14,158 8,140 14,122Z"
              transform="translate(260 113) scale(0.88) translate(-260 -113)"
              stroke="var(--thread)"
              strokeWidth="3.2"
              strokeDasharray="12 10"
              strokeOpacity="0.15"
            />
            <ellipse cx="170" cy="128" rx="34" ry="15" transform="rotate(-14 170 128)" strokeWidth="3.6" strokeOpacity="0.085" />
            <ellipse cx="300" cy="128" rx="26" ry="11" transform="rotate(-6 300 128)" strokeWidth="3.6" strokeOpacity="0.085" />
            <circle cx="402" cy="112" r="9" strokeWidth="3.6" strokeOpacity="0.085" />
            <path d="M90,70l-3,14 M150,42l-1,14 M220,38l1,14 M320,84l3,13 M440,40l3,14" strokeWidth="2.8" strokeOpacity="0.085" />
          </g>

          {/* Curved Collar Arc Piece */}
          <g
            transform="translate(212 34) rotate(14)"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path
              d="M8,62 C36,12 104,12 132,62 C96,46 44,46 8,62 Z"
              stroke="var(--chalk)"
              strokeWidth="1.4"
              strokeOpacity="0.085"
            />
            <path
              d="M22,55 C44,24 96,24 118,55"
              stroke="var(--thread)"
              strokeWidth="1.2"
              strokeDasharray="5 5"
              strokeOpacity="0.14"
            />
          </g>

          {/* Tailor's Scissors (48px Brand Icon Spec) */}
          <g
            transform="translate(362 34) rotate(24) scale(1.45)"
            fill="none"
            stroke="var(--chalk)"
            strokeWidth="1.1"
            strokeOpacity="0.09"
            strokeLinecap="square"
            strokeLinejoin="miter"
          >
            <circle cx="12" cy="36" r="6" />
            <circle cx="36" cy="36" r="6" />
            <path d="M16,31L38,6 M32,31L10,6" />
            <circle cx="24" cy="21" r="2.1" fill="var(--chalk)" fillOpacity="0.14" stroke="none" />
          </g>

          {/* Front Bodice Piece with Armhole Cutout & Grainline */}
          <g
            transform="translate(38 192) rotate(-7) scale(0.62)"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path
              d="M0,18 Q36,36 62,0 L124,0 Q114,58 148,74 L148,205 L0,205 Z"
              stroke="var(--chalk)"
              strokeWidth="2"
              strokeOpacity="0.085"
            />
            <path
              d="M12,30 Q40,46 66,12 L112,12 Q105,64 136,80 L136,193 L12,193 Z"
              stroke="var(--thread)"
              strokeWidth="1.8"
              strokeDasharray="8 7"
              strokeOpacity="0.13"
            />
            <path
              d="M74,64 V162 M68,76 L74,64 L80,76 M68,150 L74,162 L80,150"
              stroke="var(--chalk)"
              strokeWidth="1.6"
              strokeOpacity="0.08"
            />
          </g>

          {/* Pocket Pentagon Piece */}
          <g
            transform="translate(232 168) rotate(12) scale(0.72)"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path
              d="M0,0 H116 V92 L58,136 L0,92 Z"
              stroke="var(--chalk)"
              strokeWidth="1.8"
              strokeOpacity="0.085"
            />
            <path
              d="M10,10 H106 V86 L58,123 L10,86 Z"
              stroke="var(--chalk)"
              strokeWidth="1.5"
              strokeDasharray="6 6"
              strokeOpacity="0.075"
            />
          </g>

          {/* Second Smaller French Curve (Inverted Counterbalance) */}
          <g
            transform="translate(432 320) rotate(156) scale(0.27)"
            fill="none"
            stroke="var(--chalk)"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path
              d="M14,122 C40,122 70,52 150,40 C240,26 300,96 392,56 C430,40 470,34 506,30 C470,120 380,196 250,196 C150,196 60,190 28,168 C14,158 8,140 14,122Z"
              strokeWidth="4.6"
              strokeOpacity="0.085"
            />
            <ellipse cx="170" cy="128" rx="34" ry="15" transform="rotate(-14 170 128)" strokeWidth="4" strokeOpacity="0.08" />
            <ellipse cx="300" cy="128" rx="26" ry="11" transform="rotate(-6 300 128)" strokeWidth="4" strokeOpacity="0.08" />
            <circle cx="402" cy="112" r="9" strokeWidth="4" strokeOpacity="0.08" />
          </g>

          {/* Measuring Tape Segment with Graduated Ticks */}
          <g
            transform="translate(178 358) rotate(-18)"
            fill="none"
            stroke="var(--chalk)"
            strokeWidth="1.25"
            strokeOpacity="0.085"
          >
            <rect x="0" y="0" width="128" height="22" />
            <path d="M12,0V11 M22,0V6 M32,0V9 M42,0V6 M52,0V12 M62,0V6 M72,0V9 M82,0V6 M92,0V11 M102,0V6 M112,0V9" />
          </g>

          {/* Needle & Trailing Curved Thread */}
          <g
            transform="translate(36 370) rotate(-10)"
            fill="none"
            strokeLinecap="round"
          >
            <path d="M52,6 L14,42" stroke="var(--chalk)" strokeWidth="1.6" strokeOpacity="0.095" />
            <ellipse cx="47" cy="11" rx="2.4" ry="5.5" transform="rotate(42 47 11)" stroke="var(--chalk)" strokeWidth="1.3" strokeOpacity="0.095" />
            <path
              d="M48,10 C82,2 86,44 122,34"
              stroke="var(--thread)"
              strokeWidth="1.4"
              strokeDasharray="6 5"
              strokeOpacity="0.17"
            />
          </g>

          {/* Scattered Subtle Basting Cross-Stitches */}
          <path
            d="M168,140l7,7 M175,140l-7,7 M352,216l7,7 M359,216l-7,7 M138,312l7,7 M145,312l-7,7 M402,414l7,7 M409,414l-7,7 M174,234l8,8 M182,234l-8,8 M318,128l8,8 M326,128l-8,8 M274,412l8,8 M282,412l-8,8 M30,148l7,7 M37,148l-7,7"
            stroke="var(--chalk)"
            strokeWidth="1.3"
            strokeOpacity="0.08"
          />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#tailoredAtelierTile)" />
    </svg>

    {/* Layer 2: Long Sweeping French-Curve Crossing Lines (ds.py sweep geometry) */}
    <svg
      viewBox="0 0 1440 860"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid slice"
      style={{ position: 'absolute', inset: 0, display: 'block' }}
    >
      {/* Primary Armhole Sweep (Bottom-Left to Upper-Right) */}
      <path
        d="M-40,790 C380,820 640,95 1480,118"
        fill="none"
        stroke="var(--thread)"
        strokeWidth="2.1"
        strokeLinecap="round"
        opacity="0.22"
      />
      <path
        d="M-40,808 C380,838 640,113 1480,136"
        fill="none"
        stroke="var(--chalk)"
        strokeWidth="1.3"
        strokeLinecap="round"
        opacity="0.10"
      />
      <path
        d="M-40,826 C380,856 640,131 1480,154"
        fill="none"
        stroke="var(--chalk)"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeDasharray="10 9"
        opacity="0.11"
      />

      {/* Secondary Counter-Crossing Sweep (Upper-Left to Lower-Right) */}
      <path
        d="M-40,155 C420,175 760,720 1480,680"
        fill="none"
        stroke="var(--kraft)"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeDasharray="9 8"
        opacity="0.15"
      />
      <path
        d="M-40,169 C420,189 760,734 1480,694"
        fill="none"
        stroke="var(--chalk)"
        strokeWidth="1"
        strokeLinecap="round"
        opacity="0.075"
      />
    </svg>
  </div>
);
