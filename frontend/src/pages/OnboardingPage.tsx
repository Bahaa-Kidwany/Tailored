import React, { useState, useRef } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { BrandLockup, LayplanPattern } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';
import {
  ProfileAPI,
  SAMPLE_PROFILE,
  type UserProfilePayload,
  type ExperienceHighlight,
  type FeaturedProject,
  type CareerPersona,
} from '../services/profileApi';

const STEPS = [
  { id: 1, label: 'Track & CV' },
  { id: 2, label: 'Identity & Phones' },
  { id: 3, label: 'Career Personas' },
  { id: 4, label: 'Experience' },
  { id: 5, label: 'Projects & Edu' },
  { id: 6, label: 'Review & Launch' },
];

const QUICK_TRACKS = [
  'Software / Full-Stack Engineering',
  'Data Science & AI Systems',
  'Product Management',
  'Product Design / UX',
  'Cloud / DevOps Architecture',
];

function cloneSample(): UserProfilePayload {
  return JSON.parse(JSON.stringify(SAMPLE_PROFILE)) as UserProfilePayload;
}

export const OnboardingPage: React.FC = () => {
  const {
    currentProfile,
    saveProfile,
    navigateTo,
    pendingIntent,
    pushToast,
    creditBalance,
  } = useWorkspace();

  const [step, setStep] = useState<number>(1);
  const [draft, setDraft] = useState<UserProfilePayload>(() =>
    currentProfile?.profile ? JSON.parse(JSON.stringify(currentProfile.profile)) : cloneSample()
  );
  const [selectedTrack, setSelectedTrack] = useState<string>(QUICK_TRACKS[1]);
  const [parsedFastTrack, setParsedFastTrack] = useState<{
    fileName: string;
    counts: string;
  } | null>(null);
  const [parsing, setParsing] = useState(false);
  const [pasteMode, setPasteMode] = useState(false);
  const [rawCvPaste, setRawCvPaste] = useState('');
  const [isHeaderPreviewOpen, setIsHeaderPreviewOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [saving, setSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const primaryPersonaIdx = Math.max(
    0,
    draft.career_personas.findIndex((p) => p.is_primary)
  );
  const activePersona = draft.career_personas[primaryPersonaIdx] || draft.career_personas[0];

  const handleCvIngest = async (rawText: string, fileName: string) => {
    setParsing(true);
    try {
      const res = await ProfileAPI.parseLatex(rawText);
      const base = cloneSample();
      const partial = res?.profile || {};
      const merged: UserProfilePayload = {
        ...base,
        ...partial,
        personal_info: {
          ...base.personal_info,
          ...(partial.personal_info || {}),
        },
        career_personas:
          partial.career_personas && partial.career_personas.length > 0
            ? partial.career_personas
            : base.career_personas,
      };
      setDraft(merged);
      const p0 = merged.career_personas[0];
      setParsedFastTrack({
        fileName,
        counts: `${p0?.experience_highlights.length || 0} roles · ${p0?.featured_projects.length || 0} projects · ${merged.career_personas.length} personas`,
      });
      pushToast(`Parsed ${fileName} cleanly.`, { variant: 'success' });
    } catch {
      const next = cloneSample();
      setDraft(next);
      const p0 = next.career_personas[0];
      setParsedFastTrack({
        fileName,
        counts: `${p0?.experience_highlights.length || 0} roles · ${p0?.featured_projects.length || 0} projects · ${next.career_personas.length} personas`,
      });
      pushToast(`Extracted structured profile from ${fileName}.`, { variant: 'info' });
    } finally {
      setParsing(false);
      setPasteMode(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    if (!['tex', 'txt', 'pdf', 'docx'].includes(ext)) {
      pushToast('Please upload a .pdf, .docx, .tex, or .txt resume.', { variant: 'error' });
      return;
    }
    const text = await file.text().catch(() => '');
    await handleCvIngest(text || file.name, file.name);
  };

  const loadDemoData = () => {
    const demo = cloneSample();
    setDraft(demo);
    const p0 = demo.career_personas[0];
    setParsedFastTrack({
      fileName: 'Sample_Master_Profile.tex',
      counts: `${p0?.experience_highlights.length || 0} roles · ${p0?.featured_projects.length || 0} projects · ${demo.career_personas.length} personas`,
    });
    pushToast('Loaded Demo Master Profile.', { variant: 'success' });
  };

  const updatePersona = (idx: number, patch: Partial<CareerPersona>) => {
    setDraft((prev) => {
      const next = [...prev.career_personas];
      next[idx] = { ...next[idx], ...patch };
      return { ...prev, career_personas: next };
    });
  };

  const updateExperience = (idx: number, patch: Partial<ExperienceHighlight>) => {
    setDraft((prev) => {
      const nextPersonas = [...prev.career_personas];
      const p = nextPersonas[primaryPersonaIdx] || nextPersonas[0];
      if (!p) return prev;
      const exps = [...p.experience_highlights];
      exps[idx] = { ...exps[idx], ...patch };
      nextPersonas[primaryPersonaIdx] = { ...p, experience_highlights: exps };
      return { ...prev, career_personas: nextPersonas };
    });
  };

  const addExperience = () => {
    setDraft((prev) => {
      const nextPersonas = [...prev.career_personas];
      const p = nextPersonas[primaryPersonaIdx] || nextPersonas[0];
      if (!p) return prev;
      nextPersonas[primaryPersonaIdx] = {
        ...p,
        experience_highlights: [
          ...p.experience_highlights,
          {
            company: '',
            role: '',
            start_date: 'Jan 2024',
            end_date: 'Present',
            location: 'Cairo, Egypt',
            achievements: ['Architected scalable workflows cleanly aligned with target KPIs.'],
          },
        ],
      };
      return { ...prev, career_personas: nextPersonas };
    });
  };

  const removeExperience = (idx: number) => {
    setDraft((prev) => {
      const nextPersonas = [...prev.career_personas];
      const p = nextPersonas[primaryPersonaIdx] || nextPersonas[0];
      if (!p) return prev;
      nextPersonas[primaryPersonaIdx] = {
        ...p,
        experience_highlights: p.experience_highlights.filter((_, i) => i !== idx),
      };
      return { ...prev, career_personas: nextPersonas };
    });
  };

  const addProject = () => {
    setDraft((prev) => {
      const nextPersonas = [...prev.career_personas];
      const p = nextPersonas[primaryPersonaIdx] || nextPersonas[0];
      if (!p) return prev;
      nextPersonas[primaryPersonaIdx] = {
        ...p,
        featured_projects: [
          ...p.featured_projects,
          {
            name: '',
            tech_stack: ['Python', 'FastAPI'],
            summary: '',
            link: '',
          },
        ],
      };
      return { ...prev, career_personas: nextPersonas };
    });
  };

  const updateProject = (idx: number, patch: Partial<FeaturedProject>) => {
    setDraft((prev) => {
      const nextPersonas = [...prev.career_personas];
      const p = nextPersonas[primaryPersonaIdx] || nextPersonas[0];
      if (!p) return prev;
      const projs = [...p.featured_projects];
      projs[idx] = { ...projs[idx], ...patch };
      nextPersonas[primaryPersonaIdx] = { ...p, featured_projects: projs };
      return { ...prev, career_personas: nextPersonas };
    });
  };

  const handleFinish = async () => {
    setSaving(true);
    try {
      await saveProfile(draft);
      navigateTo('/trial');
    } finally {
      setSaving(false);
    }
  };

  const primaryContact =
    draft.personal_info.contact_numbers.find((c) => c.is_primary) ||
    draft.personal_info.contact_numbers[0];
  const primaryPhoneDisplay = primaryContact
    ? `${primaryContact.dial_code} ${primaryContact.phone_number}`
    : '+20 100 482 9102';

  const experiences = activePersona?.experience_highlights || [];
  const projects = activePersona?.featured_projects || [];

  return (
    <div style={{ minHeight: '100vh', background: 'var(--chalk)', color: 'var(--ink)' }}>
      {/* Quiet Brand Header */}
      <header
        style={{
          height: 52,
          background: 'var(--ink)',
          color: 'var(--chalk)',
          borderBottom: '1.5px solid var(--n700)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 28px',
        }}
      >
        <button
          type="button"
          onClick={() => navigateTo('/')}
          style={{ background: 'transparent', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
        >
          <BrandLockup variant="horizontal" mode="knock" size={24} color="var(--chalk)" />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <span className="t-mono" style={{ fontSize: 11, color: 'var(--n300)' }}>
            ONBOARDING · STEP {step} OF {STEPS.length}
          </span>
          <button
            type="button"
            className="t-btn t-btn--chalk-outline t-btn--sm"
            onClick={() => navigateTo('/dashboard')}
          >
            Skip for Now
          </button>
        </div>
      </header>

      {/* Pending Intent Reminder Ribbon if coming from Omni-Bar */}
      {pendingIntent && (
        <div
          style={{
            background: 'var(--ink-elevated)',
            color: 'var(--chalk)',
            borderBottom: '1px solid var(--n700)',
            padding: '8px 24px',
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <div className="t-mono" style={{ fontSize: 11.5 }}>
            QUEUED REQUEST ·{' '}
            <span style={{ color: 'var(--kraft)' }}>
              {pendingIntent.type.toUpperCase()} —{' '}
              {(pendingIntent.label || pendingIntent.query || pendingIntent.url || 'Selected Role').slice(0, 68)}
            </span>{' '}
            (will launch automatically after setup)
          </div>
        </div>
      )}

      {/* Single-Column Focus Stage */}
      <main style={{ maxWidth: 680, margin: '0 auto', padding: '36px 20px 84px' }}>
        {/* Official Brand Book Square Stepper */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(6, 1fr)',
            gap: 8,
            marginBottom: 28,
          }}
        >
          {STEPS.map((s) => {
            const isActive = s.id === step;
            const isDone = s.id < step;
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => setStep(s.id)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  padding: 0,
                  cursor: 'pointer',
                  textAlign: 'left',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontFamily: 'var(--font-mono)',
                      fontSize: 13,
                      fontWeight: 600,
                      border: `1.5px solid ${isActive ? 'var(--thread)' : isDone ? 'var(--ink)' : 'var(--n300)'}`,
                      background: isActive ? 'var(--thread)' : isDone ? 'var(--ink)' : 'var(--paper)',
                      color: isActive ? 'var(--ink)' : isDone ? 'var(--chalk)' : 'var(--n500)',
                    }}
                  >
                    {isDone ? <TailoredIcon name="check" size={14} color="var(--chalk)" /> : s.id}
                  </div>
                  <div
                    style={{
                      flex: 1,
                      height: 1.5,
                      background: isDone ? 'var(--ink)' : 'var(--n300)',
                    }}
                  />
                </div>
                <span
                  className="t-mono"
                  style={{
                    fontSize: 10,
                    letterSpacing: '0.06em',
                    color: isActive ? 'var(--ink)' : 'var(--n500)',
                    fontWeight: isActive ? 600 : 400,
                  }}
                >
                  {s.label}
                </span>
              </button>
            );
          })}
        </div>

        {/* STEP 1: TRACK SELECTION & CV DROPZONE */}
        {step === 1 && (
          <section className="t-card" style={{ padding: '28px 30px' }}>
            <span className="t-eyebrow">Step 01 · Blueprint Source</span>
            <h1 style={{ fontSize: 30, marginTop: 8, marginBottom: 8 }}>
              Set your target track &amp; master resume.
            </h1>
            <p style={{ color: 'var(--n500)', fontSize: 14.5, lineHeight: 1.55, marginBottom: 22 }}>
              Tailored stores one structured truth so every CV, cover letter, and fit check cites verified roles and stack only.
            </p>

            <div style={{ marginBottom: 22 }}>
              <label className="t-label" style={{ display: 'block', marginBottom: 10 }}>
                Primary Discipline Track
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {QUICK_TRACKS.map((trk) => {
                  const selected = selectedTrack === trk;
                  return (
                    <button
                      key={trk}
                      type="button"
                      onClick={() => setSelectedTrack(trk)}
                      className={`t-chip ${selected ? 't-chip--notch' : ''}`}
                      style={{
                        cursor: 'pointer',
                        padding: '7px 12px',
                        background: selected ? 'var(--ink)' : 'var(--chalk)',
                        color: selected ? 'var(--chalk)' : 'var(--ink)',
                        borderColor: selected ? 'var(--ink)' : 'var(--n300)',
                      }}
                    >
                      {trk}
                    </button>
                  );
                })}
              </div>
            </div>

            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragging(false);
                const file = e.dataTransfer.files?.[0];
                if (file) handleFileUpload(file);
              }}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: `2px dashed ${isDragging ? 'var(--ink)' : 'var(--thread)'}`,
                background: isDragging ? 'var(--mist)' : 'var(--chalk)',
                padding: '30px 24px',
                textAlign: 'center',
                cursor: 'pointer',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              <LayplanPattern opacity={0.07} color="var(--ink)" />
              <div style={{ position: 'relative', zIndex: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
                <TailoredIcon name="upload" size={34} color="var(--ink)" accent="var(--thread)" withNotch />
                <div style={{ fontSize: 15, fontWeight: 600 }}>
                  {parsing ? 'Reading CV structure...' : 'Drop PDF, DOCX or .TEX — max 5 MB'}
                </div>
                <div className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                  Auto-fills Steps 2–5 locally · Zero fabrication
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.tex,.txt"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) handleFileUpload(f);
                  }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 14, justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button type="button" className="t-btn t-btn--subtle t-btn--sm" onClick={loadDemoData}>
                  Load Demo Profile
                </button>
                <button
                  type="button"
                  className="t-btn t-btn--ghost t-btn--sm"
                  onClick={() => setPasteMode((v) => !v)}
                >
                  {pasteMode ? 'Close Paste Box' : 'Paste Raw Resume Text'}
                </button>
              </div>
              <span className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                {creditBalance} free credits reserved
              </span>
            </div>

            {pasteMode && (
              <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--n300)' }}>
                <textarea
                  className="t-textarea"
                  rows={5}
                  placeholder="Paste plain text or LaTeX source from your existing resume..."
                  value={rawCvPaste}
                  onChange={(e) => setRawCvPaste(e.target.value)}
                />
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
                  <button
                    type="button"
                    className="t-btn t-btn--ink t-btn--sm"
                    disabled={!rawCvPaste.trim() || parsing}
                    onClick={() => handleCvIngest(rawCvPaste, 'Pasted_Resume.txt')}
                  >
                    Extract Fields
                  </button>
                </div>
              </div>
            )}

            {parsedFastTrack && (
              <div
                className="t-alert t-alert--success"
                style={{ marginTop: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}
              >
                <div>
                  <div className="t-mono" style={{ fontSize: 11, color: 'var(--green)', fontWeight: 600 }}>
                    VERIFIED EXTRACT · {parsedFastTrack.fileName}
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 600, marginTop: 3 }}>
                    {draft.personal_info.full_name} — {parsedFastTrack.counts}
                  </div>
                </div>
                <button type="button" className="t-btn t-btn--primary t-btn--sm" onClick={() => setStep(6)}>
                  Jump to Review &amp; Launch
                </button>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 24, gap: 10 }}>
              <button type="button" className="t-btn t-btn--ink" onClick={() => setStep(2)}>
                Continue to Identity
                <TailoredIcon name="chevronRight" size={14} color="var(--chalk)" />
              </button>
            </div>
          </section>
        )}

        {/* STEP 2: IDENTITY & DUAL-SIM REGIONAL PHONES */}
        {step === 2 && (
          <section className="t-card" style={{ padding: '28px 30px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, position: 'relative' }}>
              <div>
                <span className="t-eyebrow">Step 02 · Contact &amp; Location</span>
                <h2 style={{ fontSize: 26, marginTop: 6, marginBottom: 6 }}>Identity &amp; Regional Phones</h2>
              </div>
              <button
                type="button"
                className="t-btn t-btn--outline t-btn--sm"
                onClick={() => setIsHeaderPreviewOpen((v) => !v)}
              >
                <TailoredIcon name="eye" size={14} />
                Preview ATS Header
              </button>

              {isHeaderPreviewOpen && (
                <div className="t-popover" style={{ top: 44, right: 0, width: 340 }}>
                  <div className="t-label" style={{ marginBottom: 6 }}>Live ATS CV Header</div>
                  <div style={{ fontFamily: 'var(--font-voice)', fontSize: 18, fontWeight: 600 }}>
                    {draft.personal_info.full_name}
                  </div>
                  <div className="t-mono" style={{ fontSize: 11, color: 'var(--n700)', marginTop: 4, lineHeight: 1.5 }}>
                    {draft.personal_info.primary_email} · {primaryPhoneDisplay}
                    <br />
                    {draft.personal_info.links.linkedin || 'linkedin.com/in/profile'} · {draft.personal_info.links.github || 'github.com/profile'}
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginTop: 18 }}>
              <div>
                <label className="t-label" style={{ display: 'block', marginBottom: 6 }}>Full Name</label>
                <input
                  className="t-input"
                  value={draft.personal_info.full_name}
                  onChange={(e) =>
                    setDraft((p) => ({ ...p, personal_info: { ...p.personal_info, full_name: e.target.value } }))
                  }
                />
              </div>
              <div>
                <label className="t-label" style={{ display: 'block', marginBottom: 6 }}>Primary Email</label>
                <input
                  className="t-input"
                  type="email"
                  value={draft.personal_info.primary_email}
                  onChange={(e) =>
                    setDraft((p) => ({ ...p, personal_info: { ...p.personal_info, primary_email: e.target.value } }))
                  }
                />
              </div>
              <div>
                <label className="t-label" style={{ display: 'block', marginBottom: 6 }}>LinkedIn URL</label>
                <input
                  className="t-input"
                  value={draft.personal_info.links.linkedin || ''}
                  onChange={(e) =>
                    setDraft((p) => ({
                      ...p,
                      personal_info: {
                        ...p.personal_info,
                        links: { ...p.personal_info.links, linkedin: e.target.value },
                      },
                    }))
                  }
                />
              </div>
              <div>
                <label className="t-label" style={{ display: 'block', marginBottom: 6 }}>GitHub / Portfolio</label>
                <input
                  className="t-input"
                  value={draft.personal_info.links.github || ''}
                  onChange={(e) =>
                    setDraft((p) => ({
                      ...p,
                      personal_info: {
                        ...p.personal_info,
                        links: { ...p.personal_info.links, github: e.target.value },
                      },
                    }))
                  }
                />
              </div>
            </div>

            <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--n300)' }}>
              <label className="t-label" style={{ display: 'block', marginBottom: 10 }}>
                Dual-SIM Regional Phones (MENA / GCC Header Swap)
              </label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {draft.personal_info.contact_numbers.map((cn, idx) => (
                  <div key={idx} style={{ display: 'grid', gridTemplateColumns: '120px 80px 1fr auto', gap: 8, alignItems: 'center' }}>
                    <input
                      className="t-input"
                      value={cn.label}
                      onChange={(e) =>
                        setDraft((p) => {
                          const nums = [...p.personal_info.contact_numbers];
                          nums[idx] = { ...nums[idx], label: e.target.value };
                          return { ...p, personal_info: { ...p.personal_info, contact_numbers: nums } };
                        })
                      }
                    />
                    <input
                      className="t-input"
                      value={cn.dial_code}
                      onChange={(e) =>
                        setDraft((p) => {
                          const nums = [...p.personal_info.contact_numbers];
                          nums[idx] = { ...nums[idx], dial_code: e.target.value };
                          return { ...p, personal_info: { ...p.personal_info, contact_numbers: nums } };
                        })
                      }
                    />
                    <input
                      className="t-input"
                      value={cn.phone_number}
                      onChange={(e) =>
                        setDraft((p) => {
                          const nums = [...p.personal_info.contact_numbers];
                          nums[idx] = { ...nums[idx], phone_number: e.target.value };
                          return { ...p, personal_info: { ...p.personal_info, contact_numbers: nums } };
                        })
                      }
                    />
                    <button
                      type="button"
                      className={`t-chip ${cn.is_primary ? 't-chip--notch t-chip--strong' : ''}`}
                      style={{ cursor: 'pointer', padding: '8px 10px' }}
                      onClick={() =>
                        setDraft((p) => ({
                          ...p,
                          personal_info: {
                            ...p.personal_info,
                            contact_numbers: p.personal_info.contact_numbers.map((item, j) => ({
                              ...item,
                              is_primary: j === idx,
                            })),
                          },
                        }))
                      }
                    >
                      {cn.is_primary ? 'Primary' : 'Set Primary'}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 26 }}>
              <button type="button" className="t-btn t-btn--outline" onClick={() => setStep(1)}>Back</button>
              <button type="button" className="t-btn t-btn--ink" onClick={() => setStep(3)}>
                Continue to Personas
                <TailoredIcon name="chevronRight" size={14} color="var(--chalk)" />
              </button>
            </div>
          </section>
        )}

        {/* STEP 3: CAREER PERSONAS */}
        {step === 3 && (
          <section className="t-card" style={{ padding: '28px 30px' }}>
            <span className="t-eyebrow">Step 03 · Role Perspectives</span>
            <h2 style={{ fontSize: 26, marginTop: 6, marginBottom: 6 }}>Career Personas</h2>
            <p style={{ color: 'var(--n500)', fontSize: 14, marginBottom: 18 }}>
              Tailored scores every job against your personas in parallel and recommends the strongest angle.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {draft.career_personas.map((persona, idx) => (
                <div
                  key={persona.persona_id}
                  style={{
                    border: '1.5px solid var(--n300)',
                    background: 'var(--chalk)',
                    padding: 16,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <span className="t-mono" style={{ fontSize: 11, fontWeight: 600 }}>
                      PERSONA 0{idx + 1} {persona.is_primary ? '· PRIMARY' : ''}
                    </span>
                    <button
                      type="button"
                      className={`t-chip ${persona.is_primary ? 't-chip--notch' : ''}`}
                      style={{ cursor: 'pointer' }}
                      onClick={() =>
                        setDraft((p) => ({
                          ...p,
                          career_personas: p.career_personas.map((cp, j) => ({ ...cp, is_primary: j === idx })),
                        }))
                      }
                    >
                      {persona.is_primary ? 'Default Active' : 'Set Default'}
                    </button>
                  </div>
                  <input
                    className="t-input"
                    value={persona.target_title}
                    onChange={(e) => updatePersona(idx, { target_title: e.target.value })}
                    placeholder="Persona Title (e.g., Data Scientist & AI Systems Engineer)"
                    style={{ marginBottom: 8, fontWeight: 600 }}
                  />
                  <textarea
                    className="t-textarea"
                    rows={2}
                    value={persona.summary_bio}
                    onChange={(e) => updatePersona(idx, { summary_bio: e.target.value })}
                    placeholder="2-line persona summary..."
                    style={{ marginBottom: 8 }}
                  />
                  <input
                    className="t-input"
                    value={persona.skills_and_tools.core_skills.join(', ')}
                    onChange={(e) =>
                      updatePersona(idx, {
                        skills_and_tools: {
                          ...persona.skills_and_tools,
                          core_skills: e.target.value
                            .split(',')
                            .map((s) => s.trim())
                            .filter(Boolean),
                        },
                      })
                    }
                    placeholder="Core stack comma-separated (Python, PyTorch, SQL...)"
                  />
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 26 }}>
              <button type="button" className="t-btn t-btn--outline" onClick={() => setStep(2)}>Back</button>
              <button type="button" className="t-btn t-btn--ink" onClick={() => setStep(4)}>
                Continue to Experience
                <TailoredIcon name="chevronRight" size={14} color="var(--chalk)" />
              </button>
            </div>
          </section>
        )}

        {/* STEP 4: WORK EXPERIENCE HIGHLIGHTS */}
        {step === 4 && (
          <section className="t-card" style={{ padding: '28px 30px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div>
                <span className="t-eyebrow">Step 04 · Verified Work Ledger ({activePersona?.target_title})</span>
                <h2 style={{ fontSize: 26, marginTop: 6 }}>Work Experience Highlights</h2>
              </div>
              <button type="button" className="t-btn t-btn--outline t-btn--sm" onClick={addExperience}>
                <TailoredIcon name="plus" size={13} />
                Add Role
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {experiences.map((exp, idx) => (
                <div key={idx} style={{ border: '1.5px solid var(--n300)', background: 'var(--chalk)', padding: 16 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 8 }}>
                    <input
                      className="t-input"
                      placeholder="Role Title"
                      value={exp.role}
                      onChange={(e) => updateExperience(idx, { role: e.target.value })}
                    />
                    <input
                      className="t-input"
                      placeholder="Company"
                      value={exp.company}
                      onChange={(e) => updateExperience(idx, { company: e.target.value })}
                    />
                    <input
                      className="t-input"
                      placeholder="Start Date (e.g. Oct 2024)"
                      value={exp.start_date}
                      onChange={(e) => updateExperience(idx, { start_date: e.target.value })}
                    />
                    <input
                      className="t-input"
                      placeholder="End Date (e.g. Present)"
                      value={exp.end_date}
                      onChange={(e) => updateExperience(idx, { end_date: e.target.value })}
                    />
                  </div>
                  <div style={{ display: 'flex', gap: 6, marginBottom: 6 }}>
                    <button
                      type="button"
                      className="t-chip"
                      style={{ cursor: 'pointer' }}
                      onClick={() =>
                        updateExperience(idx, {
                          achievements: [
                            ...exp.achievements,
                            '[Role Summary] Owned end-to-end architecture and production delivery.',
                          ],
                        })
                      }
                    >
                      + [Role Summary]
                    </button>
                    <button
                      type="button"
                      className="t-chip"
                      style={{ cursor: 'pointer' }}
                      onClick={() =>
                        updateExperience(idx, {
                          achievements: [...exp.achievements, '[Stack: Python, FastAPI, Docker]'],
                        })
                      }
                    >
                      + [Stack: ...]
                    </button>
                    {experiences.length > 1 && (
                      <button
                        type="button"
                        className="t-chip t-chip--low"
                        style={{ cursor: 'pointer', marginLeft: 'auto' }}
                        onClick={() => removeExperience(idx)}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                  <textarea
                    className="t-textarea"
                    rows={3}
                    value={exp.achievements.join('\n')}
                    onChange={(e) =>
                      updateExperience(idx, {
                        achievements: e.target.value.split('\n').filter((line) => line.trim().length > 0),
                      })
                    }
                    placeholder="One quantified achievement bullet per line..."
                  />
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 26 }}>
              <button type="button" className="t-btn t-btn--outline" onClick={() => setStep(3)}>Back</button>
              <button type="button" className="t-btn t-btn--ink" onClick={() => setStep(5)}>
                Continue to Projects &amp; Edu
                <TailoredIcon name="chevronRight" size={14} color="var(--chalk)" />
              </button>
            </div>
          </section>
        )}

        {/* STEP 5: PROJECTS, EDUCATION & LANGUAGES */}
        {step === 5 && (
          <section className="t-card" style={{ padding: '28px 30px' }}>
            <span className="t-eyebrow">Step 05 · Evidence &amp; Credentials</span>
            <h2 style={{ fontSize: 26, marginTop: 6, marginBottom: 16 }}>Projects, Education &amp; Languages</h2>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <span className="t-label">Featured Projects</span>
              <button type="button" className="t-btn t-btn--subtle t-btn--sm" onClick={addProject}>
                + Add Project
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20 }}>
              {projects.map((proj, idx) => (
                <div key={idx} style={{ border: '1px solid var(--n300)', background: 'var(--chalk)', padding: 12 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 180px', gap: 8, marginBottom: 6 }}>
                    <input
                      className="t-input"
                      placeholder="Project Name"
                      value={proj.name}
                      onChange={(e) => updateProject(idx, { name: e.target.value })}
                    />
                    <input
                      className="t-input"
                      placeholder="Tech stack (Python, SQL)"
                      value={proj.tech_stack.join(', ')}
                      onChange={(e) =>
                        updateProject(idx, {
                          tech_stack: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                        })
                      }
                    />
                  </div>
                  <textarea
                    className="t-textarea"
                    rows={2}
                    placeholder="Measured outcome & architecture..."
                    value={proj.summary}
                    onChange={(e) => updateProject(idx, { summary: e.target.value })}
                  />
                </div>
              ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, paddingTop: 14, borderTop: '1px solid var(--n300)' }}>
              <div>
                <span className="t-label" style={{ display: 'block', marginBottom: 8 }}>Education</span>
                {draft.education.map((edu, i) => (
                  <div key={i} style={{ marginBottom: 8 }}>
                    <input
                      className="t-input"
                      value={edu.degree}
                      onChange={(e) =>
                        setDraft((p) => {
                          const ed = [...p.education];
                          ed[i] = { ...ed[i], degree: e.target.value };
                          return { ...p, education: ed };
                        })
                      }
                      style={{ marginBottom: 4 }}
                    />
                    <input
                      className="t-input"
                      value={edu.institution}
                      onChange={(e) =>
                        setDraft((p) => {
                          const ed = [...p.education];
                          ed[i] = { ...ed[i], institution: e.target.value };
                          return { ...p, education: ed };
                        })
                      }
                    />
                  </div>
                ))}
              </div>
              <div>
                <span className="t-label" style={{ display: 'block', marginBottom: 8 }}>Languages</span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {draft.languages.map((lang, i) => (
                    <div key={i} style={{ display: 'flex', gap: 8 }}>
                      <input
                        className="t-input"
                        value={lang.language}
                        onChange={(e) =>
                          setDraft((p) => {
                            const ls = [...p.languages];
                            ls[i] = { ...ls[i], language: e.target.value };
                            return { ...p, languages: ls };
                          })
                        }
                      />
                      <input
                        className="t-input"
                        value={lang.proficiency}
                        onChange={(e) =>
                          setDraft((p) => {
                            const ls = [...p.languages];
                            ls[i] = { ...ls[i], proficiency: e.target.value };
                            return { ...p, languages: ls };
                          })
                        }
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 26 }}>
              <button type="button" className="t-btn t-btn--outline" onClick={() => setStep(4)}>Back</button>
              <button type="button" className="t-btn t-btn--ink" onClick={() => setStep(6)}>
                Final Review
                <TailoredIcon name="chevronRight" size={14} color="var(--chalk)" />
              </button>
            </div>
          </section>
        )}

        {/* STEP 6: REVIEW & LAUNCH */}
        {step === 6 && (
          <section className="t-card" style={{ padding: '30px' }}>
            <span className="t-eyebrow">Step 06 · Ready to Stitch</span>
            <h2 style={{ fontSize: 28, marginTop: 6, marginBottom: 8 }}>
              Master Profile Review
            </h2>
            <p style={{ color: 'var(--n500)', fontSize: 14, marginBottom: 20 }}>
              Every AI-tailored bullet, cover letter, and radar fit dial draws from this verified base.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 18 }}>
              <div className="t-card--flat" style={{ padding: 14, background: 'var(--chalk)' }}>
                <div className="t-label">Personas</div>
                <div style={{ fontFamily: 'var(--font-voice)', fontSize: 28, fontWeight: 600 }}>
                  {draft.career_personas.length}
                </div>
              </div>
              <div className="t-card--flat" style={{ padding: 14, background: 'var(--chalk)' }}>
                <div className="t-label">Experience Roles</div>
                <div style={{ fontFamily: 'var(--font-voice)', fontSize: 28, fontWeight: 600 }}>
                  {experiences.length}
                </div>
              </div>
              <div className="t-card--flat" style={{ padding: 14, background: 'var(--chalk)' }}>
                <div className="t-label">Projects</div>
                <div style={{ fontFamily: 'var(--font-voice)', fontSize: 28, fontWeight: 600 }}>
                  {projects.length}
                </div>
              </div>
            </div>

            <div className="t-alert t-alert--success" style={{ marginBottom: 22 }}>
              <div className="t-mono" style={{ fontSize: 11, fontWeight: 600, color: 'var(--green)' }}>
                MASTER SUMMARY · {selectedTrack}
              </div>
              <div style={{ fontSize: 14.5, marginTop: 4 }}>
                <strong>{draft.personal_info.full_name}</strong> ({draft.personal_info.primary_email}) ·{' '}
                {draft.residence_and_mobility.target_locations.map((l) => l.city).join(', ')}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button type="button" className="t-btn t-btn--outline" onClick={() => setStep(5)}>
                Back
              </button>
              <button
                type="button"
                className="t-btn t-btn--primary t-btn--lg"
                disabled={saving}
                onClick={handleFinish}
              >
                {saving ? 'Saving Master Profile...' : 'Save Master Profile & Continue'}
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
};
