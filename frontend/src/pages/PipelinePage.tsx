import React, { useState, useMemo, useEffect } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { ResizableSplitPane } from '../components/common/ResizableSplitPane';
import { AtelierFrenchCurveBackdrop, FitDial } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';
import { extractEmail, type JobItem } from '../services/jobsApi';
import { cleanCompanyName, cleanTargetJobTitle } from '../services/cvFitApi';
import { hasDirectRecruiterEmail, type PipelineStatus } from '../services/pipelineStorage';

const STAGE_META: {
  id: PipelineStatus;
  label: string;
}[] = [
  { id: 'saved', label: 'Saved' },
  { id: 'in_process', label: 'Ready to Send' },
  { id: 'applied', label: 'Applied' },
  { id: 'interview', label: 'Interview' },
];

export const PipelinePage: React.FC = () => {
  const {
    pipelineItems,
    tailoredDocs,
    coverLetters,
    addToPipeline,
    updatePipelineStage,
    updatePipelineEmail,
    removeFromPipeline,
    openJobInStudio,
    openDocInStudio,
    openJobInCoverLetters,
    navigateTo,
  } = useWorkspace();

  const [viewMode, setViewMode] = useState<'split' | 'board' | 'table'>('split');
  const [showArchived, setShowArchived] = useState(false);
  const [selectedId, setSelectedId] = useState<string>(pipelineItems[0]?.id || '');
  const [pasteOpen, setPasteOpen] = useState(false);
  const [pasteText, setPasteText] = useState('');
  const [emailDrafts, setEmailDrafts] = useState<Record<string, string>>({});

  const visibleItems = useMemo(() => {
    const filtered = pipelineItems.filter((p) => (showArchived ? true : p.status !== 'archived'));
    const priority: Record<PipelineStatus, number> = {
      applied: 1,
      in_process: 2,
      interview: 3,
      saved: 4,
      archived: 5,
    };
    return [...filtered].sort((a, b) => priority[a.status] - priority[b.status]);
  }, [pipelineItems, showArchived]);

  const activeItem = visibleItems.find((p) => p.id === selectedId) || visibleItems[0] || null;
  const editingEmail = activeItem ? (emailDrafts[activeItem.id] ?? activeItem.recruiter_email ?? '') : '';

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target && (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || target.isContentEditable)) return;
      if (visibleItems.length === 0) return;

      const idx = visibleItems.findIndex((i) => i.id === activeItem?.id);
      if (e.key.toLowerCase() === 'j') {
        const next = visibleItems[Math.min(visibleItems.length - 1, Math.max(0, idx + 1))];
        if (next) setSelectedId(next.id);
      } else if (e.key.toLowerCase() === 'k') {
        const prev = visibleItems[Math.max(0, idx - 1)];
        if (prev) setSelectedId(prev.id);
      } else if (e.key.toLowerCase() === 'd' && activeItem) {
        openJobInCoverLetters(activeItem.job, {
          mode: activeItem.status === 'applied' ? 'followup' : 'pitch',
        });
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [visibleItems, activeItem, openJobInCoverLetters]);

  const handleTrackOpportunity = () => {
    if (!pasteText.trim()) return;
    const email = extractEmail(pasteText);
    const urlMatch = pasteText.match(/https?:\/\/\S+/i);
    const lines = pasteText.split('\n').map((l) => l.trim()).filter(Boolean);
    const titleGuess = lines[0]?.slice(0, 68) || 'Target Opportunity';

    const syntheticJob: JobItem = {
      id: Date.now(),
      source_id: `manual_${Date.now()}`,
      title: titleGuess,
      company_name: email ? email.split('@')[1]?.split('.')[0] || 'Direct Team' : 'External Portal',
      location: 'Cairo / GCC Hybrid',
      url: urlMatch ? urlMatch[0] : '',
      raw_description: pasteText.trim(),
      fit_score: 86,
      is_high_match: true,
      source_type: email ? 'recruiter_post' : 'manual',
      parsed_skills: ['Python', 'FastAPI', 'SQL', 'PyTorch', 'Docker'].filter((s) =>
        pasteText.toLowerCase().includes(s.toLowerCase())
      ),
      responsibilities: lines.slice(1, 4),
      location_type: 'Hybrid',
      created_at: new Date().toISOString(),
      recruiter_email: email || undefined,
    };

    const created = addToPipeline(syntheticJob, 'saved', email);
    setPasteText('');
    setPasteOpen(false);
    if (created) setSelectedId(created.id);
  };

  const overdueCount = visibleItems.filter((i) => i.status === 'applied').length;
  const segIdx = viewMode === 'split' ? 0 : viewMode === 'board' ? 1 : 2;

  const activeCvDoc = activeItem
    ? tailoredDocs.find(
        (d) => d.doc_id === activeItem.tailored_cv_doc_id || d.job_id === activeItem.job.id
      ) || null
    : null;
  const activeLetterDoc = activeItem
    ? activeItem.cover_letter || coverLetters.find((c) => c.job_id === activeItem.job.id) || null
    : null;
  const activeIsDirect = activeItem ? hasDirectRecruiterEmail(activeItem.job) || Boolean(activeItem.recruiter_email) : false;

  return (
    <div className="t-studio-shell t-cv-studio-v2">
      {/* SOLID PATTERN-FREE PIPELINE COMMAND BAR */}
      <header className="t-studio-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
          <h1 style={{ fontSize: 19, margin: 0, color: 'var(--paper)' }}>Application Pipeline</h1>
          {overdueCount > 0 && (
            <span className="t-dash-kpi-pill" style={{ cursor: 'default' }}>
              <span className="t-signal-down" aria-hidden="true" />
              <span className="t-mono" style={{ fontWeight: 600 }}>{overdueCount}</span>
              <span>Follow-up due</span>
            </span>
          )}
          <span className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)' }}>
            {visibleItems.length} tracked
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="t-atelier-seg" role="tablist" aria-label="Pipeline view mode">
            <span
              aria-hidden="true"
              className="t-atelier-seg-thumb"
              style={{ transform: `translateX(${segIdx * 100}%)` }}
            />
            {[
              { id: 'split' as const, label: 'Split' },
              { id: 'board' as const, label: 'Board' },
              { id: 'table' as const, label: 'Table' },
            ].map((m) => (
              <button
                key={m.id}
                type="button"
                role="tab"
                aria-selected={viewMode === m.id}
                className={`t-atelier-seg-btn ${viewMode === m.id ? 't-atelier-seg-btn--active' : ''}`}
                onClick={() => setViewMode(m.id)}
              >
                {m.label}
              </button>
            ))}
          </div>

          <button
            type="button"
            className="t-atelier-topbar-ghost"
            style={showArchived ? { background: 'var(--ink-elevated)', opacity: 1 } : undefined}
            onClick={() => setShowArchived((v) => !v)}
          >
            <span>Archived</span>
          </button>

          <button
            type="button"
            className="t-atelier-export-btn"
            onClick={() => setPasteOpen((v) => !v)}
          >
            <TailoredIcon name="plus" size={13} color="var(--ink)" />
            <span>Track Opportunity</span>
          </button>
        </div>
      </header>

      {/* Inline Opportunity Capture Bar (Supports BOTH Direct Email & External Portal links) */}
      {pasteOpen && (
        <div
          style={{
            background: 'var(--ink-elevated)',
            padding: '12px 20px',
            borderBottom: '1px solid rgba(229, 224, 218, 0.08)',
            position: 'relative',
            zIndex: 35,
          }}
        >
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', maxWidth: 1120 }}>
            <input
              id="pipeline-track-input"
              name="pipelineOpportunity"
              className="t-atelier-inline-input"
              placeholder="Paste recruiter email post, portal job link, or role summary..."
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && pasteText.trim()) handleTrackOpportunity();
              }}
            />
            <button
              type="button"
              className="t-atelier-btn-primary"
              disabled={!pasteText.trim()}
              onClick={handleTrackOpportunity}
            >
              Add to Pipeline
            </button>
            <button
              type="button"
              className="t-atelier-topbar-ghost"
              onClick={() => setPasteOpen(false)}
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* DARK ATELIER STAGE WITH FRENCH-CURVE BACKDROP */}
      <div className="t-atelier-split-stage">
        <AtelierFrenchCurveBackdrop />

        {/* VIEW 1: FOCUS SPLIT */}
        {viewMode === 'split' && (
          visibleItems.length === 0 ? (
            <div className="t-atelier-split-panel" style={{ width: '100%', alignItems: 'center', justifyContent: 'center', padding: 48 }}>
              <h2 style={{ fontSize: 22, marginBottom: 8 }}>Pipeline CRM is empty</h2>
              <p style={{ fontSize: 13.5, color: 'var(--n500)', marginBottom: 18 }}>
                Track any direct recruiter thread or external portal application in one quiet queue.
              </p>
              <button type="button" className="t-atelier-btn-primary" onClick={() => setPasteOpen(true)}>
                + Track First Opportunity
              </button>
            </div>
          ) : (
            <ResizableSplitPane
              storageKey="pipeline_focus_split_v3"
              defaultLeftPct={35}
              minLeftPx={340}
              minRightPx={460}
              left={
                <div className="t-atelier-split-panel">
                  <div style={{ flex: 1, overflowY: 'auto', padding: '14px 14px 10px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {visibleItems.map((item) => {
                      const stage = STAGE_META.find((s) => s.id === item.status);
                      const active = activeItem?.id === item.id;
                      const score = Math.round(item.job.fit_score);
                      const isDirect = hasDirectRecruiterEmail(item.job) || Boolean(item.recruiter_email);
                      return (
                        <div
                          key={item.id}
                          className={`t-dash-match-row ${active ? 't-dash-match-row--active' : ''}`}
                          onClick={() => setSelectedId(item.id)}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0, flex: 1 }}>
                            <span
                              className={`t-dash-fit-badge ${
                                score >= 75
                                  ? 't-dash-fit-badge--strong'
                                  : score >= 50
                                    ? 't-dash-fit-badge--mid'
                                    : 't-dash-fit-badge--low'
                              }`}
                            >
                              {score >= 75 ? (
                                <span className="t-signal-up" aria-hidden="true" />
                              ) : score < 50 ? (
                                <span className="t-signal-down" aria-hidden="true" />
                              ) : (
                                <span className="t-atelier-fit-dot" style={{ background: 'var(--amber)' }} />
                              )}
                              <span>{score}%</span>
                            </span>

                            <div style={{ minWidth: 0 }}>
                              <div
                                style={{
                                  fontWeight: 600,
                                  fontSize: 14,
                                  color: 'var(--ink)',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                }}
                              >
                                {cleanTargetJobTitle(item.job.title)}
                              </div>
                              <div style={{ fontSize: 12, color: 'var(--n500)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {cleanCompanyName(item.job.company_name)} · {isDirect ? item.recruiter_email || 'Direct Email' : 'External Portal'}
                              </div>
                            </div>
                          </div>

                          <span
                            className={`t-dash-tag ${
                              item.status === 'applied'
                                ? 't-dash-tag--amber'
                                : item.status === 'in_process'
                                  ? 't-dash-tag--mist'
                                  : item.status === 'interview'
                                    ? 't-dash-tag--green'
                                    : 't-dash-tag--paper'
                            }`}
                          >
                            {item.status === 'applied' && <span className="t-signal-down" aria-hidden="true" />}
                            <span>{stage?.label || item.status}</span>
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Clean Stage Count Strip */}
                  <div
                    style={{
                      padding: '12px 16px',
                      borderTop: '1px solid rgba(26, 20, 18, 0.08)',
                      display: 'grid',
                      gridTemplateColumns: 'repeat(4, 1fr)',
                      gap: 6,
                    }}
                  >
                    {STAGE_META.map((st) => {
                      const count = visibleItems.filter((x) => x.status === st.id).length;
                      return (
                        <div
                          key={st.id}
                          style={{
                            background: 'white',
                            borderRadius: '4px 10px 4px 4px',
                            padding: '6px 8px',
                            textAlign: 'center',
                          }}
                        >
                          <div style={{ fontSize: 10.5, color: 'var(--n500)', fontWeight: 500 }}>{st.label}</div>
                          <div className="t-mono" style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)', marginTop: 1 }}>
                            {count}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              }
              right={
                <div className="t-atelier-split-panel" style={{ overflowY: 'auto', padding: '24px 28px 30px' }}>
                  {activeItem ? (
                    <>
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'flex-start',
                          gap: 16,
                          paddingBottom: 16,
                          borderBottom: '1px solid rgba(26, 20, 18, 0.08)',
                        }}
                      >
                        <div style={{ minWidth: 0 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                            {activeIsDirect ? (
                              <span className="t-dash-tag t-dash-tag--green">
                                <span className="t-signal-up" aria-hidden="true" />
                                <span>Direct Email Thread</span>
                              </span>
                            ) : (
                              <span className="t-dash-tag t-dash-tag--mist">External Portal Application</span>
                            )}
                            {activeItem.status === 'applied' && (
                              <span className="t-dash-tag t-dash-tag--amber">
                                <span className="t-signal-down" aria-hidden="true" />
                                <span>7-Day Follow-up Ready</span>
                              </span>
                            )}
                          </div>
                          <h2 style={{ fontSize: 25, margin: 0 }}>{cleanTargetJobTitle(activeItem.job.title)}</h2>
                          <div style={{ fontSize: 13.5, color: 'var(--n500)', marginTop: 4 }}>
                            {cleanCompanyName(activeItem.job.company_name)} · {activeItem.job.location}
                          </div>
                        </div>
                        <FitDial score={activeItem.job.fit_score} size={76} />
                      </div>

                      {/* Stage Pills + Channel Email Editor */}
                      <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div>
                          <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--n500)', marginBottom: 6 }}>
                            Pipeline Stage
                          </div>
                          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            {[...STAGE_META, { id: 'archived' as const, label: 'Archived' }].map((st) => (
                              <button
                                key={st.id}
                                type="button"
                                className={`t-atelier-stage-pill ${
                                  activeItem.status === st.id ? 't-atelier-stage-pill--active' : ''
                                }`}
                                onClick={() => updatePipelineStage(activeItem.id, st.id)}
                              >
                                {st.label}
                              </button>
                            ))}
                          </div>
                        </div>

                        {activeIsDirect && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <label
                              htmlFor="pipe-recruiter-email"
                              style={{ fontSize: 12, fontWeight: 600, color: 'var(--n500)', width: 110, flexShrink: 0 }}
                            >
                              Recruiter Email
                            </label>
                            <input
                              id="pipe-recruiter-email"
                              className="t-atelier-inline-input"
                              style={{ background: 'white' }}
                              value={editingEmail}
                              onChange={(e) =>
                                setEmailDrafts((prev) => ({ ...prev, [activeItem.id]: e.target.value }))
                              }
                            />
                            <button
                              type="button"
                              className="t-atelier-btn-tonal"
                              onClick={() => {
                                updatePipelineEmail(activeItem.id, editingEmail);
                              }}
                            >
                              Save
                            </button>
                          </div>
                        )}
                      </div>

                      {/* Connected Application Package Card (CV + Cover Letter + Outreach) */}
                      <div className="t-dash-subcard" style={{ marginTop: 16 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--n500)' }}>
                            Connected Application Package
                          </span>
                          <button
                            type="button"
                            className="t-atelier-btn-ghost"
                            style={{ padding: '2px 8px', fontSize: 12 }}
                            onClick={() => navigateTo(`/pipeline/${activeItem.id}`)}
                          >
                            Full Dossier →
                          </button>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
                          <div style={{ background: 'var(--paper)', borderRadius: '4px 12px 4px 4px', padding: '10px 12px' }}>
                            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--n500)' }}>Paired CV</div>
                            <div style={{ fontWeight: 600, fontSize: 13, marginTop: 2 }}>
                              {activeCvDoc ? 'Tailored CV Ready' : 'Master Baseline CV'}
                            </div>
                            <button
                              type="button"
                              className="t-atelier-btn-ghost"
                              style={{ padding: '4px 0 0', fontSize: 12, color: 'var(--dye)', fontWeight: 600 }}
                              onClick={() =>
                                activeCvDoc
                                  ? openDocInStudio(activeCvDoc.doc_id)
                                  : openJobInStudio(activeItem.job, { skipCreditCheck: true })
                              }
                            >
                              Open in CV Studio →
                            </button>
                          </div>

                          <div style={{ background: 'var(--paper)', borderRadius: '4px 12px 4px 4px', padding: '10px 12px' }}>
                            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--n500)' }}>Outreach Pitch</div>
                            <div style={{ fontWeight: 600, fontSize: 13, marginTop: 2 }}>
                              {activeLetterDoc ? 'Saved Letter Attached' : 'Ready to compose'}
                            </div>
                            <button
                              type="button"
                              className="t-atelier-btn-ghost"
                              style={{ padding: '4px 0 0', fontSize: 12, color: 'var(--dye)', fontWeight: 600 }}
                              onClick={() =>
                                openJobInCoverLetters(activeItem.job, {
                                  mode: activeItem.status === 'applied' ? 'followup' : 'pitch',
                                })
                              }
                            >
                              {activeItem.status === 'applied' ? 'Draft Follow-Up →' : 'Compose Outreach →'}
                            </button>
                          </div>
                        </div>

                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                          {activeIsDirect ? (
                            <>
                              <button
                                type="button"
                                className="t-atelier-btn-primary"
                                onClick={() =>
                                  openJobInCoverLetters(activeItem.job, {
                                    mode: activeItem.status === 'applied' ? 'followup' : 'pitch',
                                  })
                                }
                              >
                                <TailoredIcon name="send" size={13} color="var(--ink)" />
                                <span>
                                  {activeItem.status === 'applied' ? 'Draft Follow-Up in Cover Letters' : 'Compose & Send'}
                                </span>
                              </button>
                            </>
                          ) : (
                            <>
                              {activeItem.job.url && (
                                <button
                                  type="button"
                                  className="t-atelier-btn-primary"
                                  onClick={() => window.open(activeItem.job.url, '_blank')}
                                >
                                  <TailoredIcon name="external" size={13} color="var(--ink)" />
                                  <span>Open External Listing</span>
                                </button>
                              )}
                              <button
                                type="button"
                                className="t-atelier-btn-tonal"
                                onClick={() => openJobInCoverLetters(activeItem.job, { mode: 'letter' })}
                              >
                                Prepare Portal Letter
                              </button>
                              {activeItem.status !== 'applied' && (
                                <button
                                  type="button"
                                  className="t-atelier-btn-tonal"
                                  onClick={() => updatePipelineStage(activeItem.id, 'applied')}
                                >
                                  Mark Applied
                                </button>
                              )}
                            </>
                          )}
                        </div>
                      </div>

                      {/* Captured Role Summary */}
                      <div style={{ marginTop: 16 }}>
                        <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--n500)', marginBottom: 6 }}>
                          Role Context
                        </div>
                        <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.58, color: 'var(--n700)' }}>
                          {activeItem.job.raw_description}
                        </p>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 18 }}>
                        <span className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                          Shortcuts: J/K step · D cover letter
                        </span>
                        <button
                          type="button"
                          className="t-atelier-btn-ghost"
                          onClick={() => removeFromPipeline(activeItem.id)}
                        >
                          Remove from Pipeline
                        </button>
                      </div>
                    </>
                  ) : null}
                </div>
              }
            />
          )
        )}

        {/* VIEW 2: ATELIER BOARD VIEW */}
        {viewMode === 'board' && (
          <div
            style={{
              position: 'relative',
              zIndex: 1,
              flex: 1,
              width: '100%',
              overflowX: 'auto',
              display: 'grid',
              gridTemplateColumns: 'repeat(4, minmax(240px, 1fr))',
              gap: 14,
              alignItems: 'stretch',
            }}
          >
            {STAGE_META.map((stage) => {
              const colItems = visibleItems.filter((p) => p.status === stage.id);
              const nextStageIdx = Math.min(STAGE_META.length - 1, STAGE_META.findIndex((s) => s.id === stage.id) + 1);
              const nextStage = STAGE_META[nextStageIdx];
              return (
                <div key={stage.id} className="t-atelier-split-panel" style={{ padding: 14 }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      paddingBottom: 10,
                      marginBottom: 10,
                      borderBottom: '1px solid rgba(26, 20, 18, 0.08)',
                    }}
                  >
                    <span style={{ fontFamily: 'var(--font-voice)', fontSize: 17, fontWeight: 540 }}>
                      {stage.label}
                    </span>
                    <span className="t-mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--n500)' }}>
                      {colItems.length}
                    </span>
                  </div>

                  <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {colItems.length === 0 ? (
                      <div style={{ padding: '24px 12px', textAlign: 'center', fontSize: 12.5, color: 'var(--n500)' }}>
                        No roles in {stage.label}
                      </div>
                    ) : (
                      colItems.map((item) => {
                        const score = Math.round(item.job.fit_score);
                        const isDirect = hasDirectRecruiterEmail(item.job) || Boolean(item.recruiter_email);
                        return (
                          <div key={item.id} className="t-dash-subcard">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                              <span className={`t-dash-tag ${isDirect ? 't-dash-tag--green' : 't-dash-tag--mist'}`}>
                                {isDirect ? 'Direct Email' : 'Portal'}
                              </span>
                              <span className="t-mono" style={{ fontSize: 11.5, fontWeight: 600, color: score >= 75 ? 'var(--green)' : 'var(--ink)' }}>
                                {score}%
                              </span>
                            </div>
                            <div style={{ fontWeight: 600, fontSize: 14 }}>{cleanTargetJobTitle(item.job.title)}</div>
                            <div style={{ fontSize: 12, color: 'var(--n500)', marginTop: 2 }}>
                              {cleanCompanyName(item.job.company_name)}
                            </div>
                            <div style={{ display: 'flex', gap: 6, marginTop: 10, flexWrap: 'wrap' }}>
                              <button
                                type="button"
                                className="t-atelier-btn-tonal"
                                style={{ padding: '5px 10px', fontSize: 12 }}
                                onClick={() => navigateTo(`/pipeline/${item.id}`)}
                              >
                                Dossier
                              </button>
                              {nextStage.id !== stage.id && (
                                <button
                                  type="button"
                                  className="t-atelier-btn-primary"
                                  style={{ padding: '5px 10px', fontSize: 12 }}
                                  onClick={() => updatePipelineStage(item.id, nextStage.id)}
                                >
                                  Move → {nextStage.label}
                                </button>
                              )}
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* VIEW 3: CLEAN TABLE VIEW (ZERO OS SELECTS) */}
        {viewMode === 'table' && (
          <div className="t-atelier-split-panel" style={{ width: '100%', padding: 20, overflowY: 'auto' }}>
            <table className="t-table">
              <thead>
                <tr>
                  <th>Role &amp; Company</th>
                  <th>Channel / Contact</th>
                  <th>Fit</th>
                  <th>Stage</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {visibleItems.map((item) => {
                  const score = Math.round(item.job.fit_score);
                  const isDirect = hasDirectRecruiterEmail(item.job) || Boolean(item.recruiter_email);
                  return (
                    <tr key={item.id}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{cleanTargetJobTitle(item.job.title)}</div>
                        <div style={{ fontSize: 12, color: 'var(--n500)' }}>
                          {cleanCompanyName(item.job.company_name)}
                        </div>
                      </td>
                      <td>
                        <span className={`t-dash-tag ${isDirect ? 't-dash-tag--green' : 't-dash-tag--mist'}`}>
                          {isDirect ? item.recruiter_email || 'Direct Email' : 'External Portal'}
                        </span>
                      </td>
                      <td>
                        <span className="t-mono" style={{ fontWeight: 600, color: score >= 75 ? 'var(--green)' : 'var(--ink)' }}>
                          {score}%
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                          {STAGE_META.map((st) => (
                            <button
                              key={st.id}
                              type="button"
                              className={`t-atelier-stage-pill ${item.status === st.id ? 't-atelier-stage-pill--active' : ''}`}
                              style={{ padding: '3px 8px', fontSize: 11.5 }}
                              onClick={() => updatePipelineStage(item.id, st.id)}
                            >
                              {st.label}
                            </button>
                          ))}
                        </div>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: 6 }}>
                          <button
                            type="button"
                            className="t-atelier-btn-primary"
                            style={{ padding: '5px 10px', fontSize: 12 }}
                            onClick={() => openJobInCoverLetters(item.job, { mode: item.status === 'applied' ? 'followup' : 'pitch' })}
                          >
                            {item.status === 'applied' ? 'Follow-Up' : 'Outreach'}
                          </button>
                          <button
                            type="button"
                            className="t-atelier-btn-tonal"
                            style={{ padding: '5px 10px', fontSize: 12 }}
                            onClick={() => navigateTo(`/pipeline/${item.id}`)}
                          >
                            Dossier
                          </button>
                          <button
                            type="button"
                            className="t-atelier-btn-ghost"
                            style={{ padding: '5px 8px', fontSize: 12 }}
                            onClick={() => removeFromPipeline(item.id)}
                          >
                            Remove
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
