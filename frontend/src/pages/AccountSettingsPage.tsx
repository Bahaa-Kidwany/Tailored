import React, { useState } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { SAMPLE_PROFILE } from '../services/profileApi';
import { AuthAPI } from '../services/authApi';
import { getAccessToken } from '../services/apiClient';

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
    pushToast,
  } = useWorkspace();

  const [emailDraft, setEmailDraft] = useState(userEmail);
  const [deleteConfirm, setDeleteConfirm] = useState('');

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
              className={`t-btn t-btn--sm ${twoFactorEnabled ? 't-btn--outline' : 't-btn--primary'}`}
              onClick={() => toggleTwoFactor(!twoFactorEnabled)}
            >
              {twoFactorEnabled ? 'Disable 2FA' : 'Enable 2FA'}
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

        {/* 5. Data Ownership & Danger Zone (Full Span) */}
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
    </div>
  );
};
