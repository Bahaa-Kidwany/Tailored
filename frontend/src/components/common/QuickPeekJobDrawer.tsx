import React from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { FitDial } from '../../brand/BrandElements';
import { TailoredIcon } from '../../brand/TailoredIcons';
import { evaluateAllPersonas } from '../../utils/fitEngine';
import { SAMPLE_PROFILE } from '../../services/profileApi';
import { isEligibleForPipeline } from '../../services/pipelineStorage';

export const QuickPeekJobDrawer: React.FC = () => {
  const {
    quickPeekJob,
    setQuickPeekJob,
    currentProfile,
    openJobInStudio,
    addToInterest,
    addToPipeline,
    openJobInCoverLetters,
    navigateTo,
    isJobUnlocked,
    dir,
  } = useWorkspace();

  if (!quickPeekJob) return null;

  const profile = currentProfile?.profile || SAMPLE_PROFILE;
  const { best } = evaluateAllPersonas(quickPeekJob, profile);
  const unlocked = isJobUnlocked(quickPeekJob.id, 'cv');
  const eligible = isEligibleForPipeline(quickPeekJob);

  return (
    <div className="t-drawer-backdrop" onClick={() => setQuickPeekJob(null)}>
      <aside
        className={`t-drawer ${dir === 'ltr' ? 't-drawer--right' : ''}`}
        style={{ width: 520, padding: 28, gap: 18 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            paddingBottom: 14,
            borderBottom: '1.5px solid var(--ink)',
          }}
        >
          <div style={{ flex: 1 }}>
            <span className="t-eyebrow">Quick Peek</span>
            <h2 style={{ fontSize: 24, marginTop: 6 }}>{quickPeekJob.title}</h2>
            <div className="t-mono" style={{ fontSize: 12, color: 'var(--n500)', marginTop: 4 }}>
              {quickPeekJob.company_name} · {quickPeekJob.location} · {quickPeekJob.location_type}
            </div>
          </div>
          <FitDial score={best.overallScore} size={82} />
          <button
            type="button"
            onClick={() => setQuickPeekJob(null)}
            className="t-btn t-btn--ghost t-btn--sm"
            aria-label="Close quick peek"
          >
            <TailoredIcon name="close" size={16} />
          </button>
        </div>

        <div className="t-alert">
          <div className="t-label" style={{ marginBottom: 4 }}>
            Why you matched · {best.personaTitle}
          </div>
          <div style={{ fontSize: 13.5 }}>{best.whyMatched}</div>
        </div>

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            type="button"
            className="t-btn t-btn--primary t-btn--sm"
            onClick={() => {
              const job = quickPeekJob;
              setQuickPeekJob(null);
              openJobInStudio(job);
            }}
          >
            <TailoredIcon name="needle" size={14} />
            <span>{unlocked ? 'Open Tailored CV (0 cr)' : 'Tailor CV · 1 cr'}</span>
          </button>

          <button
            type="button"
            className="t-btn t-btn--outline t-btn--sm"
            onClick={() => {
              addToInterest(quickPeekJob);
            }}
          >
            <TailoredIcon name="save" size={14} />
            <span>Save to Interest</span>
          </button>

          {eligible ? (
            quickPeekJob.recruiter_email ? (
              <button
                type="button"
                className="t-btn t-btn--ink t-btn--sm"
                onClick={() => {
                  const j = quickPeekJob;
                  setQuickPeekJob(null);
                  addToPipeline(j, 'in_process');
                  openJobInCoverLetters(j, { mode: 'pitch' });
                }}
              >
                <TailoredIcon name="send" size={14} />
                <span>Send Email</span>
              </button>
            ) : (
              <button
                type="button"
                className="t-btn t-btn--ink t-btn--sm"
                onClick={() => addToPipeline(quickPeekJob, 'saved')}
              >
                <span>Add to Pipeline</span>
              </button>
            )
          ) : (
            <a
              href={quickPeekJob.url}
              target="_blank"
              rel="noreferrer"
              className="t-btn t-btn--subtle t-btn--sm"
            >
              <TailoredIcon name="external" size={13} />
              <span>Apply on {quickPeekJob.source_type === 'wuzzuf' ? 'Wuzzuf' : 'LinkedIn'}</span>
            </a>
          )}

          <button
            type="button"
            className="t-btn t-btn--ghost t-btn--sm"
            onClick={() => {
              const id = quickPeekJob.id;
              setQuickPeekJob(null);
              navigateTo(`/jobs/${id}`);
            }}
          >
            <span>Full 9-Pillar Report</span>
          </button>
        </div>

        <div>
          <div className="t-label" style={{ color: 'var(--n500)', marginBottom: 8 }}>
            Matched &amp; Bridgeable Skills
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {best.matchedSkills.map((sk) => (
              <span key={sk} className="t-chip t-chip--notch t-chip--strong">
                {sk}
              </span>
            ))}
            {best.missingSkills.map((sk) => (
              <span key={sk} className="t-chip t-chip--notch t-chip--partial">
                {sk} (Bridge)
              </span>
            ))}
          </div>
        </div>

        <div>
          <div className="t-label" style={{ color: 'var(--n500)', marginBottom: 8 }}>
            Full Description
          </div>
          <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--n700)', whiteSpace: 'pre-line' }}>
            {quickPeekJob.raw_description}
          </p>
        </div>
      </aside>
    </div>
  );
};
