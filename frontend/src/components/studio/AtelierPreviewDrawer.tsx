import React from 'react';
import { TailoredIcon } from '../../brand/TailoredIcons';
import type { ParsedLatexCv } from '../../utils/latexLiveSync';
import { CvPaperPreview } from './CvPaperPreview';

export interface AtelierPreviewData {
  kind: 'cv' | 'letter' | 'job';
  id: string;
  title: string;
  subtitle: string;
  fitScore?: number;
  summary?: string;
  bullets?: string[];
  subjectLine?: string;
  bodyText?: string;
  matchedSkills?: string[];
  missingSkills?: string[];
  cvDocument?: ParsedLatexCv;
  loading?: boolean;
  primaryActionLabel?: string;
  onPrimaryAction?: () => void;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
}

export interface AtelierPreviewDrawerProps {
  preview: AtelierPreviewData | null;
  onClose: () => void;
}

export const AtelierPreviewDrawer: React.FC<AtelierPreviewDrawerProps> = ({ preview, onClose }) => {
  if (!preview) return null;

  const score = preview.fitScore !== undefined ? Math.round(preview.fitScore) : null;

  return (
    <aside className="t-atelier-preview-drawer" role="dialog" aria-label={`Preview ${preview.title}`}>
      <div className="t-atelier-preview-head">
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span className="t-dash-tag t-dash-tag--mist">
              {preview.kind === 'cv' ? 'Saved CV Preview' : preview.kind === 'letter' ? 'Cover Letter Preview' : 'Role Brief Preview'}
            </span>
            {score !== null && (
              <span
                className={`t-dash-tag ${score >= 75 ? 't-dash-tag--green' : ''}`}
                style={
                  score < 75
                    ? { background: score < 50 ? 'rgba(143, 29, 44, 0.08)' : 'rgba(227, 154, 27, 0.14)', color: score < 50 ? 'var(--alarm)' : 'var(--ink)' }
                    : undefined
                }
              >
                {score >= 75 ? (
                  <span className="t-signal-up" aria-hidden="true" />
                ) : score < 50 ? (
                  <span className="t-signal-down" aria-hidden="true" />
                ) : (
                  <span className="t-atelier-fit-dot" style={{ background: 'var(--amber)' }} />
                )}
                <span className="t-mono">{score}% Fit</span>
              </span>
            )}
          </div>
          <h3 style={{ fontSize: 19, marginTop: 6, marginBottom: 0 }}>{preview.title}</h3>
          <div className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)', marginTop: 2 }}>
            {preview.subtitle}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          {preview.secondaryActionLabel && preview.onSecondaryAction && (
            <button
              type="button"
              className="t-atelier-btn-tonal"
              onClick={preview.onSecondaryAction}
            >
              <span>{preview.secondaryActionLabel}</span>
            </button>
          )}
          {preview.primaryActionLabel && preview.onPrimaryAction && (
            <button
              type="button"
              className="t-atelier-btn-primary"
              onClick={preview.onPrimaryAction}
            >
              <span>{preview.primaryActionLabel}</span>
            </button>
          )}
          <button
            type="button"
            className="t-atelier-icon-btn"
            onClick={onClose}
            aria-label="Close preview"
            title="Close preview (Esc)"
          >
            <TailoredIcon name="close" size={14} />
          </button>
        </div>
      </div>

      <div className="t-atelier-preview-body">
        {preview.matchedSkills && preview.matchedSkills.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
            {preview.matchedSkills.slice(0, 6).map((sk) => (
              <span key={sk} className="t-dash-tag t-dash-tag--green">
                <span className="t-signal-up" aria-hidden="true" />
                <span>{sk}</span>
              </span>
            ))}
            {preview.missingSkills?.slice(0, 3).map((sk) => (
              <span
                key={sk}
                className="t-dash-tag"
                style={{ background: 'rgba(143, 29, 44, 0.08)', color: 'var(--alarm)' }}
              >
                <span className="t-signal-down" aria-hidden="true" />
                <span>{sk}</span>
              </span>
            ))}
          </div>
        )}

        {preview.kind === 'cv' && preview.cvDocument ? (
          <div>
            {preview.loading && (
              <div
                className="t-mono"
                style={{ fontSize: 11, color: 'var(--n500)', marginBottom: 8 }}
              >
                Syncing full tailored bullets &amp; LaTeX sheet...
              </div>
            )}
            <CvPaperPreview data={preview.cvDocument} compact />
          </div>
        ) : (
          <>
            {preview.subjectLine && (
              <div style={{ marginBottom: 14, paddingBottom: 10, borderBottom: '1px solid rgba(26, 20, 18, 0.08)' }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--n500)', marginBottom: 3 }}>Subject</div>
                <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--ink)' }}>{preview.subjectLine}</div>
              </div>
            )}

            {preview.summary && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--n500)', marginBottom: 6 }}>
                  {preview.kind === 'cv' ? 'Professional Summary' : 'Role Summary'}
                </div>
                <p style={{ margin: 0, fontSize: 14, lineHeight: 1.62, color: 'var(--ink)' }}>{preview.summary}</p>
              </div>
            )}

            {preview.bullets && preview.bullets.length > 0 && (
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--n500)', marginBottom: 8 }}>
                  Key Bullet Highlights
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {preview.bullets.map((b, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '10px 12px',
                        borderRadius: '4px 12px 4px 4px',
                        background: 'var(--paper)',
                        fontSize: 13.5,
                        lineHeight: 1.55,
                        color: 'var(--ink)',
                      }}
                    >
                      {b}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {preview.bodyText && (
              <div
                style={{
                  padding: '14px 16px',
                  borderRadius: '4px 14px 4px 4px',
                  background: 'var(--paper)',
                  fontSize: 14,
                  lineHeight: 1.65,
                  color: 'var(--ink)',
                  whiteSpace: 'pre-line',
                }}
              >
                {preview.bodyText}
              </div>
            )}
          </>
        )}
      </div>
    </aside>
  );
};
