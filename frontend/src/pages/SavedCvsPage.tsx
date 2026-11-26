import React, { useState, useEffect } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { ResizableSplitPane } from '../components/common/ResizableSplitPane';
import { EmptyState, FitDial } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';
import { SAMPLE_PROFILE } from '../services/profileApi';
import { CvFitAPI, cleanCompanyName, cleanTargetJobTitle, type CvFitDetail } from '../services/cvFitApi';

export const SavedCvsPage: React.FC = () => {
  const {
    tailoredDocs,
    currentProfile,
    radarJobs,
    pipelineItems,
    openDocInStudio,
    openJobInStudio,
    forkSavedDoc,
    navigateTo,
    pushToast,
  } = useWorkspace();

  const profile = currentProfile?.profile || SAMPLE_PROFILE;
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'draft' | 'dispatched'>('all');
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
  const [selectedDocId, setSelectedDocId] = useState<string>(tailoredDocs[0]?.doc_id || '');
  const [inspectorTab, setInspectorTab] = useState<'paper' | 'diff' | 'tex'>('paper');
  const [detail, setDetail] = useState<CvFitDetail | null>(null);

  const dispatchedJobIds = new Set(
    pipelineItems.filter((p) => p.status === 'applied' || p.status === 'interview').map((p) => p.job.id)
  );

  const getPersonaTitle = (personaId?: string) =>
    profile.career_personas.find((p) => p.persona_id === personaId)?.target_title ||
    profile.career_personas[0]?.target_title ||
    'Primary Persona';

  const getPersonaSummary = (personaId?: string) =>
    profile.career_personas.find((p) => p.persona_id === personaId)?.summary_bio ||
    profile.career_personas[0]?.summary_bio ||
    '';

  const filteredDocs = tailoredDocs.filter((d) => {
    const isSent = d.job_id !== undefined && dispatchedJobIds.has(d.job_id);
    if (statusFilter === 'dispatched' && !isSent) return false;
    if (statusFilter === 'draft' && isSent) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        (d.job_title || '').toLowerCase().includes(q) ||
        (d.company_name || '').toLowerCase().includes(q) ||
        getPersonaTitle(d.persona_id).toLowerCase().includes(q)
      );
    }
    return true;
  });

  const activeSummary = filteredDocs.find((d) => d.doc_id === selectedDocId) || filteredDocs[0] || null;

  useEffect(() => {
    let mounted = true;
    if (!activeSummary) return;
    CvFitAPI.getCvFit(activeSummary.doc_id).then((res) => {
      if (mounted) setDetail(res);
    });
    return () => {
      mounted = false;
    };
  }, [activeSummary]);

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Slim Canonical Base Templates Strip (0 Credits) */}
      <div
        style={{
          background: 'var(--ink)',
          color: 'var(--chalk)',
          padding: '8px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          flexWrap: 'wrap',
          borderBottom: '1px solid var(--n700)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span className="t-mono" style={{ fontSize: 10.5, color: 'var(--kraft)', letterSpacing: '0.1em' }}>
            CANONICAL BASE TEMPLATES (0 CR):
          </span>
          {profile.career_personas.map((p) => (
            <button
              key={p.persona_id}
              type="button"
              className="t-btn t-btn--chalk-outline t-btn--sm"
              style={{ fontSize: 10.5, padding: '4px 10px' }}
              onClick={() => openJobInStudio(radarJobs[0], { skipCreditCheck: true })}
            >
              {p.target_title} · Base .tex
            </button>
          ))}
        </div>
        <button
          type="button"
          className="t-btn t-btn--ghost t-btn--sm"
          style={{ color: 'var(--chalk)' }}
          onClick={() => navigateTo('/profile')}
        >
          Edit Master Truth →
        </button>
      </div>

      {/* Control Header */}
      <div
        style={{
          background: 'var(--paper)',
          borderBottom: '1.5px solid var(--ink)',
          padding: '10px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <input
            className="t-input"
            style={{ width: 250 }}
            placeholder="Search tailored CVs by company or role..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {(['all', 'draft', 'dispatched'] as const).map((st) => (
            <button
              key={st}
              type="button"
              className={`t-chip ${statusFilter === st ? 't-chip--notch' : ''}`}
              style={{
                cursor: 'pointer',
                padding: '6px 12px',
                background: statusFilter === st ? 'var(--ink)' : 'var(--chalk)',
                color: statusFilter === st ? 'var(--chalk)' : 'var(--ink)',
              }}
              onClick={() => setStatusFilter(st)}
            >
              {st === 'all' ? `All (${tailoredDocs.length})` : st === 'draft' ? 'Working Drafts' : 'Dispatched Locks'}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', border: '1.5px solid var(--ink)' }}>
          <button
            type="button"
            onClick={() => setViewMode('table')}
            className="t-mono"
            style={{
              padding: '5px 12px',
              fontSize: 11,
              border: 'none',
              cursor: 'pointer',
              background: viewMode === 'table' ? 'var(--ink)' : 'var(--paper)',
              color: viewMode === 'table' ? 'var(--chalk)' : 'var(--ink)',
            }}
          >
            Table
          </button>
          <button
            type="button"
            onClick={() => setViewMode('grid')}
            className="t-mono"
            style={{
              padding: '5px 12px',
              fontSize: 11,
              border: 'none',
              cursor: 'pointer',
              background: viewMode === 'grid' ? 'var(--ink)' : 'var(--paper)',
              color: viewMode === 'grid' ? 'var(--chalk)' : 'var(--ink)',
            }}
          >
            Grid
          </button>
        </div>
      </div>

      {/* 62% / 38% Split Library */}
      {filteredDocs.length === 0 ? (
        <div style={{ flex: 1, padding: 32 }}>
          <EmptyState
            icon="cv"
            headline="No saved tailored CVs yet"
            subtext="Pick a match from Job Radar to craft your first role-specific 1-page ATS resume."
            ctaLabel="Browse Job Radar"
            onCta={() => navigateTo('/radar')}
          />
        </div>
      ) : (
        <ResizableSplitPane
          storageKey="saved_cvs_split_v2"
          defaultLeftPct={50}
          minLeftPx={420}
          minRightPx={440}
          left={
            <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100%', justifyContent: 'space-between', padding: viewMode === 'grid' ? 20 : 0 }}>
              {viewMode === 'table' ? (
                <table className="t-table">
                  <thead>
                    <tr>
                      <th>Target Role &amp; Company</th>
                      <th>Fit Score</th>
                      <th>Persona</th>
                      <th>Status</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredDocs.map((doc) => {
                      const isSent = doc.job_id !== undefined && dispatchedJobIds.has(doc.job_id);
                      const active = activeSummary?.doc_id === doc.doc_id;
                      const scoreVal = Math.round(doc.fit_score ?? 90);
                      return (
                        <tr
                          key={doc.doc_id}
                          style={{
                            background: active ? 'var(--paper)' : undefined,
                            cursor: 'pointer',
                          }}
                          onClick={() => setSelectedDocId(doc.doc_id)}
                        >
                          <td>
                            <div style={{ fontWeight: 600 }}>{cleanTargetJobTitle(doc.job_title)}</div>
                            <div className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                              {cleanCompanyName(doc.company_name || 'Target Organization')}
                            </div>
                          </td>
                          <td>
                            <span className="t-chip t-chip--strong">{scoreVal}% Tailored</span>
                          </td>
                          <td className="t-mono" style={{ fontSize: 11.5 }}>{getPersonaTitle(doc.persona_id)}</td>
                          <td>
                            {isSent ? (
                              <span className="t-chip t-chip--dye">Dispatched Lock</span>
                            ) : (
                              <span className="t-chip t-chip--mist">Draft</span>
                            )}
                          </td>
                          <td style={{ textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                            <div style={{ display: 'inline-flex', gap: 6 }}>
                              {isSent ? (
                                <button
                                  type="button"
                                  className="t-btn t-btn--outline t-btn--sm"
                                  onClick={() => forkSavedDoc(doc.doc_id)}
                                >
                                  Fork (0 cr)
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  className="t-btn t-btn--ink t-btn--sm"
                                  onClick={() => openDocInStudio(doc.doc_id)}
                                >
                                  Studio
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 14 }}>
                  {filteredDocs.map((doc) => {
                    const isSent = doc.job_id !== undefined && dispatchedJobIds.has(doc.job_id);
                    const active = activeSummary?.doc_id === doc.doc_id;
                    const scoreVal = Math.round(doc.fit_score ?? 90);
                    return (
                      <div
                        key={doc.doc_id}
                        className="t-card"
                        style={{
                          padding: 18,
                          borderColor: active ? 'var(--thread)' : 'var(--n300)',
                          cursor: 'pointer',
                        }}
                        onClick={() => setSelectedDocId(doc.doc_id)}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                          <FitDial score={scoreVal} size={52} />
                          {isSent ? (
                            <span className="t-chip t-chip--dye">Dispatched</span>
                          ) : (
                            <span className="t-chip t-chip--mist">Editable · 0 cr</span>
                          )}
                        </div>
                        <div style={{ fontWeight: 600, fontSize: 15 }}>{cleanTargetJobTitle(doc.job_title)}</div>
                        <div className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)', marginTop: 3 }}>
                          {cleanCompanyName(doc.company_name || 'Target Organization')}
                        </div>
                        <div style={{ display: 'flex', gap: 6, marginTop: 14 }} onClick={(e) => e.stopPropagation()}>
                          <button
                            type="button"
                            className="t-btn t-btn--ink t-btn--sm"
                            onClick={() => (isSent ? forkSavedDoc(doc.doc_id) : openDocInStudio(doc.doc_id))}
                          >
                            {isSent ? 'Fork Copy' : 'Open Studio'}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              <div
                style={{
                  marginTop: 'auto',
                  padding: '14px 18px',
                  borderTop: '1px solid var(--n300)',
                  background: 'var(--paper)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 8,
                }}
              >
                <span className="t-mono" style={{ fontSize: 11, color: 'var(--n700)' }}>
                  All saved drafts re-compile, diff, and download PDF/.tex at 0 credits forever.
                </span>
                <button type="button" className="t-btn t-btn--subtle t-btn--sm" onClick={() => navigateTo('/radar')}>
                  + Tailor New Role
                </button>
              </div>
            </div>
          }
          right={
            activeSummary ? (
              <div style={{ padding: '24px 26px 64px', background: 'var(--paper)', minHeight: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', paddingBottom: 14, borderBottom: '1.5px solid var(--ink)' }}>
                  <div>
                    <span className="t-eyebrow">
                      {activeSummary.job_id !== undefined && dispatchedJobIds.has(activeSummary.job_id)
                        ? 'Immutable Sent Snapshot'
                        : 'Saved Tailored Document · 0 cr'}
                    </span>
                    <h2 style={{ fontSize: 22, marginTop: 4 }}>{cleanTargetJobTitle(activeSummary.job_title)}</h2>
                    <div className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)', marginTop: 2 }}>
                      {cleanCompanyName(activeSummary.company_name || 'Target Organization')} ·{' '}
                      {Math.round(activeSummary.fit_score ?? 90)}% Fit
                    </div>
                  </div>
                  <FitDial score={Math.round(activeSummary.fit_score ?? 90)} size={68} />
                </div>

                {/* Action Strip (Single Line) */}
                <div style={{ display: 'flex', gap: 6, flexWrap: 'nowrap', marginTop: 14, marginBottom: 16 }}>
                  {activeSummary.job_id !== undefined && dispatchedJobIds.has(activeSummary.job_id) ? (
                    <button
                      type="button"
                      className="t-btn t-btn--primary t-btn--sm"
                      onClick={() => forkSavedDoc(activeSummary.doc_id)}
                    >
                      Fork Copy (0 cr)
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="t-btn t-btn--primary t-btn--sm"
                      onClick={() => openDocInStudio(activeSummary.doc_id)}
                    >
                      Open Studio (0 cr)
                    </button>
                  )}
                  <button
                    type="button"
                    className="t-btn t-btn--outline t-btn--sm"
                    onClick={() => {
                      CvFitAPI.downloadArtifact(detail || activeSummary, 'pdf');
                      pushToast('Compiled ATS PDF download started.');
                    }}
                  >
                    <TailoredIcon name="download" size={13} />
                    PDF
                  </button>
                  <button
                    type="button"
                    className="t-btn t-btn--subtle t-btn--sm"
                    onClick={() => {
                      CvFitAPI.downloadArtifact(detail || activeSummary, 'tex');
                      pushToast('Downloaded .tex source.');
                    }}
                  >
                    .tex
                  </button>
                  <button
                    type="button"
                    className="t-btn t-btn--ghost t-btn--sm"
                    onClick={() => navigateTo('/cover-letters')}
                  >
                    Cover Letter →
                  </button>
                </div>

                {/* Inspector Mode Switch */}
                <div style={{ display: 'flex', gap: 6, marginBottom: 14 }}>
                  {[
                    { id: 'paper' as const, label: 'Paper Preview' },
                    { id: 'diff' as const, label: 'Diff vs Base' },
                    { id: 'tex' as const, label: '.tex Source' },
                  ].map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      className="t-chip"
                      style={{
                        cursor: 'pointer',
                        background: inspectorTab === t.id ? 'var(--ink)' : 'var(--chalk)',
                        color: inspectorTab === t.id ? 'var(--chalk)' : 'var(--ink)',
                      }}
                      onClick={() => setInspectorTab(t.id)}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>

                {detail && inspectorTab === 'paper' && (
                  <div style={{ border: '1px solid var(--ink)', background: 'var(--paper)', padding: 18, fontSize: 13 }}>
                    <div style={{ textAlign: 'center', borderBottom: '1px solid var(--ink)', paddingBottom: 10, marginBottom: 12 }}>
                      <div style={{ fontFamily: 'var(--font-voice)', fontSize: 18, fontWeight: 600 }}>
                        {profile.personal_info.full_name}
                      </div>
                      <div className="t-mono" style={{ fontSize: 10.5, color: 'var(--n500)' }}>
                        {profile.personal_info.primary_email} · {getPersonaTitle(activeSummary.persona_id)}
                      </div>
                    </div>
                    <div className="t-label" style={{ marginBottom: 4 }}>Professional Summary</div>
                    <p style={{ lineHeight: 1.5, marginBottom: 12 }}>{getPersonaSummary(activeSummary.persona_id)}</p>
                    <div className="t-label" style={{ marginBottom: 6 }}>Tailored Role Bullet Highlights</div>
                    <ul className="t-bullets">
                      {detail.bullet_diffs.map((b, i) => (
                        <li key={i}>{b.tailored_bullet}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {detail && inspectorTab === 'diff' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {detail.bullet_diffs.map((b, i) => (
                      <div key={i} className="t-card--flat" style={{ padding: 12, background: 'var(--chalk)' }}>
                        <div className="t-mono" style={{ fontSize: 10.5, color: 'var(--n500)', marginBottom: 4 }}>
                          {b.section}
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--alarm)', textDecoration: 'line-through', marginBottom: 4 }}>
                          {b.original_bullet}
                        </div>
                        <div style={{ fontSize: 13, color: 'var(--green)', fontWeight: 500 }}>
                          {b.tailored_bullet}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {detail && inspectorTab === 'tex' && (
                  <pre
                    className="t-mono"
                    style={{
                      background: 'var(--ink)',
                      color: 'var(--chalk)',
                      padding: 14,
                      fontSize: 11.5,
                      overflowX: 'auto',
                      whiteSpace: 'pre-wrap',
                      margin: 0,
                    }}
                  >
                    {detail.tailored_latex_content || detail.base_latex_content || ''}
                  </pre>
                )}
              </div>
            ) : null
          }
        />
      )}
    </div>
  );
};
