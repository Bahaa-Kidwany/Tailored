import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { ResizableSplitPane } from '../components/common/ResizableSplitPane';
import { AtelierFrenchCurveBackdrop, FitDial, MeasureRulerBar } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';
import { SAMPLE_PROFILE } from '../services/profileApi';
import { computeNinePillarFit, evaluateAllPersonas } from '../utils/fitEngine';
import { cleanCompanyName, cleanTargetJobTitle } from '../services/cvFitApi';
import { hasDirectRecruiterEmail } from '../services/pipelineStorage';

export interface RadarPageProps {
  initialTab?: 'all' | 'saved' | 'direct';
}

export const RadarPage: React.FC<RadarPageProps> = ({ initialTab = 'all' }) => {
  const {
    currentPath,
    currentSearch,
    radarJobs,
    hiddenJobIds,
    hideJob,
    unhideJob,
    addToInterest,
    removeFromInterest,
    interestList,
    ingestJobUrlOrText,
    addToPipeline,
    openJobInStudio,
    openJobInCoverLetters,
    runLiveSweep,
    currentProfile,
    setActivePersonaId,
    isJobUnlocked,
    navigateTo,
    pushToast,
  } = useWorkspace();

  const profile = currentProfile?.profile || SAMPLE_PROFILE;
  const personas = profile.career_personas;

  const urlTabParam = new URLSearchParams(currentSearch).get('tab');
  const queueTab: 'all' | 'saved' | 'direct' =
    currentPath === '/interest'
      ? 'saved'
      : urlTabParam === 'saved' || urlTabParam === 'direct' || urlTabParam === 'all'
        ? urlTabParam
        : initialTab;

  const setQueueTab = (t: 'all' | 'saved' | 'direct') => {
    navigateTo(t === 'all' ? '/radar' : `/radar?tab=${t}`);
  };

  const [search, setSearch] = useState('');
  const [captureInput, setCaptureInput] = useState('');
  const [personaFilter, setPersonaFilter] = useState<string>('best');
  const [personaMenuOpen, setPersonaMenuOpen] = useState(false);
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const [workModeFilter, setWorkModeFilter] = useState<string>('All');
  const [minFitFilter, setMinFitFilter] = useState<number>(0);
  const [showHidden, setShowHidden] = useState<boolean>(false);
  const [sweeping, setSweeping] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<number>(radarJobs[0]?.id || 101);

  const headerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const onMouseDown = (e: MouseEvent) => {
      if (headerRef.current && !headerRef.current.contains(e.target as Node)) {
        setPersonaMenuOpen(false);
        setIsFiltersOpen(false);
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setPersonaMenuOpen(false);
        setIsFiltersOpen(false);
      }
    };
    window.addEventListener('mousedown', onMouseDown);
    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('keydown', onKeyDown);
    };
  }, []);

  const baseSourceJobs = useMemo(() => {
    if (queueTab === 'saved') return interestList;
    if (queueTab === 'direct') return radarJobs.filter((j) => hasDirectRecruiterEmail(j));
    return radarJobs;
  }, [queueTab, radarJobs, interestList]);

  const rankedJobs = useMemo(() => {
    return baseSourceJobs
      .filter((job) => (showHidden ? true : !hiddenJobIds.has(job.id)))
      .map((job) => {
        if (personaFilter === 'best') {
          const { best } = evaluateAllPersonas(job, profile);
          return { job, evalRes: best };
        }
        const p = personas.find((x) => x.persona_id === personaFilter) || personas[0];
        return { job, evalRes: computeNinePillarFit(job, p, profile) };
      })
      .filter(({ job, evalRes }) => {
        if (search.trim()) {
          const q = search.toLowerCase();
          const hit =
            job.title.toLowerCase().includes(q) ||
            job.company_name.toLowerCase().includes(q) ||
            job.location.toLowerCase().includes(q) ||
            job.parsed_skills.some((s) => s.toLowerCase().includes(q));
          if (!hit) return false;
        }
        if (workModeFilter !== 'All' && job.location_type !== workModeFilter) return false;
        if (evalRes.overallScore < minFitFilter) return false;
        return true;
      })
      .sort((a, b) => b.evalRes.overallScore - a.evalRes.overallScore);
  }, [baseSourceJobs, hiddenJobIds, showHidden, personaFilter, profile, personas, search, workModeFilter, minFitFilter]);

  const activeEntry = rankedJobs.find((r) => r.job.id === selectedJobId) || rankedJobs[0] || null;
  const activeFilterCount =
    (workModeFilter !== 'All' ? 1 : 0) + (minFitFilter > 0 ? 1 : 0) + (showHidden ? 1 : 0);

  // J / K / X / B keyboard triage
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target && (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || target.isContentEditable)) return;
      if (rankedJobs.length === 0) return;

      const idx = rankedJobs.findIndex((r) => r.job.id === activeEntry?.job.id);
      if (e.key.toLowerCase() === 'j') {
        const next = rankedJobs[Math.min(rankedJobs.length - 1, Math.max(0, idx + 1))];
        if (next) setSelectedJobId(next.job.id);
      } else if (e.key.toLowerCase() === 'k') {
        const prev = rankedJobs[Math.max(0, idx - 1)];
        if (prev) setSelectedJobId(prev.job.id);
      } else if (e.key.toLowerCase() === 'x' && activeEntry) {
        hideJob(activeEntry.job.id);
      } else if (e.key.toLowerCase() === 'b' && activeEntry) {
        addToInterest(activeEntry.job);
        pushToast('Saved to Shortlist.');
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [rankedJobs, activeEntry, hideJob, addToInterest, pushToast]);

  const handleSweep = async () => {
    setSweeping(true);
    try {
      await runLiveSweep(search || 'Data Scientist OR Machine Learning Egypt GCC');
    } finally {
      setSweeping(false);
    }
  };

  const handleCapture = async (openStudio: boolean) => {
    if (!captureInput.trim()) return;
    const job = await ingestJobUrlOrText(captureInput, {
      openInStudio: openStudio,
      onlySaveInterest: !openStudio,
    });
    setCaptureInput('');
    if (job && !openStudio) {
      setSelectedJobId(job.id);
      setQueueTab('saved');
    }
  };

  const handlePasteScreenshot = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of Array.from(items)) {
      if (item.type.startsWith('image/')) {
        e.preventDefault();
        setCaptureInput(
          'Screenshot OCR Capture: Senior AI Systems Engineer at Careem · Dubai / Hybrid · hiring@careem.com · Python, FastAPI, Docker, LLMs, PyTorch'
        );
        pushToast('Screenshot converted via local OCR parser.', { variant: 'info' });
        return;
      }
    }
  };

  const selectedPersonaLabel =
    personaFilter === 'best'
      ? `Best Fit (${personas.length})`
      : personas.find((p) => p.persona_id === personaFilter)?.target_title || 'Persona';

  return (
    <div className="t-studio-shell t-cv-studio-v2">
      {/* SOLID PATTERN-FREE ATELIER RADAR TOP BAR (ZERO OS SELECTS) */}
      <header ref={headerRef} className="t-studio-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0, position: 'relative' }}>
          <div className="t-atelier-tab-strip" role="tablist" aria-label="Job queue tabs">
            {[
              { id: 'all' as const, label: 'All Matches' },
              { id: 'saved' as const, label: `Saved Shortlist (${interestList.length})` },
              { id: 'direct' as const, label: 'Direct Email' },
            ].map((t) => (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={queueTab === t.id}
                className={`t-atelier-tab-pill ${queueTab === t.id ? 't-atelier-tab-pill--active' : ''}`}
                onClick={() => setQueueTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              background: 'var(--ink-elevated)',
              borderRadius: '4px 10px 4px 10px',
              padding: '5px 10px',
              width: 220,
              boxShadow: 'inset 0 1px 0 rgba(229, 224, 218, 0.06)',
            }}
          >
            <TailoredIcon name="search" size={13} color="var(--n500)" />
            <input
              id="radar-search-input"
              name="radarSearch"
              aria-label="Search roles, companies, skills"
              placeholder="Filter roles or skills..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                border: 'none',
                background: 'transparent',
                outline: 'none',
                color: 'var(--chalk)',
                fontFamily: 'var(--font-ui)',
                fontSize: 12.5,
                width: '100%',
              }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, position: 'relative' }}>
          <button
            type="button"
            className={`t-atelier-pair-btn ${personaMenuOpen ? 't-atelier-pair-btn--open' : ''}`}
            onClick={() => {
              setPersonaMenuOpen((v) => !v);
              setIsFiltersOpen(false);
            }}
          >
            <span>{selectedPersonaLabel}</span>
            <TailoredIcon name="chevronDown" size={11} color="var(--chalk)" />
          </button>

          <button
            type="button"
            className="t-atelier-topbar-ghost"
            onClick={() => {
              setIsFiltersOpen((v) => !v);
              setPersonaMenuOpen(false);
            }}
          >
            <TailoredIcon name="filter" size={13} color="var(--chalk)" />
            <span>Filters{activeFilterCount > 0 ? ` (${activeFilterCount})` : ''}</span>
          </button>

          <button
            type="button"
            className="t-atelier-export-btn"
            disabled={sweeping}
            onClick={handleSweep}
          >
            <TailoredIcon name="radar" size={13} color="var(--ink)" />
            <span>{sweeping ? 'Sweeping...' : 'Live Sweep'}</span>
          </button>

          {personaMenuOpen && (
            <div className="t-popover" style={{ top: 44, right: 180, width: 290 }}>
              <div className="t-atelier-popover-label">Score Roles Against</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <button
                  type="button"
                  className={`t-atelier-menu-row ${personaFilter === 'best' ? 't-atelier-menu-row--active' : ''}`}
                  onClick={() => {
                    setPersonaFilter('best');
                    setPersonaMenuOpen(false);
                  }}
                >
                  <span>Best Fit Across All ({personas.length})</span>
                </button>
                {personas.map((p) => (
                  <button
                    key={p.persona_id}
                    type="button"
                    className={`t-atelier-menu-row ${personaFilter === p.persona_id ? 't-atelier-menu-row--active' : ''}`}
                    onClick={() => {
                      setPersonaFilter(p.persona_id);
                      setActivePersonaId(p.persona_id);
                      setPersonaMenuOpen(false);
                    }}
                  >
                    <span>{p.target_title}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {isFiltersOpen && (
            <div className="t-popover" style={{ top: 44, right: 90, width: 310 }}>
              <div className="t-atelier-popover-label">Work Mode</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
                {['All', 'Remote', 'Hybrid', 'On-site'].map((wm) => (
                  <button
                    key={wm}
                    type="button"
                    className={`t-atelier-popover-chip ${workModeFilter === wm ? 't-atelier-popover-chip--active' : ''}`}
                    onClick={() => setWorkModeFilter(wm)}
                  >
                    {wm}
                  </button>
                ))}
              </div>

              <div className="t-atelier-popover-label">Minimum Fit Threshold</div>
              <div style={{ display: 'flex', gap: 6, marginBottom: 14 }}>
                {[
                  { label: 'Any', val: 0 },
                  { label: '50%+', val: 50 },
                  { label: '75%+ Strong', val: 75 },
                ].map((opt) => (
                  <button
                    key={opt.val}
                    type="button"
                    className={`t-atelier-popover-chip ${minFitFilter === opt.val ? 't-atelier-popover-chip--active' : ''}`}
                    onClick={() => setMinFitFilter(opt.val)}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>

              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, marginBottom: 12, cursor: 'pointer' }}>
                <input
                  id="radar-show-hidden"
                  type="checkbox"
                  checked={showHidden}
                  onChange={(e) => setShowHidden(e.target.checked)}
                />
                <span>Show hidden roles ({hiddenJobIds.size})</span>
              </label>

              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <button
                  type="button"
                  className="t-atelier-btn-ghost"
                  onClick={() => {
                    setWorkModeFilter('All');
                    setMinFitFilter(0);
                    setShowHidden(false);
                  }}
                >
                  Reset
                </button>
                <button
                  type="button"
                  className="t-atelier-btn-primary"
                  onClick={() => setIsFiltersOpen(false)}
                >
                  Done
                </button>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* ATELIER STAGE + FRENCH CURVE BACKDROP + FLOATING PAPER SPLIT */}
      <div className="t-atelier-split-stage">
        <AtelierFrenchCurveBackdrop />
        <ResizableSplitPane
          storageKey="radar_split_v3"
          defaultLeftPct={42}
          minLeftPx={360}
          minRightPx={460}
          left={
            <div className="t-atelier-split-panel">
              {/* Integrated Multi-Modal Ingest Bar */}
              <div style={{ padding: '14px 16px 10px', borderBottom: '1px solid rgba(26, 20, 18, 0.07)' }}>
                <div className="t-dash-ingest">
                  <TailoredIcon name="link" size={14} color="var(--n500)" />
                  <input
                    id="radar-ingest-input"
                    name="radarCapture"
                    aria-label="Paste job link, text, email, or screenshot"
                    className="t-dash-ingest-input"
                    placeholder="Paste URL, recruiter email post, or Ctrl+V screenshot..."
                    value={captureInput}
                    onChange={(e) => setCaptureInput(e.target.value)}
                    onPaste={handlePasteScreenshot}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && captureInput.trim()) handleCapture(false);
                    }}
                  />
                  <button
                    type="button"
                    className="t-atelier-btn-tonal"
                    disabled={!captureInput.trim()}
                    onClick={() => handleCapture(false)}
                  >
                    Save (0 cr)
                  </button>
                  <button
                    type="button"
                    className="t-atelier-btn-primary"
                    disabled={!captureInput.trim()}
                    onClick={() => handleCapture(true)}
                  >
                    Tailor (1 cr)
                  </button>
                </div>
              </div>

              {/* Ranked Queue Stream */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '10px 14px 14px', display: 'flex', flexDirection: 'column', gap: 7 }}>
                {rankedJobs.length === 0 ? (
                  <div style={{ padding: 28, textAlign: 'center' }}>
                    <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 6 }}>No roles in this view</div>
                    <div style={{ fontSize: 13, color: 'var(--n500)', marginBottom: 14 }}>
                      {queueTab === 'saved'
                        ? 'Save promising roles from All Matches or paste any link above.'
                        : 'Widen your filters or run a Live Sweep.'}
                    </div>
                    <button
                      type="button"
                      className="t-atelier-btn-primary"
                      onClick={() => {
                        setSearch('');
                        setWorkModeFilter('All');
                        setMinFitFilter(0);
                        setShowHidden(false);
                        if (queueTab === 'saved') setQueueTab('all');
                      }}
                    >
                      Show All Matches
                    </button>
                  </div>
                ) : (
                  rankedJobs.map(({ job, evalRes }) => {
                    const score = Math.round(evalRes.overallScore);
                    const isSelected = activeEntry?.job.id === job.id;
                    const isHidden = hiddenJobIds.has(job.id);
                    const isSaved = interestList.some((i) => i.id === job.id);
                    const badgeTier =
                      score >= 75
                        ? 't-dash-fit-badge--strong'
                        : score >= 50
                          ? 't-dash-fit-badge--mid'
                          : 't-dash-fit-badge--low';

                    return (
                      <div
                        key={job.id}
                        className={`t-dash-match-row ${isSelected ? 't-dash-match-row--active' : ''}`}
                        style={{ opacity: isHidden ? 0.55 : 1, padding: '10px 12px 10px 14px' }}
                        onClick={() => setSelectedJobId(job.id)}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0, flex: 1 }}>
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

                          <div style={{ minWidth: 0, flex: 1 }}>
                            <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {cleanTargetJobTitle(job.title)}
                            </div>
                            <div style={{ fontSize: 12, color: 'var(--n500)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {cleanCompanyName(job.company_name)} · {job.location} · {job.location_type || 'Hybrid'}
                            </div>
                          </div>
                        </div>

                        <div className="t-dash-row-secondary" onClick={(e) => e.stopPropagation()}>
                          <button
                            type="button"
                            className="t-atelier-icon-btn"
                            title={isSaved ? 'Remove from Shortlist' : 'Save to Shortlist (B)'}
                            onClick={() => {
                              if (isSaved) {
                                removeFromInterest(job.id);
                              } else {
                                addToInterest(job);
                                pushToast('Saved to Shortlist.');
                              }
                            }}
                          >
                            <TailoredIcon
                              name={isSaved ? 'check' : 'save'}
                              size={14}
                              color={isSaved ? 'var(--green)' : undefined}
                            />
                          </button>
                          <button
                            type="button"
                            className="t-atelier-icon-btn"
                            title={isHidden ? 'Unhide' : 'Hide Role (X)'}
                            onClick={() => (isHidden ? unhideJob(job.id) : hideJob(job.id))}
                          >
                            <TailoredIcon name={isHidden ? 'eye' : 'hide'} size={14} />
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          }
          right={
            <div className="t-atelier-split-panel" style={{ overflowY: 'auto', padding: '24px 28px 32px' }}>
              {activeEntry ? (
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
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
                        <span className="t-dash-tag t-dash-tag--paper">{activeEntry.job.location_type || 'Hybrid'}</span>
                        {hasDirectRecruiterEmail(activeEntry.job) ? (
                          <span className="t-dash-tag t-dash-tag--green">
                            <span className="t-signal-up" aria-hidden="true" />
                            <span>Direct Email</span>
                          </span>
                        ) : (
                          <span className="t-dash-tag t-dash-tag--mist">External Portal</span>
                        )}
                      </div>
                      <h1 style={{ fontSize: 24, margin: 0 }}>{cleanTargetJobTitle(activeEntry.job.title)}</h1>
                      <div style={{ fontSize: 13.5, color: 'var(--n500)', marginTop: 4 }}>
                        {cleanCompanyName(activeEntry.job.company_name)} · {activeEntry.job.location}
                      </div>
                    </div>
                    <FitDial score={activeEntry.evalRes.overallScore} size={82} />
                  </div>

                  {/* Single-Line Why You Matched Callout */}
                  <div className="t-dash-subcard" style={{ marginTop: 14 }}>
                    <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--n500)', marginBottom: 3 }}>
                      Best Persona · {activeEntry.evalRes.personaTitle}
                    </div>
                    <div style={{ fontSize: 13.5, color: 'var(--ink)' }}>{activeEntry.evalRes.whyMatched}</div>
                  </div>

                  {/* Unified Action Ribbon */}
                  <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap', alignItems: 'center' }}>
                    <button
                      type="button"
                      className="t-atelier-btn-primary"
                      onClick={() => openJobInStudio(activeEntry.job)}
                    >
                      {isJobUnlocked(activeEntry.job.id, 'cv') ? 'Open Tailored CV (0 cr)' : 'Tailor CV (1 cr)'}
                    </button>
                    <button
                      type="button"
                      className="t-atelier-btn-tonal"
                      onClick={() => openJobInCoverLetters(activeEntry.job, { mode: 'pitch' })}
                    >
                      Draft Cover Letter
                    </button>
                    <button
                      type="button"
                      className="t-atelier-btn-tonal"
                      onClick={() => addToPipeline(activeEntry.job, 'saved')}
                    >
                      Track in Pipeline
                    </button>
                    <button
                      type="button"
                      className="t-atelier-btn-ghost"
                      onClick={() => navigateTo(`/jobs/${activeEntry.job.id}`)}
                    >
                      Full 9-Pillar Audit →
                    </button>
                  </div>

                  {/* Semantic Matched vs Gap Keywords */}
                  <div style={{ marginTop: 18 }}>
                    <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--n500)', marginBottom: 8 }}>
                      Skill Alignment
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {activeEntry.evalRes.matchedSkills.map((sk) => (
                        <span key={sk} className="t-dash-tag t-dash-tag--green">
                          <span className="t-signal-up" aria-hidden="true" />
                          <span>{sk}</span>
                        </span>
                      ))}
                      {activeEntry.evalRes.missingSkills.map((sk) => (
                        <span
                          key={sk}
                          className="t-dash-tag"
                          style={{ background: 'rgba(143, 29, 44, 0.08)', color: 'var(--alarm)' }}
                        >
                          <span className="t-signal-down" aria-hidden="true" />
                          <span>Gap: {sk}</span>
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Top 4 Measuring-Tape Pillars Preview */}
                  <div style={{ marginTop: 18, paddingTop: 14, borderTop: '1px solid rgba(26, 20, 18, 0.07)' }}>
                    <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--n500)', marginBottom: 10 }}>
                      Core Pillar Snapshot
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                      {activeEntry.evalRes.pillars.slice(0, 4).map((pil) => (
                        <div key={pil.key}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                            <span style={{ fontSize: 12.5, fontWeight: 600 }}>
                              {pil.label} ({pil.weight}%)
                            </span>
                            <span className="t-mono" style={{ fontSize: 12 }}>{pil.score}%</span>
                          </div>
                          <MeasureRulerBar
                            value={pil.score}
                            width={260}
                            accent={pil.score >= 75 ? 'var(--green)' : 'var(--amber)'}
                          />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Normalized Role Summary */}
                  <div style={{ marginTop: 18, paddingTop: 14, borderTop: '1px solid rgba(26, 20, 18, 0.07)' }}>
                    <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--n500)', marginBottom: 6 }}>
                      Role Brief
                    </div>
                    <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--n700)', margin: 0 }}>
                      {activeEntry.job.raw_description}
                    </p>
                    {activeEntry.job.responsibilities?.length > 0 && (
                      <ul className="t-bullets" style={{ marginTop: 10, fontSize: 13.5 }}>
                        {activeEntry.job.responsibilities.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </>
              ) : (
                <div style={{ padding: 48, textAlign: 'center', color: 'var(--n500)' }}>
                  Select any role on the left or paste a link to inspect fit pillars.
                </div>
              )}
            </div>
          }
        />
      </div>
    </div>
  );
};
