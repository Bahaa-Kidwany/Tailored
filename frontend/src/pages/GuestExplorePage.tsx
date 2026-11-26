import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { BrandLockup, FitDial, EmptyState } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';
import { ResizableSplitPane } from '../components/common/ResizableSplitPane';
import { computeNinePillarFit } from '../utils/fitEngine';
import { SAMPLE_PROFILE, ProfileAPI } from '../services/profileApi';
import type { JobItem } from '../services/jobsApi';

/**
 * 02 — Public Guest Job Radar & Intent-Preserving Gate (/explore)
 */
export const GuestExplorePage: React.FC = () => {
  const {
    radarJobs,
    hiddenJobIds,
    hideJob,
    navigateTo,
    isAuthenticated,
    currentSearch,
    setPendingIntent,
    saveProfile,
    currentProfile,
    pushToast,
    dir,
  } = useWorkspace();

  const urlParams = new URLSearchParams(currentSearch);
  const [search, setSearch] = useState(urlParams.get('q') || '');
  const [sourceFilter, setSourceFilter] = useState<'all' | 'linkedin' | 'wuzzuf' | 'recruiter'>('all');
  const [modeFilter, setModeFilter] = useState<'all' | 'Remote' | 'Hybrid' | 'On-site'>('all');
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const [gateJob, setGateJob] = useState<{ job: JobItem; action: string } | null>(null);
  const cvInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isAuthenticated) {
      navigateTo(`/radar${currentSearch}`);
    }
  }, [isAuthenticated, navigateTo, currentSearch]);

  const samplePersona = SAMPLE_PROFILE.career_personas[0];

  const visibleJobs = useMemo(() => {
    return radarJobs.filter((j) => {
      if (hiddenJobIds.has(j.id)) return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        const hit =
          j.title.toLowerCase().includes(q) ||
          j.company_name.toLowerCase().includes(q) ||
          j.location.toLowerCase().includes(q) ||
          j.parsed_skills.some((s) => s.toLowerCase().includes(q));
        if (!hit) return false;
      }
      if (sourceFilter !== 'all') {
        const s = (j.source_type || '').toLowerCase();
        if (sourceFilter === 'recruiter' && !s.includes('recruiter') && !s.includes('post')) return false;
        if (sourceFilter === 'linkedin' && !s.includes('linkedin')) return false;
        if (sourceFilter === 'wuzzuf' && !s.includes('wuzzuf')) return false;
      }
      if (modeFilter !== 'all' && j.location_type.toLowerCase() !== modeFilter.toLowerCase()) {
        return false;
      }
      return true;
    });
  }, [radarJobs, hiddenJobIds, search, sourceFilter, modeFilter]);

  const [selectedJobId, setSelectedJobId] = useState<number>(visibleJobs[0]?.id || 101);
  const activeJob = visibleJobs.find((j) => j.id === selectedJobId) || visibleJobs[0] || null;
  const activeFit = activeJob ? computeNinePillarFit(activeJob, samplePersona, SAMPLE_PROFILE) : null;

  const activeFilterCount = (sourceFilter !== 'all' ? 1 : 0) + (modeFilter !== 'all' ? 1 : 0);

  // Keyboard navigation J / K / X
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      if (!visibleJobs.length) return;
      const idx = visibleJobs.findIndex((j) => j.id === activeJob?.id);
      if (e.key.toLowerCase() === 'j') {
        setSelectedJobId(visibleJobs[Math.min(visibleJobs.length - 1, idx + 1)].id);
      } else if (e.key.toLowerCase() === 'k') {
        setSelectedJobId(visibleJobs[Math.max(0, idx - 1)].id);
      } else if (e.key.toLowerCase() === 'x' && activeJob) {
        hideJob(activeJob.id);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [visibleJobs, activeJob, hideJob]);

  const openGate = (job: JobItem, action: string) => {
    setGateJob({ job, action });
  };

  const commitGateToAuth = (mode: 'register' | 'login') => {
    if (!gateJob) return;
    setPendingIntent({
      type: gateJob.action === 'Tailor CV' ? 'tailor_job' : 'inspect_fit',
      jobId: gateJob.job.id,
      label: `${gateJob.action}: ${gateJob.job.company_name} — ${gateJob.job.title}`,
    });
    setGateJob(null);
    navigateTo(mode === 'register' ? '/register' : '/login');
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--chalk)' }}>
      {/* Guest Header */}
      <header className="t-topnav">
        <div className="t-topnav-left">
          <button
            type="button"
            onClick={() => navigateTo('/')}
            style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: 0 }}
          >
            <BrandLockup variant="horizontal" mode="knock" size={24} color="var(--chalk)" dir={dir} />
          </button>
          <div className="t-topnav-divider" />
          <span className="t-mono" style={{ fontSize: 11.5, opacity: 0.85 }}>
            Guest Preview · Sample AI Track Benchmark
          </span>
        </div>

        <div className="t-topnav-right">
          <input
            ref={cvInputRef}
            type="file"
            accept=".tex,.pdf,.docx"
            style={{ display: 'none' }}
            onChange={async (e) => {
              const f = e.target.files?.[0];
              if (!f) return;
              const txt = await f.text();
              const parsed = await ProfileAPI.parseLatex(txt);
              if (parsed.success && parsed.profile && currentProfile?.profile) {
                await saveProfile({ ...currentProfile.profile, ...parsed.profile });
              }
              setPendingIntent({ type: 'cv_upload', jobId: activeJob?.id, label: `Parsed ${f.name}` });
              pushToast(`Parsed ${f.name} — sign up to compute your personal 9-pillar score.`);
              navigateTo('/register');
            }}
          />
          <button type="button" onClick={() => cvInputRef.current?.click()} className="t-btn t-btn--chalk-outline t-btn--sm">
            Drop CV for Your Score
          </button>
          <button type="button" onClick={() => navigateTo('/login')} className="t-nav-link">
            Sign In
          </button>
          <button type="button" onClick={() => navigateTo('/register')} className="t-btn t-btn--primary t-btn--sm">
            Sign Up — 2 Free Credits
          </button>
        </div>
      </header>

      {/* Streamlined 3-Control Filter Bar */}
      <div
        style={{
          height: 52,
          padding: '0 20px',
          background: 'var(--paper)',
          borderBottom: '1.5px solid var(--n300)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          position: 'relative',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, maxWidth: 640 }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <input
              className="t-input"
              style={{ padding: '6px 12px', fontSize: 13.5 }}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search live roles, skills, or cities..."
            />
          </div>
          <div style={{ position: 'relative' }}>
            <button
              type="button"
              onClick={() => setIsFiltersOpen((v) => !v)}
              className="t-btn t-btn--outline t-btn--sm"
            >
              <TailoredIcon name="filter" size={13} />
              <span>Filters{activeFilterCount > 0 ? ` (${activeFilterCount})` : ''}</span>
            </button>
            {isFiltersOpen && (
              <div className="t-popover" style={{ top: 40, left: 0, width: 290 }}>
                <div className="t-label" style={{ marginBottom: 8 }}>Source</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
                  {(['all', 'linkedin', 'wuzzuf', 'recruiter'] as const).map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setSourceFilter(s)}
                      className={`t-btn t-btn--sm ${sourceFilter === s ? 't-btn--ink' : 't-btn--subtle'}`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
                <div className="t-label" style={{ marginBottom: 8 }}>Work Mode</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {(['all', 'Remote', 'Hybrid', 'On-site'] as const).map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setModeFilter(m)}
                      className={`t-btn t-btn--sm ${modeFilter === m ? 't-btn--ink' : 't-btn--subtle'}`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <span className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)' }}>
          {visibleJobs.length} live roles · Sample Benchmark Scores
        </span>
      </div>

      {/* Resizable 38 / 62 Master-Detail Split */}
      <div style={{ flex: 1, minHeight: 0 }}>
        {visibleJobs.length === 0 ? (
          <EmptyState
            icon="radar"
            headline="No public roles match your filters"
            subtext="Reset filters or sign up with 2 free credits to ingest a direct job link."
            ctaLabel="Reset Filters"
            onCta={() => {
              setSearch('');
              setSourceFilter('all');
              setModeFilter('all');
            }}
          />
        ) : (
          <ResizableSplitPane
            storageKey="explore_split"
            defaultLeftPct={38}
            minLeftPx={320}
            minRightPx={420}
            left={
              <div>
                {visibleJobs.map((job) => {
                  const fit = computeNinePillarFit(job, samplePersona, SAMPLE_PROFILE);
                  const active = activeJob?.id === job.id;
                  return (
                    <div
                      key={job.id}
                      className={`t-list-row ${active ? 't-list-row--active' : ''}`}
                      onClick={() => setSelectedJobId(job.id)}
                    >
                      <div style={{ minWidth: 0, flex: 1 }}>
                        <div style={{ fontWeight: 600, fontSize: 14.5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {job.title}
                        </div>
                        <div className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)', marginTop: 3 }}>
                          {job.company_name} · {job.location} · {job.source_type}
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div className="t-list-row-hover-actions">
                          <button
                            type="button"
                            className="t-btn t-btn--ghost t-btn--sm"
                            style={{ padding: 4 }}
                            onClick={(e) => {
                              e.stopPropagation();
                              openGate(job, 'Save to Interest');
                            }}
                            title="Save"
                          >
                            <TailoredIcon name="save" size={14} />
                          </button>
                          <button
                            type="button"
                            className="t-btn t-btn--ghost t-btn--sm"
                            style={{ padding: 4 }}
                            onClick={(e) => {
                              e.stopPropagation();
                              hideJob(job.id);
                            }}
                            title="Hide (X)"
                          >
                            <TailoredIcon name="hide" size={14} />
                          </button>
                        </div>
                        <FitDial score={fit.overallScore} size={52} />
                      </div>
                    </div>
                  );
                })}
              </div>
            }
            right={
              activeJob && activeFit ? (
                <div style={{ padding: 28, background: 'var(--paper)', minHeight: '100%' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      gap: 16,
                      paddingBottom: 18,
                      borderBottom: '1.5px solid var(--n300)',
                    }}
                  >
                    <div>
                      <span className="t-eyebrow">Public Preview</span>
                      <h1 style={{ fontSize: 30, marginTop: 6 }}>{activeJob.title}</h1>
                      <div className="t-mono" style={{ fontSize: 12.5, color: 'var(--n500)', marginTop: 4 }}>
                        {activeJob.company_name} · {activeJob.location} · {activeJob.location_type}
                      </div>
                      <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
                        <button
                          type="button"
                          onClick={() => openGate(activeJob, 'Tailor CV')}
                          className="t-btn t-btn--primary t-btn--sm"
                        >
                          Tailor CV (2 Free Credits)
                        </button>
                        <button
                          type="button"
                          onClick={() => openGate(activeJob, 'Save to Interest')}
                          className="t-btn t-btn--outline t-btn--sm"
                        >
                          Save Job
                        </button>
                        <a
                          href={activeJob.url}
                          target="_blank"
                          rel="noreferrer"
                          className="t-btn t-btn--subtle t-btn--sm"
                        >
                          <TailoredIcon name="external" size={13} />
                          <span>Apply Externally</span>
                        </a>
                      </div>
                    </div>
                    <FitDial score={activeFit.overallScore} size={94} />
                  </div>

                  {/* 1-Line Why Matched */}
                  <div className="t-alert" style={{ marginTop: 18 }}>
                    <div className="t-label" style={{ marginBottom: 4 }}>
                      Benchmark Fit Summary (Sample AI Engineer Profile)
                    </div>
                    <div style={{ fontSize: 14 }}>{activeFit.whyMatched}</div>
                    <button
                      type="button"
                      onClick={() => openGate(activeJob, 'Unlock Your Score')}
                      style={{
                        marginTop: 8,
                        background: 'transparent',
                        border: 'none',
                        padding: 0,
                        fontFamily: 'var(--font-mono)',
                        fontSize: 11,
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        borderBottom: '2px dashed var(--thread)',
                        cursor: 'pointer',
                      }}
                    >
                      Unlock Your Personal 9-Pillar Score
                    </button>
                  </div>

                  {/* Read-Only Surgical Preview */}
                  <div className="t-card" style={{ marginTop: 18, padding: 18, background: 'var(--chalk)' }}>
                    <div className="t-label" style={{ marginBottom: 8 }}>
                      Sample Tailored CV Bullet Preview
                    </div>
                    <div className="t-diff-old" style={{ marginBottom: 6 }}>
                      Built routing &amp; pricing logic for backend APIs.
                    </div>
                    <div className="t-diff-new">
                      Architected {activeJob.parsed_skills.slice(0, 2).join(' & ')} endpoints aligned with{' '}
                      {activeJob.company_name}&rsquo;s core stack.
                    </div>
                  </div>

                  <div style={{ marginTop: 20 }}>
                    <div className="t-label" style={{ color: 'var(--n500)', marginBottom: 8 }}>
                      Extracted Skills
                    </div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {activeJob.parsed_skills.map((s) => (
                        <span key={s} className="t-chip t-chip--notch">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div style={{ marginTop: 22 }}>
                    <div className="t-label" style={{ color: 'var(--n500)', marginBottom: 8 }}>
                      Full Job Description
                    </div>
                    <p style={{ fontSize: 14.5, lineHeight: 1.65, color: 'var(--n700)', whiteSpace: 'pre-line' }}>
                      {activeJob.raw_description}
                    </p>
                  </div>
                </div>
              ) : null
            }
          />
        )}
      </div>

      {/* Intent-Preserving Feature Gate Modal */}
      {gateJob && (
        <div className="t-backdrop" onClick={() => setGateJob(null)}>
          <div className="t-modal" style={{ width: '100%', maxWidth: 520, padding: 32 }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span className="t-eyebrow">Unlock This Opportunity</span>
              <button type="button" onClick={() => setGateJob(null)} className="t-btn t-btn--ghost t-btn--sm">
                <TailoredIcon name="close" size={15} />
              </button>
            </div>
            <h2 style={{ fontSize: 28 }}>
              Sign up to <em>{gateJob.action}</em> for {gateJob.job.company_name}.
            </h2>
            <p style={{ fontSize: 14, color: 'var(--n700)', marginTop: 8 }}>
              Role queued: <strong>{gateJob.job.title}</strong> ({gateJob.job.location}). You receive{' '}
              <strong>2 Free Credits</strong> immediately — zero card required.
            </p>
            <div className="t-stitch" style={{ margin: '18px 0' }} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <button type="button" onClick={() => commitGateToAuth('register')} className="t-btn t-btn--primary">
                Create Free Account &amp; Continue
              </button>
              <button type="button" onClick={() => commitGateToAuth('login')} className="t-btn t-btn--outline">
                Already Have an Account? Sign In
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
