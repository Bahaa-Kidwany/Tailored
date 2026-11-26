import React from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { TailoredIcon } from '../../brand/TailoredIcons';

export const IdentityDrawer: React.FC = () => {
  const {
    isIdentityDrawerOpen,
    setIsIdentityDrawerOpen,
    currentProfile,
    activePersonaId,
    setPrimaryPersona,
    activeRegionalPhone,
    setActiveRegionalPhone,
    navigateTo,
    signOut,
    dir,
    setDir,
    userEmail,
  } = useWorkspace();

  if (!isIdentityDrawerOpen) return null;

  const profile = currentProfile?.profile;
  const personas = profile?.career_personas || [];
  const fullName = profile?.personal_info.full_name || 'Mostafa Ibrahim';

  return (
    <div className="t-drawer-backdrop" onClick={() => setIsIdentityDrawerOpen(false)}>
      <aside
        className={`t-drawer ${dir === 'rtl' ? 't-drawer--right' : ''}`}
        onClick={(e) => e.stopPropagation()}
        style={{ padding: 24, justifyContent: 'space-between', gap: 24 }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>
          {/* Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              paddingBottom: 16,
              borderBottom: '1.5px solid var(--n300)',
            }}
          >
            <div>
              <span className="t-eyebrow">Active Identity</span>
              <h2 style={{ fontSize: 24, marginTop: 6 }}>{fullName}</h2>
              <div className="t-mono" style={{ fontSize: 12, color: 'var(--n500)', marginTop: 2 }}>
                {userEmail}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsIdentityDrawerOpen(false)}
              className="t-btn t-btn--ghost t-btn--sm"
              aria-label="Close drawer"
            >
              <TailoredIcon name="close" size={16} />
            </button>
          </div>

          {/* Persona Selector */}
          <div>
            <div className="t-label" style={{ color: 'var(--n500)', marginBottom: 10 }}>
              Career Persona Track
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {personas.map((p) => {
                const selected = p.persona_id === activePersonaId;
                return (
                  <button
                    key={p.persona_id}
                    type="button"
                    onClick={() => setPrimaryPersona(p.persona_id)}
                    style={{
                      textAlign: 'left',
                      padding: '12px 14px',
                      background: selected ? 'var(--chalk)' : 'transparent',
                      border: selected ? '2px solid var(--ink)' : '1.5px solid var(--n300)',
                      borderLeft: selected ? '4px solid var(--thread)' : '1.5px solid var(--n300)',
                      cursor: 'pointer',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: 4,
                      }}
                    >
                      <span style={{ fontWeight: 600, fontSize: 14 }}>{p.target_title}</span>
                      {selected && <span className="t-chip t-chip--notch">Active</span>}
                    </div>
                    <div style={{ fontSize: 12.5, color: 'var(--n500)' }}>
                      {p.seniority_level} · {p.years_of_experience} yrs ·{' '}
                      {p.skills_and_tools.core_skills.slice(0, 3).join(', ')}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Regional Phone Switcher */}
          <div>
            <div className="t-label" style={{ color: 'var(--n500)', marginBottom: 10 }}>
              Regional CV Header Phone
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
              {[
                { code: '+20' as const, label: 'Cairo EG' },
                { code: '+966' as const, label: 'Riyadh KSA' },
                { code: '+971' as const, label: 'Dubai UAE' },
              ].map((item) => {
                const active = activeRegionalPhone === item.code;
                return (
                  <button
                    key={item.code}
                    type="button"
                    onClick={() => setActiveRegionalPhone(item.code)}
                    style={{
                      padding: '9px 8px',
                      background: active ? 'var(--ink)' : 'transparent',
                      color: active ? 'var(--chalk)' : 'var(--ink)',
                      border: '1.5px solid var(--ink)',
                      cursor: 'pointer',
                      textAlign: 'center',
                    }}
                  >
                    <div className="t-mono" style={{ fontSize: 13, fontWeight: 600 }}>
                      {item.code}
                    </div>
                    <div style={{ fontSize: 11, opacity: 0.75 }}>{item.label}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Bilingual Layout Toggle (EN / AR) */}
          <div>
            <div className="t-label" style={{ color: 'var(--n500)', marginBottom: 10 }}>
              Language &amp; Reading Direction
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <button
                type="button"
                onClick={() => setDir('ltr')}
                className={`t-btn t-btn--sm ${dir === 'ltr' ? 't-btn--ink' : 't-btn--outline'}`}
              >
                English (LTR)
              </button>
              <button
                type="button"
                onClick={() => setDir('rtl')}
                className={`t-btn t-btn--sm ${dir === 'rtl' ? 't-btn--ink' : 't-btn--outline'}`}
              >
                العربية (RTL)
              </button>
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <div
          style={{
            paddingTop: 18,
            borderTop: '1.5px solid var(--n300)',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          <button
            type="button"
            className="t-btn t-btn--outline"
            onClick={() => {
              setIsIdentityDrawerOpen(false);
              navigateTo('/profile');
            }}
          >
            <TailoredIcon name="profile" size={15} />
            <span>Master Profile &amp; Personas</span>
          </button>
          <button
            type="button"
            className="t-btn t-btn--outline"
            onClick={() => {
              setIsIdentityDrawerOpen(false);
              navigateTo('/plans');
            }}
          >
            <TailoredIcon name="credit" size={15} />
            <span>Plans, Credits &amp; Ledger</span>
          </button>
          <button
            type="button"
            className="t-btn t-btn--outline"
            onClick={() => {
              setIsIdentityDrawerOpen(false);
              navigateTo('/account');
            }}
          >
            <TailoredIcon name="settings" size={15} />
            <span>Account &amp; Security</span>
          </button>
          <button
            type="button"
            className="t-btn t-btn--alarm t-btn--sm"
            style={{ marginTop: 4 }}
            onClick={signOut}
          >
            <TailoredIcon name="logout" size={14} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </div>
  );
};
