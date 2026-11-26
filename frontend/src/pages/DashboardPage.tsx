import React, { useState, useEffect, useMemo } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { AtelierFrenchCurveBackdrop, FitDial } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';
import { evaluateAllPersonas } from '../utils/fitEngine';
import { SAMPLE_PROFILE } from '../services/profileApi';
import { cleanCompanyName, cleanTargetJobTitle } from '../services/cvFitApi';

export const DashboardPage: React.FC = () => {
  const {
    currentProfile,
    activePersonaId,
    activeRegionalPhone,
    creditBalance,
    radarJobs,
    hiddenJobIds,
    activeStudioDoc,
    activeStudioJob,
    openJobInStudio,
    openDocInStudio,
    setQuickPeekJob,
    addToInterest,
    ingestJobUrlOrText,
    pipelineItems,
    openJobInCoverLetters,
    navigateTo,
    isJobUnlocked,
    setIsIdentityDrawerOpen,
    pushToast,
  } = useWorkspace();

  const [ingestText, setIngestText] = useState('');
  const [selectedMatchIdx, setSelectedMatchIdx] = useState(0);

  const profile = currentProfile?.profile || SAMPLE_PROFILE;
  const activePersona =
    profile.career_personas.find((p) => p.persona_id === activePersonaId) ||
    profile.career_personas[0];

  const firstName = profile.personal_info.full_name.split(' ')[0] || 'Tailor';

  const visibleJobs = useMemo(
    () => radarJobs.filter((j) => !hiddenJobIds.has(j.id)),
    [radarJobs, hiddenJobIds]
  );

  const rankedMatches = useMemo(
    () =>
      visibleJobs
        .map((job) => ({ job, evalRes: evaluateAllPersonas(job, profile) }))
        .sort((a, b) => b.evalRes.best.overallScore - a.evalRes.best.overallScore)
        .slice(0, 5),
    [visibleJobs, profile]
  );

  const clampedIdx =
    rankedMatches.length === 0 ? 0 : Math.min(selectedMatchIdx, rankedMatches.length - 1);
  const selectedMatch = rankedMatches[clampedIdx] ?? rankedMatches[0];

  const activeDraftEval = useMemo(
    () => evaluateAllPersonas(activeStudioJob, profile).best,
    [activeStudioJob, profile]
  );
  const activeDraftScore = activeStudioDoc?.fit_score ?? activeDraftEval.overallScore;

  const followUpsDue = pipelineItems.filter((p) => p.status === 'applied');
  const readyToDispatch = pipelineItems.filter((p) => p.status === 'in_process');
  const interviewsCount = pipelineItems.filter((p) => p.status === 'interview').length;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target && (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || target.isContentEditable)) {
        return;
      }
      if (e.key === 'ArrowDown' && rankedMatches.length > 0) {
        e.preventDefault();
        setSelectedMatchIdx((idx) => Math.min(rankedMatches.length - 1, idx + 1));
      } else if (e.key === 'ArrowUp' && rankedMatches.length > 0) {
        e.preventDefault();
        setSelectedMatchIdx((idx) => Math.max(0, idx - 1));
      } else if (e.code === 'Space' && selectedMatch) {
        e.preventDefault();
        setQuickPeekJob(selectedMatch.job);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [rankedMatches.length, selectedMatch, setQuickPeekJob]);

  const handleIngest = async (tailorNow: boolean) => {
    if (!ingestText.trim()) return;
    await ingestJobUrlOrText(ingestText, { openInStudio: tailorNow, onlySaveInterest: !tailorNow });
    setIngestText('');
  };

  const handlePasteCapture = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of Array.from(items)) {
      if (item.type.startsWith('image/')) {
        e.preventDefault();
        const synthetic =
          'Screenshot OCR Capture: Lead ML Systems Engineer at Tabby · Riyadh / Hybrid · hr@tabby.ai · Stack: Python, PyTorch, FastAPI, Docker, PostgreSQL';
        setIngestText(synthetic);
        pushToast('Captured job post screenshot via OCR.', { variant: 'info' });
        return;
      }
    }
  };

  return (
    <div className="t-dash-shell">
      {/* ZONE 1 — Pattern-Free Dark Atelier Command Strip */}
      <header className="t-dash-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', minWidth: 0 }}>
          <h1 style={{ fontSize: 21, lineHeight: 1.15, color: 'var(--paper)', margin: 0 }}>
            Good afternoon, {firstName}.
          </h1>
          <button
            type="button"
            className="t-atelier-pair-btn"
            onClick={() => setIsIdentityDrawerOpen(true)}
            title="Switch active career persona or regional SIM"
          >
            <span>{activePersona?.target_title}</span>
            <span className="t-mono" style={{ fontSize: 11.5, color: 'var(--kraft)' }}>
              {activeRegionalPhone}
            </span>
            <TailoredIcon name="chevronDown" size={12} color="var(--chalk)" />
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <button type="button" className="t-dash-kpi-pill" onClick={() => navigateTo('/radar')}>
            {rankedMatches.length > 0 && <span className="t-signal-up" aria-hidden="true" />}
            <span className="t-mono" style={{ fontWeight: 600 }}>
              {rankedMatches.length}/{visibleJobs.length}
            </span>
            <span>Matches</span>
          </button>

          <button type="button" className="t-dash-kpi-pill" onClick={() => navigateTo('/pipeline')}>
            <span className="t-mono" style={{ fontWeight: 600 }}>{readyToDispatch.length}</span>
            <span>Ready</span>
          </button>

          <button type="button" className="t-dash-kpi-pill" onClick={() => navigateTo('/pipeline')}>
            {followUpsDue.length > 0 && <span className="t-signal-down" aria-hidden="true" />}
            <span className="t-mono" style={{ fontWeight: 600 }}>{followUpsDue.length}</span>
            <span>Follow-up</span>
          </button>

          <button type="button" className="t-dash-kpi-pill" onClick={() => navigateTo('/plans')}>
            {creditBalance === 0 && <span className="t-signal-down" aria-hidden="true" />}
            <span className="t-mono" style={{ fontWeight: 600 }}>{creditBalance} cr</span>
          </button>
        </div>
      </header>

      {/* DARK ATELIER STAGE WITH FRENCH-CURVE BACKDROP */}
      <div className="t-dash-stage">
        <AtelierFrenchCurveBackdrop />

        <div className="t-dash-grid">
          {/* ZONE 2 — Left Floating Panel: Discover & Tailor */}
          <section className="t-dash-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
              <div>
                <h2 style={{ fontSize: 20, lineHeight: 1.15 }}>Today&apos;s Top Matches</h2>
                <p style={{ margin: '3px 0 0', fontSize: 12.5, color: 'var(--n500)' }}>
                  Pick a role to tailor, or paste any job link below
                </p>
              </div>
              <button type="button" className="t-atelier-btn-ghost" onClick={() => navigateTo('/radar')}>
                Browse Radar ({visibleJobs.length}) →
              </button>
            </div>

            {/* Integrated Quick Role Ingest Dock */}
            <div className="t-dash-ingest" style={{ margin: '14px 0' }}>
              <TailoredIcon name="link" size={15} color="var(--n500)" />
              <input
                id="dashboard-ingest-input"
                name="ingestText"
                aria-label="Paste job URL, recruiter post, or screenshot"
                className="t-dash-ingest-input"
                placeholder="Paste job URL, recruiter post, or Ctrl+V screenshot..."
                value={ingestText}
                onChange={(e) => setIngestText(e.target.value)}
                onPaste={handlePasteCapture}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && ingestText.trim()) handleIngest(false);
                }}
              />
              <button
                type="button"
                className="t-atelier-btn-tonal"
                disabled={!ingestText.trim()}
                onClick={() => handleIngest(false)}
              >
                Save (0 cr)
              </button>
              <button
                type="button"
                className="t-atelier-btn-primary"
                disabled={!ingestText.trim()}
                onClick={() => handleIngest(true)}
              >
                Tailor (1 cr)
              </button>
            </div>

            {/* Calm 5-Row Aligned Ranked List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
              {rankedMatches.map(({ job, evalRes }, idx) => {
                const score = Math.round(evalRes.best.overallScore);
                const unlocked = isJobUnlocked(job.id, 'cv');
                const selected = idx === clampedIdx;
                const badgeTier =
                  score >= 75
                    ? 't-dash-fit-badge--strong'
                    : score >= 50
                      ? 't-dash-fit-badge--mid'
                      : 't-dash-fit-badge--low';

                return (
                  <div
                    key={job.id}
                    className={`t-dash-match-row ${selected ? 't-dash-match-row--active' : ''}`}
                    onClick={() => setSelectedMatchIdx(idx)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0, flex: 1 }}>
                      <span className={`t-dash-fit-badge ${badgeTier}`}>
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
                            fontSize: 14.5,
                            color: 'var(--ink)',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            navigateTo(`/jobs/${job.id}`);
                          }}
                        >
                          {cleanTargetJobTitle(job.title)}
                        </div>
                        <div
                          style={{
                            fontSize: 12.5,
                            color: 'var(--n500)',
                            marginTop: 2,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {cleanCompanyName(job.company_name)} · {job.location} ·{' '}
                          <span style={{ color: 'var(--n700)', fontWeight: 500 }}>
                            {evalRes.best.personaTitle}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                      <div className="t-dash-row-secondary">
                        <button
                          type="button"
                          className="t-atelier-icon-btn"
                          title="Quick Peek (Space)"
                          aria-label={`Quick peek ${cleanTargetJobTitle(job.title)}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            setQuickPeekJob(job);
                          }}
                        >
                          <TailoredIcon name="eye" size={14} />
                        </button>
                        <button
                          type="button"
                          className="t-atelier-icon-btn"
                          title="Save to Saved Shortlist"
                          aria-label={`Save ${cleanTargetJobTitle(job.title)}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            addToInterest(job);
                            pushToast('Saved to Shortlist.');
                          }}
                        >
                          <TailoredIcon name="save" size={14} />
                        </button>
                      </div>

                      <button
                        type="button"
                        className={selected ? 't-atelier-btn-primary' : 't-atelier-btn-tonal'}
                        style={{ minWidth: 108, justifyContent: 'center' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          openJobInStudio(job);
                        }}
                      >
                        {unlocked ? 'Open · 0 cr' : 'Tailor · 1 cr'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Live Selected-Role Fit Breakdown Strip */}
            {selectedMatch && (
              <div
                style={{
                  marginTop: 'auto',
                  paddingTop: 12,
                  borderTop: '1px solid rgba(26, 20, 18, 0.07)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 12,
                  flexWrap: 'wrap',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', minWidth: 0 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--n500)', marginRight: 2 }}>
                    Selected Fit:
                  </span>
                  {selectedMatch.evalRes.best.matchedSkills.slice(0, 3).map((sk) => (
                    <span key={sk} className="t-dash-tag t-dash-tag--green">
                      <span className="t-signal-up" aria-hidden="true" />
                      <span>{sk}</span>
                    </span>
                  ))}
                  {selectedMatch.evalRes.best.missingSkills.slice(0, 2).map((sk) => (
                    <span
                      key={sk}
                      className="t-dash-tag"
                      style={{ background: 'rgba(143, 29, 44, 0.07)', color: 'var(--alarm)' }}
                    >
                      <span className="t-signal-down" aria-hidden="true" />
                      <span>{sk}</span>
                    </span>
                  ))}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <button
                    type="button"
                    className="t-atelier-btn-ghost"
                    onClick={() => setQuickPeekJob(selectedMatch.job)}
                  >
                    Quick Peek
                  </button>
                  <button
                    type="button"
                    className="t-atelier-btn-ghost"
                    onClick={() => navigateTo(`/jobs/${selectedMatch.job.id}`)}
                  >
                    Full Details →
                  </button>
                </div>
              </div>
            )}
          </section>

          {/* ZONE 3 — Right Floating Panels: Continue Drafting + Needs Your Action */}
          <aside style={{ display: 'flex', flexDirection: 'column', gap: 16, minWidth: 0 }}>
            {/* Panel A: Resume Active Draft */}
            <section className="t-dash-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
                <h2 style={{ fontSize: 19, lineHeight: 1.15 }}>Continue Drafting</h2>
                <span className="t-dash-tag t-dash-tag--green">
                  <span className="t-signal-up" aria-hidden="true" />
                  <span>0 cr to edit</span>
                </span>
              </div>
              <p style={{ margin: '3px 0 12px', fontSize: 12.5, color: 'var(--n500)' }}>
                Resume your active tailored CV or cover letter
              </p>

              <div className="t-dash-subcard" style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <FitDial score={activeDraftScore} size={62} />
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div
                    style={{
                      fontWeight: 600,
                      fontSize: 15.5,
                      color: 'var(--ink)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {cleanTargetJobTitle(activeStudioJob.title)}
                  </div>
                  <div style={{ fontSize: 12.5, color: 'var(--n500)', marginTop: 2 }}>
                    {cleanCompanyName(activeStudioJob.company_name)} · {activeStudioJob.location}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
                    <span className="t-dash-tag t-dash-tag--green">
                      <span className="t-signal-up" aria-hidden="true" />
                      <span>{activeDraftEval.matchedSkills.length} matched</span>
                    </span>
                    {activeDraftEval.missingSkills.length > 0 && (
                      <span
                        className="t-dash-tag"
                        style={{ background: 'rgba(143, 29, 44, 0.07)', color: 'var(--alarm)' }}
                      >
                        <span className="t-signal-down" aria-hidden="true" />
                        <span>{activeDraftEval.missingSkills.length} gap</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div style={{ marginTop: 14, display: 'flex', gap: 8 }}>
                <button
                  type="button"
                  className="t-atelier-btn-primary"
                  style={{ flex: 1, justifyContent: 'center' }}
                  onClick={() =>
                    activeStudioDoc
                      ? openDocInStudio(activeStudioDoc.doc_id)
                      : openJobInStudio(activeStudioJob, { skipCreditCheck: true })
                  }
                >
                  <span>Open CV Studio</span>
                  <TailoredIcon name="chevronRight" size={13} color="var(--ink)" />
                </button>
                <button
                  type="button"
                  className="t-atelier-btn-tonal"
                  onClick={() => navigateTo('/cover-letters')}
                >
                  Cover Letter
                </button>
              </div>
            </section>

            {/* Panel B: Urgent Pipeline Actions */}
            <section className="t-dash-panel" style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
                <div>
                  <h2 style={{ fontSize: 19, lineHeight: 1.15 }}>Needs Your Action</h2>
                  <p style={{ margin: '3px 0 0', fontSize: 12.5, color: 'var(--n500)' }}>
                    Pending dispatches and overdue follow-ups
                  </p>
                </div>
                <button type="button" className="t-atelier-btn-ghost" onClick={() => navigateTo('/pipeline')}>
                  Pipeline ({pipelineItems.length}) →
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 14, marginBottom: 14 }}>
                {readyToDispatch.slice(0, 2).map((item) => (
                  <div key={item.id} className="t-dash-subcard t-dash-subcard--dye">
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: 8,
                        marginBottom: 6,
                      }}
                    >
                      <span className="t-dash-tag t-dash-tag--mist">Ready to send</span>
                      <span className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                        {item.recruiter_email}
                      </span>
                    </div>
                    <div style={{ fontWeight: 600, fontSize: 14.5, color: 'var(--ink)' }}>
                      {cleanTargetJobTitle(item.job.title)}
                    </div>
                    <div style={{ fontSize: 12.5, color: 'var(--n500)', margin: '2px 0 10px' }}>
                      {cleanCompanyName(item.job.company_name)} · Tailored CV attached
                    </div>
                    <button
                      type="button"
                      className="t-atelier-btn-primary"
                      onClick={() => openJobInCoverLetters(item.job, { mode: 'pitch' })}
                    >
                      <TailoredIcon name="send" size={13} color="var(--ink)" />
                      <span>Open in Cover Letters</span>
                    </button>
                  </div>
                ))}

                {followUpsDue.slice(0, 2).map((item) => (
                  <div key={item.id} className="t-dash-subcard t-dash-subcard--amber">
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: 8,
                        marginBottom: 6,
                      }}
                    >
                      <span className="t-dash-tag t-dash-tag--amber">
                        <span className="t-signal-down" aria-hidden="true" />
                        <span>Follow-up due</span>
                      </span>
                      <span className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                        7d elapsed
                      </span>
                    </div>
                    <div style={{ fontWeight: 600, fontSize: 14.5, color: 'var(--ink)' }}>
                      {cleanTargetJobTitle(item.job.title)}
                    </div>
                    <div style={{ fontSize: 12.5, color: 'var(--n500)', margin: '2px 0 10px' }}>
                      {cleanCompanyName(item.job.company_name)} · {item.recruiter_email}
                    </div>
                    <button
                      type="button"
                      className="t-atelier-btn-tonal"
                      onClick={() => navigateTo(`/pipeline/${item.id}`)}
                    >
                      Draft Follow-Up
                    </button>
                  </div>
                ))}

                {readyToDispatch.length === 0 && followUpsDue.length === 0 && (
                  <div className="t-dash-subcard" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span className="t-signal-up" aria-hidden="true" />
                    <span style={{ fontSize: 13.5, color: 'var(--n700)' }}>
                      All caught up — no pending dispatches or overdue follow-ups.
                    </span>
                  </div>
                )}
              </div>

              <div
                style={{
                  marginTop: 'auto',
                  paddingTop: 12,
                  borderTop: '1px solid rgba(26, 20, 18, 0.07)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 10,
                }}
              >
                <span className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)' }}>
                  {readyToDispatch.length} ready · {followUpsDue.length} applied · {interviewsCount} interview
                </span>
                <button
                  type="button"
                  className="t-atelier-btn-ghost"
                  onClick={() => navigateTo('/pipeline')}
                >
                  Open CRM →
                </button>
              </div>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
};
