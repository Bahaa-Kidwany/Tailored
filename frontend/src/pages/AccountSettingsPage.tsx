import React, { useEffect, useState } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { SAMPLE_PROFILE } from '../services/profileApi';
import { AuthAPI, type PrivacyConsentsPayload } from '../services/authApi';
import { AgentAPI, type BehavioralMemoryFact, type ProactiveSuggestion } from '../services/agentApi';
import { ApiError, getAccessToken } from '../services/apiClient';
import { TelemetrySDK } from '../services/telemetrySdk';

export const AccountSettingsPage: React.FC = () => {
  const {
    userEmail,
    updateAccountEmail,
    hasPassword,
    twoFactorEnabled,
    toggleTwoFactor,
    connectedSso,
    toggleSso,
    sessions,
    revokeSession,
    dir,
    setDir,
    density,
    setDensity,
    defaultHomeRoute,
    setDefaultHomeRoute,
    defaultIntensity,
    setDefaultIntensity,
    notifThreshold,
    setNotifThreshold,
    notifCadence,
    setNotifCadence,
    resetAllPaneWidths,
    currentProfile,
    signOut,
    navigateTo,
    pushToast,
  } = useWorkspace();

  const [emailDraft, setEmailDraft] = useState(userEmail);
  const [deleteConfirm, setDeleteConfirm] = useState('');

  // 2FA Modal state
  const [twoFaModalMode, setTwoFaModalMode] = useState<'enable' | 'disable' | null>(null);
  const [twoFaSetupData, setTwoFaSetupData] = useState<{
    secret: string;
    otpauth_uri: string;
    recovery_codes: string[];
  } | null>(null);
  const [twoFaCodeInput, setTwoFaCodeInput] = useState('');
  const [twoFaBusy, setTwoFaBusy] = useState(false);

  // Privacy & Telemetry Consents state
  const [consents, setConsents] = useState<PrivacyConsentsPayload>({
    analytics_micro_signals: true,
    ai_passive_learning: true,
    proactive_nudges: true,
  });

  // AI Behavioral Memory Inspector state
  const [memoryFacts, setMemoryFacts] = useState<BehavioralMemoryFact[]>([]);
  const [proactiveSuggestions, setProactiveSuggestions] = useState<ProactiveSuggestion[]>([]);
  const [memoryLoading, setMemoryLoading] = useState(false);

  const loadPrivacyAndMemory = async () => {
    if (!getAccessToken()) return;
    setMemoryLoading(true);
    try {
      const [priv, mem] = await Promise.all([
        AuthAPI.getPrivacy().catch(() => null),
        AgentAPI.getMemory().catch(() => null),
      ]);
      if (priv) {
        setConsents(priv);
        TelemetrySDK.setConsent(priv.analytics_micro_signals);
      }
      if (mem) {
        setMemoryFacts(mem.memory_facts || []);
        setProactiveSuggestions(mem.proactive_suggestions || []);
      }
    } finally {
      setMemoryLoading(false);
    }
  };

  useEffect(() => {
    void loadPrivacyAndMemory();
  }, []);

  const handleConsentToggle = async (key: keyof PrivacyConsentsPayload) => {
    const nextValue = !consents[key];
    const nextState: PrivacyConsentsPayload = { ...consents, [key]: nextValue };
    setConsents(nextState);
    if (key === 'analytics_micro_signals') {
      TelemetrySDK.setConsent(nextValue);
    }
    if (getAccessToken()) {
      try {
        const updated = await AuthAPI.updatePrivacy({ [key]: nextValue });
        setConsents(updated);
        TelemetrySDK.setConsent(updated.analytics_micro_signals);
        pushToast('Privacy consent preference saved.', { variant: 'success' });
      } catch {
        setConsents(consents);
        pushToast('Could not persist privacy setting.', { variant: 'error' });
      }
    } else {
      pushToast('Privacy preference updated in session.');
    }
  };

  const handleOpen2faModal = async () => {
    setTwoFaCodeInput('');
    if (twoFactorEnabled) {
      setTwoFaSetupData(null);
      setTwoFaModalMode('disable');
      return;
    }
    if (!getAccessToken()) {
      toggleTwoFactor(true);
      return;
    }
    setTwoFaBusy(true);
    try {
      const setup = await AuthAPI.setup2fa();
      setTwoFaSetupData(setup);
      setTwoFaModalMode('enable');
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Unable to start 2FA setup.';
      pushToast(msg, { variant: 'error' });
    } finally {
      setTwoFaBusy(false);
    }
  };

  const handleConfirm2faModal = async (e: React.FormEvent) => {
    e.preventDefault();
    const code = twoFaCodeInput.trim();
    if (!code) return;
    if (!getAccessToken()) {
      toggleTwoFactor(twoFaModalMode === 'enable');
      setTwoFaModalMode(null);
      return;
    }
    setTwoFaBusy(true);
    try {
      if (twoFaModalMode === 'enable') {
        await AuthAPI.enable2fa(code);
        toggleTwoFactor(true);
      } else if (twoFaModalMode === 'disable') {
        await AuthAPI.disable2fa(code);
        toggleTwoFactor(false);
      }
      setTwoFaModalMode(null);
      setTwoFaSetupData(null);
      setTwoFaCodeInput('');
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Invalid verification code.';
      pushToast(msg, { variant: 'error' });
    } finally {
      setTwoFaBusy(false);
    }
  };

  const handleDeleteFact = async (factId: string) => {
    setMemoryFacts((prev) => prev.filter((f) => f.id !== factId));
    if (getAccessToken()) {
      await AgentAPI.deleteMemoryFact(factId).catch(() => {});
    }
    pushToast('Removed behavioral memory fact.');
  };

  const handleClearMemory = async () => {
    setMemoryFacts([]);
    setProactiveSuggestions([]);
    if (getAccessToken()) {
      await AgentAPI.clearMemory().catch(() => {});
    }
    pushToast('Cleared all ambient behavioral memory.', { variant: 'success' });
  };

  const handleResolveSuggestion = async (sugg: ProactiveSuggestion, status: 'clicked' | 'dismissed') => {
    setProactiveSuggestions((prev) => prev.map((s) => (s.id === sugg.id ? { ...s, status } : s)));
    if (getAccessToken()) {
      await AgentAPI.resolveSuggestion(sugg.id, status).catch(() => {});
    }
    if (status === 'clicked' && sugg.cta_route) {
      navigateTo(sugg.cta_route);
    }
  };

  // Sole-Login Protection Guard: count active login channels
  const activeAuthCount =
    (hasPassword ? 1 : 0) + (connectedSso.google ? 1 : 0) + (connectedSso.linkedin ? 1 : 0);

  const handleToggleSso = (provider: 'google' | 'linkedin') => {
    const isDisconnecting = connectedSso[provider];
    if (isDisconnecting && activeAuthCount <= 1) {
      pushToast('Cannot disconnect your only remaining sign-in method. Set a password first.', {
        variant: 'error',
      });
      return;
    }
    toggleSso(provider);
  };

  const handleExportJson = async () => {
    if (getAccessToken()) {
      try {
        const blob = await AuthAPI.exportArchive();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'tailored_gdpr_export_archive.zip';
        a.click();
        URL.revokeObjectURL(url);
        pushToast('Exported verified GDPR Vault .zip archive.', { variant: 'success' });
        return;
      } catch {
        // fallback to client JSON export below
      }
    }
    const payload = JSON.stringify(currentProfile?.profile || SAMPLE_PROFILE, null, 2);
    const blob = new Blob([payload], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'tailored_master_profile_gdpr_export.json';
    a.click();
    URL.revokeObjectURL(url);
    pushToast('Exported complete Master Profile JSON archive.', { variant: 'success' });
  };

  return (
    <div className="t-page-fluid">
      <div style={{ marginBottom: 22 }}>
        <span className="t-eyebrow">Account, Security & Ergonomics</span>
        <h1 style={{ fontSize: 30, marginTop: 4 }}>Workspace & Security Settings</h1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18, alignItems: 'start' }}>
        {/* 1. Credentials & 2FA */}
        <section className="t-card" style={{ padding: 24 }}>
          <span className="t-eyebrow">Identity & Access</span>
          <h2 style={{ fontSize: 20, marginTop: 4, marginBottom: 14 }}>Credentials & Two-Factor Auth</h2>

          <div style={{ marginBottom: 14 }}>
            <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>Account Email</label>
            <div style={{ display: 'flex', gap: 8 }}>
              <input className="t-input" value={emailDraft} onChange={(e) => setEmailDraft(e.target.value)} />
              <button type="button" className="t-btn t-btn--ink t-btn--sm" onClick={() => updateAccountEmail(emailDraft)}>
                Update
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderTop: '1px solid var(--n300)' }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>Authenticator App 2FA</div>
              <div className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                {twoFactorEnabled ? 'Protected via TOTP codes' : 'Optional second verification step'}
              </div>
            </div>
            <button
              type="button"
              disabled={twoFaBusy}
              className={`t-btn t-btn--sm ${twoFactorEnabled ? 't-btn--outline' : 't-btn--primary'}`}
              onClick={() => void handleOpen2faModal()}
            >
              {twoFaBusy ? 'Preparing…' : twoFactorEnabled ? 'Disable 2FA' : 'Enable 2FA'}
            </button>
          </div>
        </section>

        {/* 2. Connected SSO with Sole-Login Guard */}
        <section className="t-card" style={{ padding: 24 }}>
          <span className="t-eyebrow">Single Sign-On</span>
          <h2 style={{ fontSize: 20, marginTop: 4, marginBottom: 14 }}>Connected Providers</h2>
          <p style={{ fontSize: 13, color: 'var(--n500)', marginBottom: 12 }}>
            Sole-login guard prevents disconnecting your last sign-in channel without a backup method.
          </p>

          {(['google', 'linkedin'] as const).map((prov) => {
            const on = connectedSso[prov];
            return (
              <div
                key={prov}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '10px 0',
                  borderTop: '1px solid var(--n300)',
                }}
              >
                <div>
                  <strong style={{ textTransform: 'capitalize' }}>{prov}</strong>
                  <div className="t-mono" style={{ fontSize: 11, color: on ? 'var(--green)' : 'var(--n500)' }}>
                    {on ? 'Connected' : 'Not linked'}
                  </div>
                </div>
                <button
                  type="button"
                  className={`t-btn t-btn--sm ${on ? 't-btn--outline' : 't-btn--ink'}`}
                  onClick={() => handleToggleSso(prov)}
                >
                  {on ? 'Disconnect' : 'Connect'}
                </button>
              </div>
            );
          })}
        </section>

        {/* 3. Workspace Ergonomics (EN/AR RTL, Density, Split-Pane Reset) */}
        <section className="t-card" style={{ padding: 24 }}>
          <span className="t-eyebrow">Brand Direction & Ergonomics</span>
          <h2 style={{ fontSize: 20, marginTop: 4, marginBottom: 14 }}>Layout & Typography Preferences</h2>

          <div style={{ marginBottom: 14 }}>
            <label className="t-label" style={{ display: 'block', marginBottom: 6 }}>Interface Direction (Brand Dual-Script)</label>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                type="button"
                className={`t-btn t-btn--sm ${dir === 'ltr' ? 't-btn--ink' : 't-btn--outline'}`}
                onClick={() => setDir('ltr')}
              >
                English (LTR)
              </button>
              <button
                type="button"
                className={`t-btn t-btn--sm ${dir === 'rtl' ? 't-btn--ink' : 't-btn--outline'}`}
                onClick={() => setDir('rtl')}
              >
                العربية (RTL Mirror)
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 14 }}>
            <div>
              <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>Default Home Route</label>
              <select
                className="t-select"
                value={defaultHomeRoute}
                onChange={(e) => setDefaultHomeRoute(e.target.value as '/dashboard' | '/radar' | '/studio')}
              >
                <option value="/dashboard">Dashboard Overview</option>
                <option value="/radar">Job Radar</option>
                <option value="/studio">CV Studio</option>
              </select>
            </div>
            <div>
              <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>Tailor Intensity Default</label>
              <select
                className="t-select"
                value={defaultIntensity}
                onChange={(e) => setDefaultIntensity(e.target.value as 'Surgical' | 'Metrics+' | 'Executive')}
              >
                <option value="Surgical">Surgical</option>
                <option value="Metrics+">Metrics+</option>
                <option value="Executive">Executive</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 10, borderTop: '1px solid var(--n300)' }}>
            <div>
              <div className="t-label">UI Density</div>
              <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
                {(['cozy', 'compact'] as const).map((d) => (
                  <button
                    key={d}
                    type="button"
                    className="t-chip"
                    style={{
                      cursor: 'pointer',
                      background: density === d ? 'var(--ink)' : 'var(--chalk)',
                      color: density === d ? 'var(--chalk)' : 'var(--ink)',
                    }}
                    onClick={() => setDensity(d)}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
            <button type="button" className="t-btn t-btn--outline t-btn--sm" onClick={resetAllPaneWidths}>
              Reset All Split-Pane Widths
            </button>
          </div>
        </section>

        {/* 4. Notification Rules & Active Sessions */}
        <section className="t-card" style={{ padding: 24 }}>
          <span className="t-eyebrow">Alerts & Active Sessions</span>
          <h2 style={{ fontSize: 20, marginTop: 4, marginBottom: 14 }}>Match Cadence & Devices</h2>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
            <div>
              <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>Notify Above Fit %</label>
              <input
                className="t-input"
                type="number"
                min={50}
                max={95}
                value={notifThreshold}
                onChange={(e) => setNotifThreshold(Number(e.target.value))}
              />
            </div>
            <div>
              <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>Digest Cadence</label>
              <select
                className="t-select"
                value={notifCadence}
                onChange={(e) => setNotifCadence(e.target.value as 'instant' | 'daily' | 'off')}
              >
                <option value="instant">Instant Match Alerts</option>
                <option value="daily">Daily Quiet Digest</option>
                <option value="off">Muted</option>
              </select>
            </div>
          </div>

          <div className="t-label" style={{ marginBottom: 8 }}>Active Browser Sessions</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {sessions.map((s) => (
              <div
                key={s.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 10px',
                  border: '1px solid var(--n300)',
                  background: 'var(--chalk)',
                }}
              >
                <div>
                  <div style={{ fontSize: 13.5, fontWeight: 600 }}>{s.device}</div>
                  <div className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                    {s.location} · {s.lastActive}
                  </div>
                </div>
                {s.current ? (
                  <span className="t-chip t-chip--strong">This Device</span>
                ) : (
                  <button type="button" className="t-btn t-btn--outline t-btn--sm" onClick={() => revokeSession(s.id)}>
                    Revoke
                  </button>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* 5. Privacy & AI Telemetry Consents */}
        <section className="t-card" style={{ padding: 24 }}>
          <span className="t-eyebrow">Privacy & Telemetry Governance</span>
          <h2 style={{ fontSize: 20, marginTop: 4, marginBottom: 12 }}>AI & Analytics Consents</h2>
          <p style={{ fontSize: 13, color: 'var(--n500)', marginBottom: 14 }}>
            Control passive behavioral signal capture, ambient personalization, and gentle proactive prompts.
          </p>

          {[
            {
              key: 'analytics_micro_signals' as const,
              title: 'Micro-Signal UX Telemetry',
              desc: 'Anonymous UI engagement metrics (scroll depth, card dwell time; zero PII).',
            },
            {
              key: 'ai_passive_learning' as const,
              title: 'Ambient AI Passive Learning',
              desc: 'Allow Studio Coach to distill style & role drift memory facts in pgvector.',
            },
            {
              key: 'proactive_nudges' as const,
              title: 'Calm Proactive Suggestions',
              desc: 'Receive rate-limited match alerts and persona drift prompts.',
            },
          ].map((item) => {
            const on = consents[item.key];
            return (
              <div
                key={item.key}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: 12,
                  padding: '10px 0',
                  borderTop: '1px solid var(--n300)',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: 13.5 }}>{item.title}</div>
                  <div style={{ fontSize: 12, color: 'var(--n500)' }}>{item.desc}</div>
                </div>
                <button
                  type="button"
                  className={`t-btn t-btn--sm ${on ? 't-btn--ink' : 't-btn--outline'}`}
                  onClick={() => void handleConsentToggle(item.key)}
                >
                  {on ? 'Enabled' : 'Disabled'}
                </button>
              </div>
            );
          })}
        </section>

        {/* 6. AI Behavioral Memory Inspector */}
        <section className="t-card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, gap: 10 }}>
            <div>
              <span className="t-eyebrow">Ambient Intelligence Inspector</span>
              <h2 style={{ fontSize: 20, marginTop: 4 }}>Learned AI Memory & Suggestions</h2>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                type="button"
                className="t-btn t-btn--outline t-btn--sm"
                onClick={() => void loadPrivacyAndMemory()}
                disabled={memoryLoading}
              >
                {memoryLoading ? 'Loading…' : 'Refresh'}
              </button>
              <button
                type="button"
                className="t-btn t-btn--outline t-btn--sm"
                disabled={memoryFacts.length === 0 && proactiveSuggestions.length === 0}
                onClick={() => void handleClearMemory()}
              >
                Clear All Memory
              </button>
            </div>
          </div>

          <div className="t-label" style={{ marginBottom: 8 }}>
            Learned Behavioral Facts ({memoryFacts.length})
          </div>
          {memoryFacts.length === 0 ? (
            <div style={{ fontSize: 13, color: 'var(--n500)', padding: '10px 0' }}>
              No distilled behavioral memory facts stored yet.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 14 }}>
              {memoryFacts.map((fact) => (
                <div
                  key={fact.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: 10,
                    padding: '9px 11px',
                    border: '1px solid var(--n300)',
                    background: 'var(--chalk)',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                      <span className="t-chip">{fact.category}</span>
                      <span className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                        conf {Math.round(fact.confidence * 100)}%
                      </span>
                    </div>
                    <div style={{ fontSize: 13 }}>{fact.fact_text}</div>
                  </div>
                  <button
                    type="button"
                    className="t-btn t-btn--outline t-btn--sm"
                    onClick={() => void handleDeleteFact(fact.id)}
                  >
                    Forget
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="t-label" style={{ marginTop: 10, marginBottom: 8 }}>
            Proactive Suggestions ({proactiveSuggestions.length})
          </div>
          {proactiveSuggestions.length === 0 ? (
            <div style={{ fontSize: 13, color: 'var(--n500)' }}>No proactive suggestions queued.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {proactiveSuggestions.map((s) => (
                <div
                  key={s.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: 10,
                    padding: '9px 11px',
                    border: '1px solid var(--n300)',
                    background: 'var(--chalk)',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 13.5 }}>{s.title}</div>
                    <div style={{ fontSize: 12.5, color: 'var(--n500)' }}>{s.body}</div>
                  </div>
                  {s.status === 'pending' || !s.status ? (
                    <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                      <button
                        type="button"
                        className="t-btn t-btn--ink t-btn--sm"
                        onClick={() => void handleResolveSuggestion(s, 'clicked')}
                      >
                        Open
                      </button>
                      <button
                        type="button"
                        className="t-btn t-btn--outline t-btn--sm"
                        onClick={() => void handleResolveSuggestion(s, 'dismissed')}
                      >
                        Dismiss
                      </button>
                    </div>
                  ) : (
                    <span className="t-chip">{s.status}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {/* 7. Data Ownership & Danger Zone (Full Span) */}
        <section className="t-card" style={{ gridColumn: '1 / -1', padding: 24, borderColor: 'var(--alarm)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <span className="t-eyebrow" style={{ color: 'var(--alarm)' }}>GDPR Ownership & Permanent Deletion</span>
              <h2 style={{ fontSize: 20, marginTop: 4 }}>Export or Delete Your Master Vault</h2>
              <p style={{ fontSize: 13.5, color: 'var(--n500)', marginTop: 4 }}>
                Download your full JSON archive anytime. Account deletion erases your Master Profile, CVs, and credit history.
              </p>
            </div>

            <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <button type="button" className="t-btn t-btn--outline t-btn--sm" onClick={handleExportJson}>
                Export JSON Archive
              </button>
              <input
                className="t-input"
                style={{ width: 170 }}
                placeholder='Type "DELETE" to confirm'
                value={deleteConfirm}
                onChange={(e) => setDeleteConfirm(e.target.value)}
              />
              <button
                type="button"
                className="t-btn t-btn--alarm t-btn--sm"
                disabled={deleteConfirm !== 'DELETE'}
                onClick={async () => {
                  if (getAccessToken()) {
                    await AuthAPI.deleteAccount('DELETE').catch(() => {});
                  }
                  pushToast('Account erased cleanly. Signing out.');
                  signOut();
                }}
              >
                Permanently Delete
              </button>
            </div>
          </div>
        </section>
      </div>

      {twoFaModalMode && (
        <div className="t-drawer-backdrop" onClick={() => setTwoFaModalMode(null)}>
          <div
            className="t-card"
            style={{
              width: 'min(480px, 92vw)',
              margin: 'auto',
              padding: 26,
              zIndex: 60,
              background: 'var(--paper)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <span className="t-eyebrow">Two-Factor Authentication</span>
            <h3 style={{ fontSize: 22, marginTop: 4, marginBottom: 10 }}>
              {twoFaModalMode === 'enable' ? 'Configure Authenticator App (TOTP)' : 'Disable Two-Factor Auth'}
            </h3>

            {twoFaModalMode === 'enable' && twoFaSetupData && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 14 }}>
                <div style={{ fontSize: 13, color: 'var(--n700)' }}>
                  Add this setup key or `otpauth://` URI to Google Authenticator / 1Password, save your single-use recovery codes, then verify with a 6-digit code.
                </div>
                <div style={{ padding: 10, background: 'var(--chalk)', border: '1px solid var(--n300)' }}>
                  <div className="t-label">Manual Secret Key</div>
                  <div className="t-mono" style={{ fontSize: 13, wordBreak: 'break-all', marginTop: 2 }}>
                    {twoFaSetupData.secret}
                  </div>
                </div>
                <div style={{ padding: 10, background: 'var(--chalk)', border: '1px solid var(--n300)' }}>
                  <div className="t-label">OTPAuth URI</div>
                  <div className="t-mono" style={{ fontSize: 11, wordBreak: 'break-all', marginTop: 2 }}>
                    {twoFaSetupData.otpauth_uri}
                  </div>
                </div>
                {twoFaSetupData.recovery_codes?.length > 0 && (
                  <div style={{ padding: 10, background: 'var(--chalk)', border: '1px solid var(--n300)' }}>
                    <div className="t-label">Single-Use Recovery Codes</div>
                    <div className="t-mono" style={{ fontSize: 11.5, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, marginTop: 4 }}>
                      {twoFaSetupData.recovery_codes.map((rc) => (
                        <span key={rc}>{rc}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <form onSubmit={(e) => void handleConfirm2faModal(e)} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label className="t-label" style={{ display: 'block', marginBottom: 5 }}>
                  {twoFaModalMode === 'enable' ? '6-Digit Verification Code' : 'Current 6-Digit Code (or Recovery Code)'}
                </label>
                <input
                  className="t-input t-mono"
                  value={twoFaCodeInput}
                  onChange={(e) => setTwoFaCodeInput(e.target.value)}
                  placeholder="123456"
                  autoFocus
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                <button type="button" className="t-btn t-btn--outline t-btn--sm" onClick={() => setTwoFaModalMode(null)}>
                  Cancel
                </button>
                <button type="submit" className="t-btn t-btn--primary t-btn--sm" disabled={twoFaBusy || !twoFaCodeInput.trim()}>
                  {twoFaBusy ? 'Verifying…' : twoFaModalMode === 'enable' ? 'Verify & Activate 2FA' : 'Confirm Disable'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
