import React from 'react';
import { useRevealOnScroll } from './useRevealOnScroll';

export interface FeatureShowcaseSectionProps {
  indexLabel: string;
  title: string;
  subtitle: string;
  routeLabel: string;
  videoSrc: string;
  positives: string[];
  negatives?: string[];
  surface?: 'paper' | 'chalk';
}

export const FeatureShowcaseSection: React.FC<FeatureShowcaseSectionProps> = ({
  indexLabel,
  title,
  subtitle,
  routeLabel,
  videoSrc,
  positives,
  negatives = [],
  surface = 'paper',
}) => {
  const { ref, visible } = useRevealOnScroll<HTMLElement>();

  return (
    <section
      ref={ref}
      style={{
        background: surface === 'paper' ? 'var(--paper)' : 'var(--chalk)',
        padding: '84px 32px',
      }}
    >
      <div style={{ maxWidth: 1080, margin: '0 auto' }}>
        {/* Editorial Header — Scrolls into view cleanly */}
        <div
          className={`t-landing-reveal ${visible ? 'is-visible' : ''}`}
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0, 1.1fr) minmax(0, 0.9fr)',
            gap: 32,
            alignItems: 'end',
            marginBottom: 34,
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <span
                className="t-mono"
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  padding: '3px 9px',
                  borderRadius: 6,
                  background: 'var(--ink)',
                  color: 'var(--chalk)',
                }}
              >
                {indexLabel}
              </span>
              <span className="t-eyebrow-dash">{routeLabel}</span>
            </div>

            <h2
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 40,
                lineHeight: 1.06,
                color: 'var(--ink)',
                margin: 0,
              }}
            >
              {title}
            </h2>
          </div>

          <div>
            <p
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: 16,
                lineHeight: 1.58,
                color: 'var(--n700)',
                margin: '0 0 16px',
              }}
            >
              {subtitle}
            </p>

            {/* Semantic Arrows: Green ▲ for positives, Red ▼ for downsides */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {positives.map((item) => (
                <span key={item} className="t-signal-pill t-signal-pill--pos">
                  <span className="t-signal-up" aria-hidden="true" />
                  {item}
                </span>
              ))}
              {negatives.map((item) => (
                <span key={item} className="t-signal-pill t-signal-pill--neg">
                  <span className="t-signal-down" aria-hidden="true" />
                  {item}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Large-Format Real Product Video Showcase Card */}
        <div className={`t-landing-reveal t-landing-reveal-d1 ${visible ? 'is-visible' : ''}`}>
          <div className="t-showcase-card">
            <div
              style={{
                height: 40,
                padding: '0 18px',
                background: 'var(--ink)',
                color: 'var(--chalk)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span
                style={{
                  fontFamily: 'var(--font-sans)',
                  fontSize: 13,
                  fontWeight: 500,
                  color: 'var(--chalk)',
                  opacity: 0.9,
                }}
              >
                Live workspace walkthrough · {routeLabel}
              </span>
              <span className="t-mono" style={{ fontSize: 11.5, color: 'var(--kraft)' }}>
                1440 × 900
              </span>
            </div>

            <video
              src={videoSrc}
              autoPlay
              loop
              muted
              playsInline
              preload="metadata"
              style={{
                display: 'block',
                width: '100%',
                height: 'auto',
                background: 'var(--ink)',
              }}
            />
          </div>
        </div>
      </div>
    </section>
  );
};
