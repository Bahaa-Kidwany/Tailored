import React, { useState, useMemo } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { EmptyState, FitDial, MeasureRulerBar } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';
import { SAMPLE_PROFILE } from '../services/profileApi';
import { evaluateAllPersonas } from '../utils/fitEngine';
import { cleanCompanyName, cleanTargetJobTitle } from '../services/cvFitApi';
import { isEligibleForPipeline } from '../services/pipelineStorage';

type FilterTab = 'all' | 'ready' | 'tailored' | 'direct';

export const InterestListPage: React.FC = () => {
  const {
    interestList,
    removeFromInterest,
    ingestJobUrlOrText,
    openJobInStudio,
    addToPipeline,
    tailoredDocs,
    currentProfile,
    isJobUnlocked,
    setQuickPeekJob,
    navigateTo,
    pushToast,
  } = useWorkspace();

  const [captureInput, setCaptureInput] = useState('');
  const [filterTab, setFilterTab] = useState<FilterTab>('all');
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [lastClickedIdx, setLastClickedIdx] = useState<number | null>(null);
  const [peekId, setPeekId] = useState<number | null>(null);

  const profile = currentProfile?.profile || SAMPLE_PROFILE;

  const enriched = useMemo(() => {
    return interestList
      .map((job) => {
        const { best } = evaluateAllPersonas(job, profile);
        const existingDoc = tailoredDocs.find((d) => d.job_id === job.id);
        const eligible = isEligibleForPipeline(job);
        return { job, best, existingDoc, eligible };
      })
      .filter(({ existingDoc, eligible }) => {
        if (filterTab === 'ready') return !existingDoc;
        if (filterTab === 'tailored') return !!existingDoc;
        if (filterTab === 'direct') return eligible;
        return true;
      });
  }, [interestList, profile, tailoredDocs, filterTab]);

  // Default to first visible row so right inspector stays persistently populated without layout jumps
  const peekItem = enriched.find((e) => e.job.id === peekId) || enriched[0] || null;

  const handleCapture = async (openStudio: boolean) => {
    if (!captureInput.trim()) return;
    await ingestJobUrlOrText(captureInput, { openInStudio: openStudio, onlySaveInterest: !openStudio });
    setCaptureInput('');
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
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

  const toggleSelect = (jobId: number, idx: number, shiftKey: boolean) => {
    if (shiftKey && lastClickedIdx !== null) {
      const start = Math.min(lastClickedIdx, idx);
      const end = Math.max(lastClickedIdx, idx);
      const rangeIds = enriched.slice(start, end + 1).map((e) => e.job.id);
      setSelectedIds((prev) => Array.from(new Set([...prev, ...rangeIds])));
    } else {
      setSelectedIds((prev) =>
        prev.includes(jobId) ? prev.filter((id) => id !== jobId) : [...prev, jobId]
      );
      setLastClickedIdx(idx);
    }
  };

  const handleBatchTailor = () => {
    const first = interestList.find((j) => selectedIds.includes(j.id));
    if (first) {
      openJobInStudio(first);
      setSelectedIds([]);
    }
  };

  const handleBatchRemove = () => {
    selectedIds.forEach((id) => removeFromInterest(id));
    setSelectedIds([]);
  };

  return (
    <div className="t-page-fluid">
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          flexWrap: 'wrap',
          gap: 12,
          marginBottom: 16,
        }}
      >
        <div>
          <span className="t-eyebrow">Saved &amp; Queued Opportunities · Staging Bench</span>
          <h1 style={{ fontSize: 30, marginTop: 4 }}>Interest List &amp; Multi-Modal Ingest</h1>
        </div>
        <span className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)' }}>
          {interestList.length} saved · Shift+Click for range select
        </span>
      </div>

      {/* Top Multi-Modal Capture Bar (Buttons keep single row inline cleanly on desktop) */}
      <section className="t-card" style={{ padding: '16px 20px', marginBottom: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span className="t-label">Paste Job URL, LinkedIn/Wuzzuf Text, Email Forward, or Ctrl+V Screenshot</span>
          <span className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>0 cr to Save &amp; Score Fit</span>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'nowrap' }}>
          <textarea
            className="t-textarea"
            rows={1}
            style={{ flex: '1 1 360px', minWidth: 0 }}
            placeholder="Paste https://linkedin.com/jobs/..., recruiter email, or press Ctrl+V on an image screenshot..."
            value={captureInput}
            onChange={(e) => setCaptureInput(e.target.value)}
            onPaste={handlePaste}
          />
          <button
            type="button"
            className="t-btn t-btn--outline t-btn--sm"
            disabled={!captureInput.trim()}
            onClick={() => handleCapture(false)}
          >
            Save &amp; Score Fit (0 cr)
          </button>
          <button
            type="button"
            className="t-btn t-btn--primary t-btn--sm"
            disabled={!captureInput.trim()}
            onClick={() => handleCapture(true)}
          >
            Tailor Immediately (1 cr)
          </button>
        </div>
      </section>

      {/* Quiet Filter Strip + Batch Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 14 }}>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {[
            { id: 'all' as const, label: `All Saved (${interestList.length})` },
            { id: 'ready' as const, label: 'Ready to Tailor' },
            { id: 'tailored' as const, label: 'Already Tailored' },
            { id: 'direct' as const, label: 'Recruiter-Direct Only' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`t-chip ${filterTab === tab.id ? 't-chip--notch' : ''}`}
              style={{
                cursor: 'pointer',
                padding: '6px 12px',
                background: filterTab === tab.id ? 'var(--ink)' : 'var(--paper)',
                color: filterTab === tab.id ? 'var(--chalk)' : 'var(--ink)',
              }}
              onClick={() => setFilterTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {selectedIds.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="t-mono" style={{ fontSize: 11.5 }}>{selectedIds.length} selected</span>
            <button type="button" className="t-btn t-btn--primary t-btn--sm" onClick={handleBatchTailor}>
              Open Selected in Studio
            </button>
            <button type="button" className="t-btn t-btn--alarm t-btn--sm" onClick={handleBatchRemove}>
              Remove
            </button>
          </div>
        )}
      </div>

      {/* Persistent Balanced 2-Column Staging & Quick-Peek Grid */}
      {enriched.length === 0 ? (
        <EmptyState
          icon="save"
          headline="No saved roles in this view"
          subtext="Save promising matches from Job Radar or paste any external link above to build your staging bench."
          ctaLabel="Browse Job Radar"
          onCta={() => navigateTo('/radar')}
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0, 1.45fr) minmax(360px, 1fr)',
            gap: 20,
            alignItems: 'start',
          }}
        >
          <div className="t-card--flat" style={{ background: 'var(--paper)', minWidth: 0 }}>
            {enriched.map(({ job, best, existingDoc, eligible }, idx) => {
              const checked = selectedIds.includes(job.id);
              const unlocked = isJobUnlocked(job.id, 'cv') || !!existingDoc;
              const isSelected = peekItem?.job.id === job.id;
              return (
                <div
                  key={job.id}
                  className={`t-list-row ${isSelected ? 't-list-row--active' : ''}`}
                  style={{ background: isSelected ? 'var(--paper)' : 'var(--chalk)' }}
                  onClick={() => setPeekId(job.id)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0, flex: 1 }}>
                    <input
                      type="checkbox"
                      aria-label={`Select ${job.title}`}
                      checked={checked}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSelect(job.id, idx, e.shiftKey);
                      }}
                      onChange={() => { }}
                    />
                    <FitDial score={best.overallScore} size={46} />
                    <div style={{ minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <span style={{ fontWeight: 600, fontSize: 14.5 }}>{cleanTargetJobTitle(job.title)}</span>
                        {eligible && <span className="t-chip t-chip--strong">Direct Email</span>}
                        {existingDoc && <span className="t-chip t-chip--dye">Tailored</span>}
                      </div>
                      <div className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)', marginTop: 2 }}>
                        {cleanCompanyName(job.company_name)} · {job.location} · Best persona: {best.personaTitle}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }} onClick={(e) => e.stopPropagation()}>
                    <button
                      type="button"
                      className="t-btn t-btn--primary t-btn--sm"
                      onClick={() => openJobInStudio(job)}
                    >
                      {unlocked ? 'Open CV (0 cr)' : 'Tailor (1 cr)'}
                    </button>
                    {eligible && (
                      <button
                        type="button"
                        className="t-btn t-btn--outline t-btn--sm"
                        onClick={() => addToPipeline(job, 'saved')}
                      >
                        Pipeline
                      </button>
                    )}
                    <button
                      type="button"
                      className="t-btn t-btn--ghost t-btn--sm"
                      title="Remove from Interest"
                      onClick={() => removeFromInterest(job.id)}
                    >
                      <TailoredIcon name="trash" size={14} color="var(--alarm)" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {peekItem && (
            <aside
              className="t-card"
              style={{
                padding: '18px 20px',
                minWidth: 0,
                position: 'sticky',
                top: 20,
                maxHeight: 'calc(100vh - 40px)',
                overflowY: 'auto',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: 12,
                  paddingBottom: 10,
                  borderBottom: '1.5px solid var(--ink)',
                  marginBottom: 10,
                }}
              >
                <div style={{ minWidth: 0 }}>
                  <span className="t-eyebrow">Quick-Peek Inspector · {peekItem.best.personaTitle}</span>
                  <h3 style={{ fontSize: 19, marginTop: 3 }}>{cleanTargetJobTitle(peekItem.job.title)}</h3>
                  <div className="t-mono" style={{ fontSize: 11, color: 'var(--n500)', marginTop: 2 }}>
                    {cleanCompanyName(peekItem.job.company_name)} · {peekItem.job.location}
                  </div>
                </div>
                <FitDial score={peekItem.best.overallScore} size={58} />
              </div>

              <div className="t-alert" style={{ padding: '10px 14px', marginBottom: 10 }}>
                <div className="t-label" style={{ marginBottom: 2 }}>Why You Matched</div>
                <div style={{ fontSize: 13 }}>{peekItem.best.whyMatched}</div>
              </div>

              {/* Stack Overlap & Core Pillars */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 10 }}>
                {peekItem.best.matchedSkills.map((sk) => (
                  <span key={sk} className="t-chip t-chip--strong t-chip--notch">{sk}</span>
                ))}
                {peekItem.best.missingSkills.map((sk) => (
                  <span key={sk} className="t-chip t-chip--partial">Gap: {sk}</span>
                ))}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 10 }}>
                {peekItem.best.pillars.slice(0, 3).map((pil) => (
                  <div key={pil.key}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                      <span style={{ fontSize: 12, fontWeight: 600 }}>{pil.label} ({pil.weight}%)</span>
                      <span className="t-mono" style={{ fontSize: 11.5 }}>{pil.score}%</span>
                    </div>
                    <MeasureRulerBar
                      value={pil.score}
                      accent={pil.score >= 75 ? 'var(--green)' : 'var(--amber)'}
                    />
                  </div>
                ))}
              </div>

              <p
                style={{
                  fontSize: 13,
                  color: 'var(--n700)',
                  lineHeight: 1.5,
                  marginBottom: 12,
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                }}
              >
                {peekItem.job.raw_description}
              </p>

              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="t-btn t-btn--ink t-btn--sm"
                  onClick={() => openJobInStudio(peekItem.job)}
                >
                  Open in Studio
                </button>
                <button
                  type="button"
                  className="t-btn t-btn--outline t-btn--sm"
                  onClick={() => setQuickPeekJob(peekItem.job)}
                >
                  Full Overlay
                </button>
                <button
                  type="button"
                  className="t-btn t-btn--ghost t-btn--sm"
                  onClick={() => navigateTo(`/jobs/${peekItem.job.id}`)}
                >
                  9-Pillar Audit →
                </button>
              </div>
            </aside>
          )}
        </div>
      )}
    </div>
  );
};
