import React, { useState, useMemo } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { ResizableSplitPane } from '../components/common/ResizableSplitPane';
import { EmptyState, FitDial } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';
import { SAMPLE_PROFILE } from '../services/profileApi';
import { evaluateAllPersonas } from '../utils/fitEngine';
import { cleanCompanyName, cleanTargetJobTitle, CvFitAPI } from '../services/cvFitApi';
import { type PipelineStatus } from '../services/pipelineStorage';

const PIPELINE_STAGES: { id: PipelineStatus; label: string }[] = [
  { id: 'saved', label: 'Saved' },
  { id: 'in_process', label: 'In Process' },
  { id: 'applied', label: 'Applied' },
  { id: 'interview', label: 'Interview' },
];

export const ApplicationDetailPage: React.FC = () => {
  const {
    currentPath,
    pipelineItems,
    pipelineExtras,
    updatePipelineStage,
    updatePipelineEmail,
    updatePipelineExtras,
    removeFromPipeline,
    tailoredDocs,
    openJobInStudio,
    forkSavedDoc,
    openJobInCoverLetters,
    currentProfile,
    navigateTo,
    pushToast,
  } = useWorkspace();

  const idMatch = currentPath.match(/^\/pipeline\/([a-zA-Z0-9_-]+)/);
  const targetId = idMatch ? idMatch[1] : pipelineItems[0]?.id;
  const item = pipelineItems.find((p) => p.id === targetId) || pipelineItems[0];

  const profile = currentProfile?.profile || SAMPLE_PROFILE;
  const extras = item ? pipelineExtras[item.id] || { rounds: [] } : { rounds: [] };

  const [emailInput, setEmailInput] = useState(item?.recruiter_email || '');
  const [recruiterName, setRecruiterName] = useState(extras.recruiterName || '');
  const [followUpDate, setFollowUpDate] = useState(extras.followUpDate || '');
  const [interviewDate, setInterviewDate] = useState(extras.interviewDate || '');
  const [compNotes, setCompNotes] = useState(extras.compensationNotes || '');
  const [newRoundName, setNewRoundName] = useState('');
  const [newRoundNotes, setNewRoundNotes] = useState('');

  const fitEval = useMemo(
    () => (item ? evaluateAllPersonas(item.job, profile).best : null),
    [item, profile]
  );

  if (!item || !fitEval) {
    return (
      <EmptyState
        icon="pipeline"
        headline="Application dossier not found"
        subtext="This application thread may have been removed."
        ctaLabel="Back to Pipeline"
        onCta={() => navigateTo('/pipeline')}
      />
    );
  }

  const matchingDoc = tailoredDocs.find((d) => d.job_id === item.job.id);
  const company = cleanCompanyName(item.job.company_name);
  const role = cleanTargetJobTitle(item.job.title);
  const frozenFile =
    extras.frozenPdfName ||
    `${profile.personal_info.full_name.replace(/\s+/g, '_')}_CV_${company.replace(/\s+/g, '_')}_FROZEN.pdf`;

  const saveInspector = () => {
    updatePipelineEmail(item.id, emailInput);
    updatePipelineExtras(item.id, {
      recruiterName,
      followUpDate,
      interviewDate,
      compensationNotes: compNotes,
    });
    pushToast('Saved recruiter dossier fields.', { variant: 'success' });
  };

  const handleAddRound = () => {
    if (!newRoundName.trim()) return;
    updatePipelineExtras(item.id, {
      rounds: [
        ...(extras.rounds || []),
        {
          id: `rnd_${Date.now()}`,
          round: newRoundName.trim(),
          date: interviewDate || 'Scheduled',
          interviewer: recruiterName || 'Hiring Manager',
          notes: newRoundNotes.trim() || 'Prepared architecture & fit gap talking points.',
        },
      ],
    });
    setNewRoundName('');
    setNewRoundNotes('');
    pushToast('Added interview round.');
  };

  const draftFollowUpNudge = () => {
    openJobInCoverLetters(item.job, { mode: 'followup' });
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Top Breadcrumb + Brand Stage Progress Rail */}
      <div
        style={{
          background: 'var(--paper)',
          borderBottom: '1.5px solid var(--ink)',
          padding: '10px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 14,
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button type="button" className="t-btn t-btn--ghost t-btn--sm" onClick={() => navigateTo('/pipeline')}>
            <TailoredIcon name="back" size={14} />
            Pipeline
          </button>
          <span style={{ fontWeight: 600, fontSize: 15 }}>
            {company} — {role}
          </span>
        </div>

        <div style={{ display: 'flex', gap: 4 }}>
          {PIPELINE_STAGES.map((st, idx) => {
            const active = item.status === st.id;
            const passed = PIPELINE_STAGES.findIndex((s) => s.id === item.status) > idx;
            return (
              <button
                key={st.id}
                type="button"
                className="t-mono"
                onClick={() => updatePipelineStage(item.id, st.id)}
                style={{
                  padding: '5px 12px',
                  fontSize: 11,
                  border: `1.5px solid ${active || passed ? 'var(--ink)' : 'var(--n300)'}`,
                  background: active ? 'var(--thread)' : passed ? 'var(--ink)' : 'var(--chalk)',
                  color: active ? 'var(--ink)' : passed ? 'var(--chalk)' : 'var(--n700)',
                  fontWeight: active ? 700 : 500,
                  cursor: 'pointer',
                }}
              >
                0{idx + 1}. {st.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* 62% / 38% Application Dossier Workbench */}
      <ResizableSplitPane
        storageKey="pipeline_detail_split"
        defaultLeftPct={62}
        minLeftPx={440}
        minRightPx={340}
        left={
          <div style={{ padding: '26px 32px 64px' }}>
            {/* 1. Frozen Immutable Sent Artifacts */}
            <section className="t-card" style={{ padding: '22px 24px', marginBottom: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 14 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <TailoredIcon name="lock" size={15} color="var(--dye)" />
                    <span className="t-eyebrow">Immutable Sent Artifact Snapshot</span>
                  </div>
                  <h2 style={{ fontSize: 21, marginTop: 6 }}>{frozenFile}</h2>
                  <div className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)', marginTop: 3 }}>
                    Exact file hash archived at dispatch · Fit at send: {fitEval.overallScore}%
                  </div>
                </div>
                <FitDial score={fitEval.overallScore} size={64} />
              </div>

              <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="t-btn t-btn--ink t-btn--sm"
                  onClick={() => {
                    if (matchingDoc) {
                      CvFitAPI.getCvFit(matchingDoc.doc_id).then((d) => {
                        if (d) CvFitAPI.downloadArtifact(d, 'pdf');
                      });
                    }
                    pushToast('Downloading exact sent PDF snapshot.');
                  }}
                >
                  <TailoredIcon name="download" size={13} color="var(--chalk)" />
                  Download Frozen PDF
                </button>
                <button
                  type="button"
                  className="t-btn t-btn--outline t-btn--sm"
                  onClick={() =>
                    matchingDoc ? forkSavedDoc(matchingDoc.doc_id) : openJobInStudio(item.job, { skipCreditCheck: true })
                  }
                >
                  Fork Unlocked Copy (0 cr)
                </button>
              </div>
            </section>

            {/* 2. Communication & Follow-Up Timeline */}
            <section className="t-card" style={{ padding: '22px 24px', marginBottom: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <div>
                  <span className="t-eyebrow">Outreach Ledger</span>
                  <h2 style={{ fontSize: 20, marginTop: 3 }}>Communication &amp; Follow-Up Timeline</h2>
                </div>
                <button type="button" className="t-btn t-btn--primary t-btn--sm" onClick={draftFollowUpNudge}>
                  <TailoredIcon name="send" size={13} color="var(--ink)" />
                  Draft 7-Day Follow-Up
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div className="t-alert">
                  <div className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                    TO: {item.recruiter_email}
                  </div>
                  <div style={{ fontWeight: 600, fontSize: 14, marginTop: 2 }}>
                    Application Package Prepared ({role})
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--n700)', marginTop: 2 }}>
                    Includes tailored 1-page ATS PDF + direct response cover note.
                  </div>
                </div>
              </div>
            </section>

            {/* 3. Interview Prep & Rounds Matrix */}
            <section className="t-card" style={{ padding: '22px 24px' }}>
              <span className="t-eyebrow">Interview Prep · Grounded in Your 9-Pillar Gaps</span>
              <h2 style={{ fontSize: 20, marginTop: 4, marginBottom: 12 }}>Rounds &amp; Defense Notes</h2>

              {fitEval.missingSkills.length > 0 && (
                <div className="t-alert t-alert--warn" style={{ marginBottom: 14 }}>
                  <div className="t-label" style={{ marginBottom: 4 }}>Likely Technical Probes Based on JD Gaps</div>
                  <div style={{ fontSize: 13.5 }}>
                    Be ready to bridge <strong>{fitEval.missingSkills.join(', ')}</strong> using adjacent examples from your production FastAPI / Python architecture.
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 16 }}>
                {(extras.rounds || []).map((r) => (
                  <div key={r.id} style={{ border: '1px solid var(--n300)', background: 'var(--chalk)', padding: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <strong style={{ fontSize: 14 }}>{r.round}</strong>
                      <span className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                        {r.date} · {r.interviewer}
                      </span>
                    </div>
                    <div style={{ fontSize: 13.5, color: 'var(--n700)' }}>{r.notes}</div>
                  </div>
                ))}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 8 }}>
                <input
                  className="t-input"
                  placeholder="Round name (e.g., System Design)"
                  value={newRoundName}
                  onChange={(e) => setNewRoundName(e.target.value)}
                />
                <input
                  className="t-input"
                  placeholder="Key talking point or questions..."
                  value={newRoundNotes}
                  onChange={(e) => setNewRoundNotes(e.target.value)}
                />
                <button type="button" className="t-btn t-btn--ink t-btn--sm" onClick={handleAddRound}>
                  Add Round
                </button>
              </div>
            </section>
          </div>
        }
        right={
          <div style={{ padding: '24px 26px 64px', background: 'var(--paper)', minHeight: '100%' }}>
            <span className="t-eyebrow">Contact &amp; Schedule Inspector</span>
            <h2 style={{ fontSize: 22, marginTop: 4, marginBottom: 16 }}>Recruiter &amp; Logistics</h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>Recruiter Name</label>
                <input
                  className="t-input"
                  placeholder="Hiring Manager / Talent Partner"
                  value={recruiterName}
                  onChange={(e) => setRecruiterName(e.target.value)}
                />
              </div>

              <div>
                <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>Recruiter Direct Email</label>
                <input
                  className="t-input"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                />
              </div>

              <div>
                <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>Target Follow-Up Date</label>
                <input
                  className="t-input"
                  type="date"
                  value={followUpDate}
                  onChange={(e) => setFollowUpDate(e.target.value)}
                />
              </div>

              <div>
                <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>Interview Date</label>
                <input
                  className="t-input"
                  type="date"
                  value={interviewDate}
                  onChange={(e) => setInterviewDate(e.target.value)}
                />
              </div>

              <div>
                <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>Compensation / Logistics Notes</label>
                <textarea
                  className="t-textarea"
                  rows={3}
                  placeholder="Notice period, hybrid expectations, range discussed..."
                  value={compNotes}
                  onChange={(e) => setCompNotes(e.target.value)}
                />
              </div>

              <button type="button" className="t-btn t-btn--primary" onClick={saveInspector}>
                Save Dossier Changes
              </button>
            </div>

            <div style={{ borderTop: '1px solid var(--n300)', marginTop: 22, paddingTop: 16, display: 'flex', justifyContent: 'space-between' }}>
              <button
                type="button"
                className="t-btn t-btn--outline t-btn--sm"
                onClick={() => navigateTo('/cover-letters')}
              >
                Open Cover Letter
              </button>
              <button
                type="button"
                className="t-btn t-btn--alarm t-btn--sm"
                onClick={() => {
                  removeFromPipeline(item.id);
                  navigateTo('/pipeline');
                }}
              >
                Remove
              </button>
            </div>
          </div>
        }
      />
    </div>
  );
};
