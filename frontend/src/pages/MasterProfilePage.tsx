import React, { useState, useEffect } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { TailoredIcon } from '../brand/TailoredIcons';
import {
  ProfileAPI,
  SAMPLE_PROFILE,
  type UserProfilePayload,
} from '../services/profileApi';

type VaultSection =
  | 'personas'
  | 'experience'
  | 'projects'
  | 'identity'
  | 'education'
  | 'certifications';

export const MasterProfilePage: React.FC = () => {
  const { currentProfile, saveProfile, activePersonaId, setActivePersonaId, navigateTo, pushToast } =
    useWorkspace();

  const [draft, setDraft] = useState<UserProfilePayload>(() =>
    JSON.parse(JSON.stringify(currentProfile?.profile || SAMPLE_PROFILE))
  );
  const [section, setSection] = useState<VaultSection>('personas');
  const [isDirty, setIsDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [previewDrawerOpen, setPreviewDrawerOpen] = useState(false);
  const [mergeModalOpen, setMergeModalOpen] = useState(false);
  const [mergeSourceText, setMergeSourceText] = useState('');
  const [parsedMergeCandidate, setParsedMergeCandidate] = useState<Partial<UserProfilePayload> | null>(null);
  const [mergeFields, setMergeFields] = useState({
    personal_info: true,
    experience_highlights: true,
    featured_projects: false,
  });

  const activeIdx = Math.max(
    0,
    draft.career_personas.findIndex((p) => p.persona_id === activePersonaId)
  );
  const activePersona = draft.career_personas[activeIdx] || draft.career_personas[0];

  const mutate = (updater: (prev: UserProfilePayload) => UserProfilePayload) => {
    setDraft((prev) => updater(prev));
    setIsDirty(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveProfile(draft);
      setIsDirty(false);
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        if (isDirty) handleSave();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  const duplicateActivePersona = () => {
    if (!activePersona) return;
    const cloneId = `p_${Date.now()}`;
    const clone = {
      ...JSON.parse(JSON.stringify(activePersona)),
      persona_id: cloneId,
      target_title: `${activePersona.target_title} (Copy)`,
      is_primary: false,
    };
    mutate((p) => ({ ...p, career_personas: [...p.career_personas, clone] }));
    setActivePersonaId(cloneId);
    pushToast('Duplicated persona for specialization.');
  };

  const handleParseMerge = async () => {
    if (!mergeSourceText.trim()) return;
    try {
      const res = await ProfileAPI.parseLatex(mergeSourceText);
      setParsedMergeCandidate(res.profile);
    } catch {
      setParsedMergeCandidate(SAMPLE_PROFILE);
    }
  };

  const applySafeMerge = () => {
    if (!parsedMergeCandidate) return;
    const candPersona = parsedMergeCandidate.career_personas?.[0];
    mutate((prev) => ({
      ...prev,
      personal_info: mergeFields.personal_info
        ? { ...prev.personal_info, ...(parsedMergeCandidate.personal_info || {}) }
        : prev.personal_info,
      career_personas: prev.career_personas.map((cp, i) => {
        if (i !== activeIdx || !candPersona) return cp;
        return {
          ...cp,
          experience_highlights: mergeFields.experience_highlights
            ? candPersona.experience_highlights
            : cp.experience_highlights,
          featured_projects: mergeFields.featured_projects
            ? candPersona.featured_projects
            : cp.featured_projects,
        };
      }),
    }));
    setMergeModalOpen(false);
    setParsedMergeCandidate(null);
    pushToast('Merged selected resume fields without discarding existing edits.', { variant: 'success' });
  };

  const exps = activePersona?.experience_highlights || [];
  const projs = activePersona?.featured_projects || [];
  const certs = activePersona?.certifications || [];
  const primaryContact =
    draft.personal_info.contact_numbers.find((c) => c.is_primary) ||
    draft.personal_info.contact_numbers[0];
  const phoneText = primaryContact
    ? `${primaryContact.dial_code} ${primaryContact.phone_number}`
    : '+20 100 482 9102';

  const skillTotal =
    (activePersona?.skills_and_tools.core_skills.length || 0) +
    (activePersona?.skills_and_tools.programming_languages.length || 0) +
    (activePersona?.skills_and_tools.frameworks_and_libraries.length || 0);

  return (
    <div className="t-page-fluid">
      {/* Top Action Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          flexWrap: 'wrap',
          gap: 14,
          paddingBottom: 16,
          borderBottom: '1.5px solid var(--ink)',
          marginBottom: 22,
        }}
      >
        <div>
          <span className="t-eyebrow">Master Profile Vault · Single Source of Truth</span>
          <h1 style={{ fontSize: 30, marginTop: 4 }}>{draft.personal_info.full_name}</h1>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            type="button"
            className="t-btn t-btn--outline t-btn--sm"
            onClick={() => setPreviewDrawerOpen(true)}
          >
            <TailoredIcon name="eye" size={14} />
            Preview Base CV (0 cr)
          </button>
          <button
            type="button"
            className="t-btn t-btn--subtle t-btn--sm"
            onClick={() => setMergeModalOpen(true)}
          >
            <TailoredIcon name="upload" size={14} />
            Re-Upload &amp; Safe Merge
          </button>
        </div>
      </div>

      {/* Balanced 3-Column Editorial Vault (220px Nav | Fluid Editor | 340px Live CV Readiness Card) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '220px minmax(0, 1fr) 340px',
          gap: 22,
          alignItems: 'start',
        }}
      >
        <nav style={{ position: 'sticky', top: 76, display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div>
            <div className="t-label" style={{ marginBottom: 8 }}>Persona-Scoped</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <button
                type="button"
                className={`t-btn t-btn--sm ${section === 'personas' ? 't-btn--ink' : 't-btn--ghost'}`}
                style={{ justifyContent: 'flex-start' }}
                onClick={() => setSection('personas')}
              >
                Personas &amp; Core Stack ({draft.career_personas.length})
              </button>
              <button
                type="button"
                className={`t-btn t-btn--sm ${section === 'experience' ? 't-btn--ink' : 't-btn--ghost'}`}
                style={{ justifyContent: 'flex-start' }}
                onClick={() => setSection('experience')}
              >
                Work Experience ({exps.length})
              </button>
              <button
                type="button"
                className={`t-btn t-btn--sm ${section === 'projects' ? 't-btn--ink' : 't-btn--ghost'}`}
                style={{ justifyContent: 'flex-start' }}
                onClick={() => setSection('projects')}
              >
                Projects ({projs.length})
              </button>
              <button
                type="button"
                className={`t-btn t-btn--sm ${section === 'certifications' ? 't-btn--ink' : 't-btn--ghost'}`}
                style={{ justifyContent: 'flex-start' }}
                onClick={() => setSection('certifications')}
              >
                Certifications ({certs.length})
              </button>
            </div>
          </div>

          <div style={{ borderTop: '1px solid var(--n300)', paddingTop: 14 }}>
            <div className="t-label" style={{ marginBottom: 8 }}>Global Shared Truth</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <button
                type="button"
                className={`t-btn t-btn--sm ${section === 'identity' ? 't-btn--ink' : 't-btn--ghost'}`}
                style={{ justifyContent: 'flex-start' }}
                onClick={() => setSection('identity')}
              >
                Personal &amp; Regional Phones
              </button>
              <button
                type="button"
                className={`t-btn t-btn--sm ${section === 'education' ? 't-btn--ink' : 't-btn--ghost'}`}
                style={{ justifyContent: 'flex-start' }}
                onClick={() => setSection('education')}
              >
                Education &amp; Languages
              </button>
            </div>
          </div>
        </nav>

        {/* Center Fluid Editor */}
        <div style={{ minWidth: 0 }}>
          {section === 'personas' && (
            <div className="t-card" style={{ padding: '24px 28px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <span className="t-eyebrow">Persona-Scoped Truth</span>
                  <h2 style={{ fontSize: 22, marginTop: 4 }}>Career Personas</h2>
                </div>
                <button type="button" className="t-btn t-btn--outline t-btn--sm" onClick={duplicateActivePersona}>
                  <TailoredIcon name="copy" size={13} />
                  Duplicate Persona
                </button>
              </div>

              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 18 }}>
                {draft.career_personas.map((p) => (
                  <button
                    key={p.persona_id}
                    type="button"
                    className={`t-chip ${p.persona_id === activePersona?.persona_id ? 't-chip--notch' : ''}`}
                    style={{
                      cursor: 'pointer',
                      padding: '7px 12px',
                      background: p.persona_id === activePersona?.persona_id ? 'var(--ink)' : 'var(--chalk)',
                      color: p.persona_id === activePersona?.persona_id ? 'var(--chalk)' : 'var(--ink)',
                    }}
                    onClick={() => setActivePersonaId(p.persona_id)}
                  >
                    {p.target_title}
                  </button>
                ))}
              </div>

              {activePersona && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div>
                    <label className="t-label" style={{ display: 'block', marginBottom: 6 }}>Persona Headline Title</label>
                    <input
                      className="t-input"
                      value={activePersona.target_title}
                      onChange={(e) =>
                        mutate((prev) => ({
                          ...prev,
                          career_personas: prev.career_personas.map((cp) =>
                            cp.persona_id === activePersona.persona_id ? { ...cp, target_title: e.target.value } : cp
                          ),
                        }))
                      }
                    />
                  </div>
                  <div>
                    <label className="t-label" style={{ display: 'block', marginBottom: 6 }}>Persona Summary Bio</label>
                    <textarea
                      className="t-textarea"
                      rows={4}
                      value={activePersona.summary_bio}
                      onChange={(e) =>
                        mutate((prev) => ({
                          ...prev,
                          career_personas: prev.career_personas.map((cp) =>
                            cp.persona_id === activePersona.persona_id
                              ? { ...cp, summary_bio: e.target.value }
                              : cp
                          ),
                        }))
                      }
                    />
                  </div>
                  <div>
                    <label className="t-label" style={{ display: 'block', marginBottom: 6 }}>
                      Core Technical Stack (comma-separated)
                    </label>
                    <textarea
                      className="t-textarea"
                      rows={2}
                      value={activePersona.skills_and_tools.core_skills.join(', ')}
                      onChange={(e) =>
                        mutate((prev) => ({
                          ...prev,
                          career_personas: prev.career_personas.map((cp) =>
                            cp.persona_id === activePersona.persona_id
                              ? {
                                  ...cp,
                                  skills_and_tools: {
                                    ...cp.skills_and_tools,
                                    core_skills: e.target.value
                                      .split(',')
                                      .map((s) => s.trim())
                                      .filter(Boolean),
                                  },
                                }
                              : cp
                          ),
                        }))
                      }
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {section === 'identity' && (
            <div className="t-card" style={{ padding: '24px 28px' }}>
              <span className="t-eyebrow">Global Shared Truth</span>
              <h2 style={{ fontSize: 22, marginTop: 4, marginBottom: 16 }}>Personal &amp; Regional Dual-SIM Phones</h2>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 18 }}>
                <div>
                  <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>Full Name</label>
                  <input
                    className="t-input"
                    value={draft.personal_info.full_name}
                    onChange={(e) =>
                      mutate((p) => ({ ...p, personal_info: { ...p.personal_info, full_name: e.target.value } }))
                    }
                  />
                </div>
                <div>
                  <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>Primary Email</label>
                  <input
                    className="t-input"
                    value={draft.personal_info.primary_email}
                    onChange={(e) =>
                      mutate((p) => ({ ...p, personal_info: { ...p.personal_info, primary_email: e.target.value } }))
                    }
                  />
                </div>
                <div>
                  <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>LinkedIn</label>
                  <input
                    className="t-input"
                    value={draft.personal_info.links.linkedin || ''}
                    onChange={(e) =>
                      mutate((p) => ({
                        ...p,
                        personal_info: { ...p.personal_info, links: { ...p.personal_info.links, linkedin: e.target.value } },
                      }))
                    }
                  />
                </div>
                <div>
                  <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>GitHub</label>
                  <input
                    className="t-input"
                    value={draft.personal_info.links.github || ''}
                    onChange={(e) =>
                      mutate((p) => ({
                        ...p,
                        personal_info: { ...p.personal_info, links: { ...p.personal_info.links, github: e.target.value } },
                      }))
                    }
                  />
                </div>
              </div>

              <div className="t-label" style={{ marginBottom: 8 }}>Regional Phone Numbers</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {draft.personal_info.contact_numbers.map((cn, idx) => (
                  <div key={idx} style={{ display: 'grid', gridTemplateColumns: '120px 80px 1fr auto', gap: 8 }}>
                    <input
                      className="t-input"
                      value={cn.label}
                      onChange={(e) =>
                        mutate((p) => {
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
                        mutate((p) => {
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
                        mutate((p) => {
                          const nums = [...p.personal_info.contact_numbers];
                          nums[idx] = { ...nums[idx], phone_number: e.target.value };
                          return { ...p, personal_info: { ...p.personal_info, contact_numbers: nums } };
                        })
                      }
                    />
                    <span className={`t-chip ${cn.is_primary ? 't-chip--strong' : ''}`}>
                      {cn.is_primary ? 'Primary' : 'Secondary'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {section === 'experience' && (
            <div className="t-card" style={{ padding: '24px 28px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <span className="t-eyebrow">{activePersona?.target_title}</span>
                  <h2 style={{ fontSize: 22, marginTop: 4 }}>Work Experience Highlights</h2>
                </div>
                <button
                  type="button"
                  className="t-btn t-btn--outline t-btn--sm"
                  onClick={() =>
                    mutate((p) => ({
                      ...p,
                      career_personas: p.career_personas.map((cp, i) =>
                        i === activeIdx
                          ? {
                              ...cp,
                              experience_highlights: [
                                ...cp.experience_highlights,
                                {
                                  company: '',
                                  role: '',
                                  start_date: 'Jan 2024',
                                  end_date: 'Present',
                                  location: 'Cairo, Egypt',
                                  achievements: ['Owned production architecture and measurable KPIs.'],
                                },
                              ],
                            }
                          : cp
                      ),
                    }))
                  }
                >
                  + Add Role
                </button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {exps.map((exp, idx) => (
                  <div key={idx} style={{ border: '1px solid var(--n300)', background: 'var(--chalk)', padding: 14 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 110px 110px', gap: 8, marginBottom: 8 }}>
                      <input
                        className="t-input"
                        value={exp.role}
                        placeholder="Role"
                        onChange={(e) =>
                          mutate((p) => ({
                            ...p,
                            career_personas: p.career_personas.map((cp, i) =>
                              i === activeIdx
                                ? {
                                    ...cp,
                                    experience_highlights: cp.experience_highlights.map((x, j) =>
                                      j === idx ? { ...x, role: e.target.value } : x
                                    ),
                                  }
                                : cp
                            ),
                          }))
                        }
                      />
                      <input
                        className="t-input"
                        value={exp.company}
                        placeholder="Company"
                        onChange={(e) =>
                          mutate((p) => ({
                            ...p,
                            career_personas: p.career_personas.map((cp, i) =>
                              i === activeIdx
                                ? {
                                    ...cp,
                                    experience_highlights: cp.experience_highlights.map((x, j) =>
                                      j === idx ? { ...x, company: e.target.value } : x
                                    ),
                                  }
                                : cp
                            ),
                          }))
                        }
                      />
                      <input
                        className="t-input"
                        value={exp.start_date}
                        placeholder="Start"
                        onChange={(e) =>
                          mutate((p) => ({
                            ...p,
                            career_personas: p.career_personas.map((cp, i) =>
                              i === activeIdx
                                ? {
                                    ...cp,
                                    experience_highlights: cp.experience_highlights.map((x, j) =>
                                      j === idx ? { ...x, start_date: e.target.value } : x
                                    ),
                                  }
                                : cp
                            ),
                          }))
                        }
                      />
                      <input
                        className="t-input"
                        value={exp.end_date}
                        placeholder="End"
                        onChange={(e) =>
                          mutate((p) => ({
                            ...p,
                            career_personas: p.career_personas.map((cp, i) =>
                              i === activeIdx
                                ? {
                                    ...cp,
                                    experience_highlights: cp.experience_highlights.map((x, j) =>
                                      j === idx ? { ...x, end_date: e.target.value } : x
                                    ),
                                  }
                                : cp
                            ),
                          }))
                        }
                      />
                    </div>
                    <textarea
                      className="t-textarea"
                      rows={3}
                      value={exp.achievements.join('\n')}
                      onChange={(e) =>
                        mutate((p) => ({
                          ...p,
                          career_personas: p.career_personas.map((cp, i) =>
                            i === activeIdx
                              ? {
                                  ...cp,
                                  experience_highlights: cp.experience_highlights.map((x, j) =>
                                    j === idx ? { ...x, achievements: e.target.value.split('\n') } : x
                                  ),
                                }
                              : cp
                          ),
                        }))
                      }
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {section === 'projects' && (
            <div className="t-card" style={{ padding: '24px 28px' }}>
              <span className="t-eyebrow">{activePersona?.target_title}</span>
              <h2 style={{ fontSize: 22, marginTop: 4, marginBottom: 14 }}>Featured Projects</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {projs.map((pr, idx) => (
                  <div key={idx} style={{ border: '1px solid var(--n300)', background: 'var(--chalk)', padding: 14 }}>
                    <input
                      className="t-input"
                      value={pr.name}
                      onChange={(e) =>
                        mutate((p) => ({
                          ...p,
                          career_personas: p.career_personas.map((cp, i) =>
                            i === activeIdx
                              ? {
                                  ...cp,
                                  featured_projects: cp.featured_projects.map((x, j) =>
                                    j === idx ? { ...x, name: e.target.value } : x
                                  ),
                                }
                              : cp
                          ),
                        }))
                      }
                      style={{ marginBottom: 8, fontWeight: 600 }}
                    />
                    <textarea
                      className="t-textarea"
                      rows={2}
                      value={pr.summary}
                      onChange={(e) =>
                        mutate((p) => ({
                          ...p,
                          career_personas: p.career_personas.map((cp, i) =>
                            i === activeIdx
                              ? {
                                  ...cp,
                                  featured_projects: cp.featured_projects.map((x, j) =>
                                    j === idx ? { ...x, summary: e.target.value } : x
                                  ),
                                }
                              : cp
                          ),
                        }))
                      }
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {section === 'education' && (
            <div className="t-card" style={{ padding: '24px 28px' }}>
              <span className="t-eyebrow">Credentials &amp; Fluency</span>
              <h2 style={{ fontSize: 22, marginTop: 4, marginBottom: 14 }}>Education &amp; Languages</h2>
              {draft.education.map((ed, i) => (
                <div key={i} style={{ border: '1px solid var(--n300)', background: 'var(--chalk)', padding: 14, marginBottom: 12 }}>
                  <div style={{ fontWeight: 600 }}>{ed.degree} {ed.field_of_study ? `— ${ed.field_of_study}` : ''}</div>
                  <div className="t-mono" style={{ fontSize: 12, color: 'var(--n500)', marginTop: 2 }}>
                    {ed.institution} {ed.graduation_year ? `· Class of ${ed.graduation_year}` : ''} {ed.grade_or_gpa ? `· ${ed.grade_or_gpa}` : ''}
                  </div>
                </div>
              ))}
              <div className="t-label" style={{ marginTop: 14, marginBottom: 8 }}>Spoken Languages</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {draft.languages.map((l, i) => (
                  <span key={i} className="t-chip t-chip--notch">
                    {l.language} · {l.proficiency}
                  </span>
                ))}
              </div>
            </div>
          )}

          {section === 'certifications' && (
            <div className="t-card" style={{ padding: '24px 28px' }}>
              <span className="t-eyebrow">Verified Credentials</span>
              <h2 style={{ fontSize: 22, marginTop: 4, marginBottom: 14 }}>Certifications</h2>
              {certs.map((c, i) => (
                <div key={i} style={{ border: '1px solid var(--n300)', background: 'var(--chalk)', padding: 12, marginBottom: 8 }}>
                  <div style={{ fontWeight: 600 }}>{c.name}</div>
                  <div className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)' }}>
                    {c.issuer} {c.issue_date ? `· ${c.issue_date}` : ''}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Sticky Live Base CV Readiness & ATS Header Snapshot */}
        <aside className="t-card" style={{ padding: '20px', position: 'sticky', top: 76 }}>
          <span className="t-eyebrow">Live Base Snapshot</span>
          <h3 style={{ fontSize: 19, marginTop: 4, marginBottom: 12 }}>ATS Readiness Card</h3>

          <div style={{ border: '1px solid var(--ink)', background: 'var(--chalk)', padding: 14, marginBottom: 14 }}>
            <div style={{ fontFamily: 'var(--font-voice)', fontSize: 18, fontWeight: 600 }}>
              {draft.personal_info.full_name}
            </div>
            <div className="t-mono" style={{ fontSize: 11, color: 'var(--n700)', marginTop: 3 }}>
              {activePersona?.target_title}
            </div>
            <div className="t-mono" style={{ fontSize: 10.5, color: 'var(--n500)', marginTop: 4, wordBreak: 'break-word' }}>
              {draft.personal_info.primary_email} · {phoneText}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 14 }}>
            <div style={{ border: '1px solid var(--n300)', padding: '8px 10px', background: 'var(--chalk)' }}>
              <div className="t-label" style={{ fontSize: 9.5, color: 'var(--n500)' }}>Verified Roles</div>
              <div style={{ fontFamily: 'var(--font-voice)', fontSize: 20, fontWeight: 600 }}>{exps.length}</div>
            </div>
            <div style={{ border: '1px solid var(--n300)', padding: '8px 10px', background: 'var(--chalk)' }}>
              <div className="t-label" style={{ fontSize: 9.5, color: 'var(--n500)' }}>Indexed Skills</div>
              <div style={{ fontFamily: 'var(--font-voice)', fontSize: 20, fontWeight: 600 }}>{skillTotal}</div>
            </div>
          </div>

          <div className="t-label" style={{ marginBottom: 6 }}>Persona Stack Preview</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 14 }}>
            {activePersona?.skills_and_tools.core_skills.slice(0, 6).map((sk) => (
              <span key={sk} className="t-chip t-chip--notch">{sk}</span>
            ))}
          </div>

          <button
            type="button"
            className="t-btn t-btn--primary t-btn--sm"
            style={{ width: '100%' }}
            onClick={() => navigateTo('/studio')}
          >
            Open Active Persona in Studio →
          </button>
        </aside>
      </div>

      {/* Sticky Dirty Save Bar */}
      {isDirty && (
        <div
          style={{
            position: 'fixed',
            bottom: 20,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'var(--ink)',
            color: 'var(--chalk)',
            border: '1.5px solid var(--thread)',
            padding: '10px 20px',
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            zIndex: 55,
          }}
        >
          <span className="t-mono" style={{ fontSize: 12 }}>
            Unsaved edits in Master Truth · Press Cmd/Ctrl+S
          </span>
          <button type="button" className="t-btn t-btn--primary t-btn--sm" disabled={saving} onClick={handleSave}>
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      )}

      {/* Preview Base CV Slide-Over Drawer */}
      {previewDrawerOpen && (
        <div className="t-drawer-backdrop" onClick={() => setPreviewDrawerOpen(false)}>
          <aside className="t-drawer t-drawer--right" style={{ width: 520, padding: 26 }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 12, borderBottom: '1.5px solid var(--ink)', marginBottom: 16 }}>
              <div>
                <span className="t-eyebrow">Canonical Base Preview (0 cr)</span>
                <h3 style={{ fontSize: 20, marginTop: 3 }}>{activePersona?.target_title}</h3>
              </div>
              <button type="button" className="t-btn t-btn--ghost t-btn--sm" onClick={() => setPreviewDrawerOpen(false)}>
                <TailoredIcon name="close" size={16} />
              </button>
            </div>
            <div className="t-cv-sheet" style={{ padding: 22, minHeight: 540 }}>
              <div style={{ fontFamily: 'var(--font-voice)', fontSize: 20, fontWeight: 600 }}>
                {draft.personal_info.full_name}
              </div>
              <div className="t-mono" style={{ fontSize: 11, color: 'var(--n500)', marginBottom: 12 }}>
                {draft.personal_info.primary_email} · {phoneText}
              </div>
              <p style={{ fontSize: 13, lineHeight: 1.5 }}>{activePersona?.summary_bio}</p>
              <div className="t-label" style={{ marginTop: 12, marginBottom: 6 }}>Stack</div>
              <div style={{ fontSize: 12.5 }}>{activePersona?.skills_and_tools.core_skills.join(' · ')}</div>
            </div>
          </aside>
        </div>
      )}

      {/* Safe CV Re-Upload Field-by-Field Merge Modal */}
      {mergeModalOpen && (
        <div className="t-backdrop" onClick={() => setMergeModalOpen(false)}>
          <div className="t-modal" style={{ width: 560, padding: 26 }} onClick={(e) => e.stopPropagation()}>
            <span className="t-eyebrow">Safe Re-Upload &amp; Diff Merge</span>
            <h3 style={{ fontSize: 24, marginTop: 6, marginBottom: 8 }}>Select fields to update</h3>
            <p style={{ fontSize: 13.5, color: 'var(--n500)', marginBottom: 12 }}>
              Paste updated LaTeX or resume text below. Custom personas and unselected sections stay untouched.
            </p>
            <textarea
              className="t-textarea"
              rows={4}
              placeholder="Paste updated CV text or LaTeX snippet..."
              value={mergeSourceText}
              onChange={(e) => setMergeSourceText(e.target.value)}
            />
            {!parsedMergeCandidate ? (
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
                <button type="button" className="t-btn t-btn--ghost t-btn--sm" onClick={() => setMergeModalOpen(false)}>
                  Cancel
                </button>
                <button type="button" className="t-btn t-btn--ink t-btn--sm" onClick={handleParseMerge}>
                  Inspect Diffs
                </button>
              </div>
            ) : (
              <div style={{ marginTop: 14 }}>
                <div className="t-label" style={{ marginBottom: 8 }}>Choose Which Extracted Sections to Merge</div>
                {(
                  [
                    ['personal_info', 'Update Contact Info & Links'],
                    ['experience_highlights', 'Merge Extracted Experience Roles'],
                    ['featured_projects', 'Overwrite Extracted Projects'],
                  ] as const
                ).map(([key, label]) => (
                  <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, fontSize: 13.5 }}>
                    <input
                      type="checkbox"
                      checked={mergeFields[key]}
                      onChange={(e) => setMergeFields((f) => ({ ...f, [key]: e.target.checked }))}
                    />
                    {label}
                  </label>
                ))}
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 14 }}>
                  <button type="button" className="t-btn t-btn--primary t-btn--sm" onClick={applySafeMerge}>
                    Apply Checked Fields
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
