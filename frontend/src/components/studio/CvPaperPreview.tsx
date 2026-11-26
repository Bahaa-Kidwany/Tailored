import React from 'react';
import type { ParsedLatexCv } from '../../utils/latexLiveSync';

export interface CvPaperPreviewProps {
  data: ParsedLatexCv;
  compact?: boolean;
}

/**
 * Formatted read-only ATS 1-page CV sheet preview shared across preview drawers.
 */
export const CvPaperPreview: React.FC<CvPaperPreviewProps> = ({ data, compact = false }) => {
  return (
    <div
      className="t-cv-preview-frame"
      style={{
        padding: compact ? '20px 24px' : '26px 32px',
      }}
    >
      {/* ATS Contact Header */}
      <div
        style={{
          textAlign: 'center',
          borderBottom: '1.5px solid var(--ink)',
          paddingBottom: 9,
          marginBottom: 11,
        }}
      >
        <div
          style={{
            fontFamily: 'var(--font-voice)',
            fontSize: compact ? 20 : 23,
            fontWeight: 600,
            letterSpacing: '-0.02em',
            lineHeight: 1.15,
            color: 'var(--ink)',
          }}
        >
          {data.fullName}
        </div>
        <div className="t-mono" style={{ fontSize: 10.2, color: 'var(--n700)', marginTop: 3 }}>
          {data.headlineLine}
        </div>
        <div className="t-mono" style={{ fontSize: 10, color: 'var(--n500)', marginTop: 2 }}>
          {data.contactLine}
        </div>
      </div>

      {/* Professional Summary */}
      <div style={{ marginBottom: 11 }}>
        <div
          className="t-mono"
          style={{
            fontSize: 9.8,
            fontWeight: 700,
            letterSpacing: '0.12em',
            borderBottom: '1px solid var(--n300)',
            paddingBottom: 2,
            marginBottom: 5,
            color: 'var(--ink)',
          }}
        >
          PROFESSIONAL SUMMARY
        </div>
        <p style={{ margin: 0, fontSize: 12.6, lineHeight: 1.48, color: 'var(--ink)' }}>
          {data.summary}
        </p>
      </div>

      {/* Technical Competencies */}
      {data.skillRows.length > 0 && (
        <div style={{ marginBottom: 11 }}>
          <div
            className="t-mono"
            style={{
              fontSize: 9.8,
              fontWeight: 700,
              letterSpacing: '0.12em',
              borderBottom: '1px solid var(--n300)',
              paddingBottom: 2,
              marginBottom: 5,
              color: 'var(--ink)',
            }}
          >
            CORE TECHNICAL COMPETENCIES
          </div>
          <div style={{ fontSize: 12, lineHeight: 1.46, color: 'var(--n700)', display: 'flex', flexDirection: 'column', gap: 2 }}>
            {data.skillRows.map((row, idx) => (
              <div key={idx}>
                <strong style={{ color: 'var(--ink)' }}>{row.label}:</strong> {row.value}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Work Experience */}
      {data.experiences.length > 0 && (
        <div style={{ marginBottom: 11 }}>
          <div
            className="t-mono"
            style={{
              fontSize: 9.8,
              fontWeight: 700,
              letterSpacing: '0.12em',
              borderBottom: '1px solid var(--n300)',
              paddingBottom: 2,
              marginBottom: 5,
              color: 'var(--ink)',
            }}
          >
            WORK EXPERIENCE
          </div>
          {data.experiences.map((exp, idx) => (
            <div key={idx} style={{ marginBottom: 7 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8, flexWrap: 'wrap', marginBottom: 2 }}>
                <div style={{ fontWeight: 700, fontSize: 12.6, color: 'var(--ink)' }}>
                  {exp.role}
                  {exp.company ? ` — ${exp.company}` : ''}
                </div>
                <div className="t-mono" style={{ fontSize: 10, color: 'var(--n500)' }}>
                  {[exp.dates, exp.location].filter(Boolean).join(' · ')}
                </div>
              </div>
              {exp.bullets.map((b, bi) => (
                <div key={bi} style={{ display: 'flex', gap: 7, fontSize: 12.2, lineHeight: 1.44, padding: '1.5px 0', color: 'var(--ink)' }}>
                  <span style={{ color: 'var(--thread)', fontWeight: 700 }}>•</span>
                  <span>{b}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* Projects & Education / Certifications */}
      {(data.projects.length > 0 || data.education.length > 0) && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {data.projects.length > 0 && (
            <div>
              <div
                className="t-mono"
                style={{
                  fontSize: 9.8,
                  fontWeight: 700,
                  letterSpacing: '0.12em',
                  borderBottom: '1px solid var(--n300)',
                  paddingBottom: 2,
                  marginBottom: 5,
                  color: 'var(--ink)',
                }}
              >
                FEATURED PROJECTS
              </div>
              {data.projects.map((pr, idx) => (
                <div key={idx} style={{ marginBottom: 5 }}>
                  <div style={{ fontWeight: 600, fontSize: 11.8, color: 'var(--ink)' }}>{pr.name}</div>
                  <div style={{ fontSize: 11.3, color: 'var(--n700)', lineHeight: 1.38 }}>{pr.summary}</div>
                </div>
              ))}
            </div>
          )}

          <div>
            <div
              className="t-mono"
              style={{
                fontSize: 9.8,
                fontWeight: 700,
                letterSpacing: '0.12em',
                borderBottom: '1px solid var(--n300)',
                paddingBottom: 2,
                marginBottom: 5,
                color: 'var(--ink)',
              }}
            >
              EDUCATION, CERTS &amp; LANGUAGES
            </div>
            {data.education.map((ed, idx) => (
              <div key={idx} style={{ marginBottom: 4 }}>
                <div style={{ fontWeight: 600, fontSize: 11.8, color: 'var(--ink)' }}>{ed.title}</div>
                <div className="t-mono" style={{ fontSize: 10, color: 'var(--n500)' }}>
                  {ed.subtitle}
                </div>
              </div>
            ))}
            {data.certs.map((c, idx) => (
              <div key={idx} className="t-mono" style={{ fontSize: 10, color: 'var(--n700)', marginTop: 2 }}>
                {c}
              </div>
            ))}
            {data.languages && (
              <div className="t-mono" style={{ fontSize: 10, color: 'var(--n500)', marginTop: 4 }}>
                Languages: {data.languages}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
