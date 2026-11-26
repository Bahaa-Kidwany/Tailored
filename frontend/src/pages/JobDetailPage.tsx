import React, { useState, useMemo } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { ResizableSplitPane } from '../components/common/ResizableSplitPane';
import { EmptyState, FitDial, MeasureRulerBar } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';
import { SAMPLE_PROFILE } from '../services/profileApi';
import { evaluateAllPersonas, computeNinePillarFit } from '../utils/fitEngine';
import { cleanCompanyName, cleanTargetJobTitle } from '../services/cvFitApi';
import { hasDirectRecruiterEmail } from '../services/pipelineStorage';

export const JobDetailPage: React.FC = () => {
  const {
    currentPath,
    radarJobs,
    interestList,
    currentProfile,
    tailoredDocs,
    openJobInStudio,
    openDocInStudio,
    addToInterest,
    addToPipeline,
    hideJob,
    navigateTo,
    isJobUnlocked,
    pushToast,
  } = useWorkspace();

  const idMatch = currentPath.match(/^\/jobs\/(\d+)/);
  const jobId = idMatch ? Number(idMatch[1]) : 101;
  const allKnownJobs = [...radarJobs, ...interestList];
  const job = allKnownJobs.find((j) => j.id === jobId) || radarJobs[0];

  const profile = currentProfile?.profile || SAMPLE_PROFILE;
  const { all, best } = useMemo(() => evaluateAllPersonas(job, profile), [job, profile]);
  const [selectedPersonaId, setSelectedPersonaId] = useState<string>(best.personaId);
  const [playbookChecks, setPlaybookChecks] = useState<Record<string, boolean>>({});
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiAnswer, setAiAnswer] = useState<string | null>(null);

  if (!job) {
    return (
      <EmptyState
        icon="job"
        headline="Role not found in Radar or Interest"
        subtext="The link may have expired or been removed."
        ctaLabel="Return to Job Radar"
        onCta={() => navigateTo('/radar')}
      />
    );
  }

  const selectedEval =
    computeNinePillarFit(
      job,
      profile.career_personas.find((p) => p.persona_id === selectedPersonaId) || profile.career_personas[0],
      profile
    ) || best;

  const existingDoc = tailoredDocs.find((d) => d.job_id === job.id);
  const unlockedCv = isJobUnlocked(job.id, 'cv');
  const isDirectChannel = hasDirectRecruiterEmail(job);

  const askInlineFitAi = () => {
    if (!aiQuestion.trim()) return;
    const missing = selectedEval.missingSkills.slice(0, 3).join(', ') || 'none detected';
    const matched = selectedEval.matchedSkills.slice(0, 4).join(', ');
    setAiAnswer(
      `Grounded check against ${selectedEval.personaTitle}: You directly match ${matched}. The gap (${missing}) can be bridged truthfully in CV Studio by emphasizing production architecture and deployment rigor from your Swvl/Noor work — no unverified skills needed. (0 credits used)`
    );
    setAiQuestion('');
  };

  const togglePlaybook = (skill: string) => {
    setPlaybookChecks((prev) => ({ ...prev, [skill]: !prev[skill] }));
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <ResizableSplitPane
        storageKey="job_detail_split"
        defaultLeftPct={58}
        minLeftPx={420}
        minRightPx={360}
        left={
          <div style={{ padding: '28px 32px 64px' }}>
            <button
              type="button"
              className="t-btn t-btn--ghost t-btn--sm"
              onClick={() => navigateTo('/radar')}
              style={{ marginBottom: 14, paddingLeft: 0 }}
            >
              <TailoredIcon name="back" size={14} />
              Back to Job Radar
            </button>

            {/* Role Header */}
            <div className="t-card" style={{ padding: '24px 26px', marginBottom: 20 }}>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
                <span className="t-chip t-chip--notch">{job.source_type || 'radar'}</span>
                <span className="t-chip">{job.location_type || 'Hybrid'}</span>
                {isDirectChannel ? (
                  <span className="t-chip t-chip--strong">Recruiter Contact Present</span>
                ) : (
                  <span className="t-chip t-chip--mist">External Portal</span>
                )}
              </div>

              <h1 style={{ fontSize: 30, margin: 0 }}>{cleanTargetJobTitle(job.title)}</h1>
              <div className="t-mono" style={{ fontSize: 13, color: 'var(--n700)', marginTop: 6 }}>
                {cleanCompanyName(job.company_name)} · {job.location}
              </div>

              <div style={{ display: 'flex', gap: 8, marginTop: 18, flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="t-btn t-btn--primary"
                  onClick={() => openJobInStudio(job)}
                >
                  {unlockedCv || existingDoc ? 'Open Tailored CV (0 cr)' : 'Tailor CV in Studio (1 cr)'}
                </button>
                <button
                  type="button"
                  className="t-btn t-btn--outline"
                  onClick={() => {
                    addToInterest(job);
                    pushToast('Saved to Shortlist.');
                  }}
                >
                  <TailoredIcon name="save" size={14} />
                  Save to Shortlist
                </button>
                <button
                  type="button"
                  className="t-btn t-btn--subtle"
                  onClick={() => addToPipeline(job, 'saved')}
                >
                  Track in Pipeline
                </button>
                {job.url && (
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noreferrer"
                    className="t-btn t-btn--ghost t-btn--sm"
                  >
                    Original Posting
                    <TailoredIcon name="external" size={13} />
                  </a>
                )}
              </div>
            </div>

            {/* Multi-Persona Fit Comparison Matrix */}
            <div className="t-card" style={{ padding: '20px 24px', marginBottom: 20 }}>
              <span className="t-eyebrow">Parallel Persona Scoring · 0 Credits</span>
              <h2 style={{ fontSize: 20, marginTop: 4, marginBottom: 12 }}>
                Multi-Persona Fit Comparison Matrix
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {all.map((pEval) => {
                  const isSel = pEval.personaId === selectedEval.personaId;
                  const isBest = pEval.personaId === best.personaId;
                  return (
                    <button
                      key={pEval.personaId}
                      type="button"
                      onClick={() => setSelectedPersonaId(pEval.personaId)}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '12px 14px',
                        background: isSel ? 'var(--chalk)' : 'var(--paper)',
                        border: `1.5px solid ${isSel ? 'var(--ink)' : 'var(--n300)'}`,
                        cursor: 'pointer',
                        textAlign: 'left',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontWeight: 600, fontSize: 14.5 }}>{pEval.personaTitle}</span>
                          {isBest && <span className="t-chip t-chip--strong">Best Angle</span>}
                        </div>
                        <div className="t-mono" style={{ fontSize: 11, color: 'var(--n500)', marginTop: 3 }}>
                          {pEval.whyMatched}
                        </div>
                      </div>
                      <div style={{ fontFamily: 'var(--font-voice)', fontSize: 24, fontWeight: 600 }}>
                        {pEval.overallScore}%
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Structured Role Description & Responsibilities */}
            <div className="t-card" style={{ padding: '22px 26px', marginBottom: 20 }}>
              <span className="t-eyebrow">Normalized Role Brief</span>
              <h2 style={{ fontSize: 20, marginTop: 4, marginBottom: 12 }}>Role Summary & Responsibilities</h2>
              <p style={{ fontSize: 14.5, lineHeight: 1.6, color: 'var(--n700)', marginBottom: 16 }}>
                {job.raw_description}
              </p>
              {job.responsibilities && job.responsibilities.length > 0 && (
                <ul className="t-bullets" style={{ fontSize: 14.5 }}>
                  {job.responsibilities.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              )}
            </div>

            {/* Existing Artifacts + Ignore */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              {existingDoc ? (
                <button
                  type="button"
                  className="t-btn t-btn--outline t-btn--sm"
                  onClick={() => openDocInStudio(existingDoc.doc_id)}
                >
                  Open Existing Artifact ({existingDoc.fit_score ?? best.overallScore}% Fit · 0 cr)
                </button>
              ) : (
                <span className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)' }}>
                  No saved tailored document yet for this posting.
                </span>
              )}
              <button
                type="button"
                className="t-btn t-btn--ghost t-btn--sm"
                onClick={() => {
                  hideJob(job.id);
                  navigateTo('/radar');
                }}
              >
                <TailoredIcon name="hide" size={14} />
                Hide Role
              </button>
            </div>
          </div>
        }
        right={
          <div style={{ padding: '26px 26px 64px', background: 'var(--paper)', minHeight: '100%' }}>
            {/* Prominent FitDial + Verdict */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 18, paddingBottom: 16, borderBottom: '1.5px solid var(--ink)' }}>
              <FitDial score={selectedEval.overallScore} size={92} />
              <div>
                <span className="t-eyebrow">9-Pillar Audit · {selectedEval.personaTitle}</span>
                <div style={{ fontSize: 18, fontWeight: 600, marginTop: 4 }}>
                  {selectedEval.overallScore >= 75
                    ? 'Strong Target Match'
                    : selectedEval.overallScore >= 50
                      ? 'Bridgeable Partial Fit'
                      : 'Pivot Stretch Role'}
                </div>
                <div className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)', marginTop: 4 }}>
                  {selectedEval.matchedSkills.length} matched · {selectedEval.missingSkills.length} gaps
                </div>
              </div>
            </div>

            {/* Brand Book 9-Pillar Measuring-Tape Bars */}
            <div style={{ marginTop: 18 }}>
              <div className="t-label" style={{ marginBottom: 10 }}>9-Pillar Breakdown</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
                {selectedEval.pillars.map((pil) => (
                  <div key={pil.key}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 12.5, fontWeight: 600 }}>
                        {pil.label}{' '}
                        <span className="t-mono" style={{ fontSize: 10.5, color: 'var(--n500)' }}>
                          ({pil.weight}%)
                        </span>
                      </span>
                      <span className="t-mono" style={{ fontSize: 12, fontWeight: 600 }}>
                        {pil.score}
                      </span>
                    </div>
                    <MeasureRulerBar
                      value={pil.score}
                      width={340}
                      accent={
                        pil.score >= 80 ? 'var(--green)' : pil.score >= 55 ? 'var(--amber)' : 'var(--alarm)'
                      }
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Matched vs Missing Chips */}
            <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--n300)' }}>
              <div className="t-label" style={{ marginBottom: 8 }}>Keyword Signals</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {selectedEval.matchedSkills.map((sk) => (
                  <span key={sk} className="t-chip t-chip--strong t-chip--notch">
                    {sk}
                  </span>
                ))}
                {selectedEval.missingSkills.map((sk) => (
                  <span key={sk} className="t-chip t-chip--partial">
                    Gap: {sk}
                  </span>
                ))}
              </div>
            </div>

            {/* Constructive Tailoring Playbook */}
            <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--n300)' }}>
              <div className="t-label" style={{ marginBottom: 8 }}>Constructive Tailoring Playbook</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {selectedEval.missingSkills.length > 0 ? (
                  selectedEval.missingSkills.map((sk) => (
                    <label
                      key={sk}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        fontSize: 13.5,
                        cursor: 'pointer',
                        padding: '7px 10px',
                        background: 'var(--chalk)',
                        border: '1px solid var(--n300)',
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={!!playbookChecks[sk]}
                        onChange={() => togglePlaybook(sk)}
                      />
                      Highlight truthful adjacency to <strong>{sk}</strong>
                    </label>
                  ))
                ) : (
                  <div className="t-alert t-alert--success">
                    All core job requirements already present in your selected persona. Focus Studio on measurable impact numbers.
                  </div>
                )}
              </div>
            </div>

            {/* Inline Ask AI About Fit Mini-Drawer (0 Credits) */}
            <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--n300)' }}>
              <div className="t-label" style={{ marginBottom: 6 }}>Ask AI About Fit (0 cr)</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <input
                  className="t-input"
                  placeholder="Can I frame my Noor experience for this role?"
                  value={aiQuestion}
                  onChange={(e) => setAiQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && askInlineFitAi()}
                />
                <button type="button" className="t-btn t-btn--ink t-btn--sm" onClick={askInlineFitAi}>
                  Ask
                </button>
              </div>
              {aiAnswer && (
                <div className="t-alert" style={{ marginTop: 10, fontSize: 13.5 }}>
                  {aiAnswer}
                </div>
              )}
            </div>
          </div>
        }
      />
    </div>
  );
};
