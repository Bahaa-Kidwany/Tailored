import React, { useState, useEffect } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { AtelierFrenchCurveBackdrop, BrandLockup } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';

/**
 * 03 — Auth: Login & Register (/login, /register) — Atelier V2
 */
export const AuthPage: React.FC<{ initialMode: 'signin' | 'signup' }> = ({ initialMode }) => {
  const {
    navigateTo,
    signIn,
    registerAccount,
    pendingIntent,
    isAuthenticated,
    defaultHomeRoute,
    dir,
  } = useWorkspace();

  const mode = initialMode;
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated && !pendingIntent) {
      navigateTo(defaultHomeRoute);
    }
  }, [isAuthenticated, pendingIntent, navigateTo, defaultHomeRoute]);

  const switchMode = (next: 'signin' | 'signup') => {
    setErrorMsg(null);
    navigateTo(next === 'signin' ? '/login' : '/register');
  };

  const passScore =
    (password.length >= 8 ? 1 : 0) +
    (/[0-9]/.test(password) ? 1 : 0) +
    (/[^a-zA-Z0-9]/.test(password) ? 1 : 0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !email.includes('@')) {
      setErrorMsg('Please enter a valid email address.');
      return;
    }
    if (password.length < 6) {
      setErrorMsg('Password must be at least 6 characters.');
      return;
    }
    if (mode === 'signin') {
      signIn(email.trim());
    } else {
      registerAccount(fullName.trim() || 'Mostafa Ibrahim', email.trim());
    }
  };

  return (
    <div className="t-auth-shell t-cv-studio-v2">
      <header className="t-studio-bar">
        <button
          type="button"
          onClick={() => navigateTo('/')}
          style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: 0, display: 'flex' }}
          aria-label="Tailored Command Center"
        >
          <BrandLockup variant="horizontal" mode="knock" size={24} color="var(--chalk)" dir={dir} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            type="button"
            className="t-atelier-topbar-ghost"
            onClick={() => navigateTo('/explore')}
          >
            <TailoredIcon name="radar" size={13} color="var(--chalk)" />
            <span>Explore Live Jobs</span>
          </button>
          <button
            type="button"
            className="t-atelier-pair-btn"
            onClick={() => navigateTo('/')}
          >
            <TailoredIcon name="back" size={13} color="var(--chalk)" />
            <span>Command Center</span>
          </button>
        </div>
      </header>

      <div className="t-auth-stage">
        <AtelierFrenchCurveBackdrop />

        <div className="t-auth-center">
          {/* Contextual Intent Reminder (Only if user arrived from a gated job/CV action) */}
          {pendingIntent && (
            <aside className="t-auth-intent-card">
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, marginBottom: 8 }}>
                <TailoredIcon name="scissors" size={13} color="var(--kraft)" />
                <span className="t-mono" style={{ fontSize: 10.5, fontWeight: 600, letterSpacing: '0.09em', color: 'var(--kraft)' }}>
                  QUEUED ACTION
                </span>
              </div>
              <h2 style={{ fontFamily: 'var(--font-voice)', fontSize: 23, fontWeight: 540, margin: 0, color: 'var(--chalk)', letterSpacing: '-0.02em' }}>
                Ready right after setup.
              </h2>
              <p style={{ fontSize: 13.5, color: 'rgba(229, 224, 218, 0.78)', marginTop: 8, marginBottom: 0, lineHeight: 1.5 }}>
                {pendingIntent.label || 'Your selected opportunity'}
              </p>
              <div className="t-stitch" style={{ margin: '16px 0', opacity: 0.2 }} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13, color: 'rgba(229, 224, 218, 0.88)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="t-signal-up" aria-hidden="true" />
                  <span>Build profile or import CV</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="t-signal-up" aria-hidden="true" />
                  <span>Claim 2 free non-expiring credits</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="t-signal-up" aria-hidden="true" />
                  <span>Resume directly on your target</span>
                </div>
              </div>
            </aside>
          )}

          {/* Single-Focus Floating Paper Atelier Auth Card */}
          <section className="t-auth-card" aria-label={mode === 'signin' ? 'Sign In' : 'Create Account'}>
            {/* Sliding Mode Switcher */}
            <div className="t-auth-seg" role="tablist" aria-label="Authentication mode">
              <span
                aria-hidden="true"
                className="t-auth-seg-thumb"
                style={{ transform: `translateX(${mode === 'signin' ? 0 : 100}%)` }}
              />
              <button
                type="button"
                role="tab"
                aria-selected={mode === 'signin'}
                className={`t-auth-seg-btn ${mode === 'signin' ? 't-auth-seg-btn--active' : ''}`}
                onClick={() => switchMode('signin')}
              >
                Sign In
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={mode === 'signup'}
                className={`t-auth-seg-btn ${mode === 'signup' ? 't-auth-seg-btn--active' : ''}`}
                onClick={() => switchMode('signup')}
              >
                Create Account
              </button>
            </div>

            <h1 style={{ fontFamily: 'var(--font-voice)', fontSize: 30, fontWeight: 540, letterSpacing: '-0.025em', color: 'var(--ink)', margin: 0 }}>
              {mode === 'signin' ? (
                <>
                  Welcome <em>back.</em>
                </>
              ) : (
                <>
                  Start with <em>2 free credits.</em>
                </>
              )}
            </h1>
            <p style={{ fontSize: 13.5, color: 'var(--n500)', marginTop: 6, marginBottom: 18, lineHeight: 1.45 }}>
              {mode === 'signin'
                ? 'Continue to your dashboard, CV studio, and application pipeline.'
                : 'Zero card required. Credits never expire.'}
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
              <button
                type="button"
                onClick={() =>
                  mode === 'signin'
                    ? signIn('mostafa.eng@tailored.atelier')
                    : registerAccount('Mostafa Ibrahim', 'mostafa.eng@tailored.atelier')
                }
                className="t-auth-sso-btn"
              >
                <TailoredIcon name="globe" size={14} color="var(--ink)" />
                <span>Continue with Google</span>
              </button>
              <button
                type="button"
                onClick={() =>
                  mode === 'signin'
                    ? signIn('mostafa.eng@tailored.atelier')
                    : registerAccount('Mostafa Ibrahim', 'mostafa.eng@tailored.atelier')
                }
                className="t-auth-sso-btn"
              >
                <TailoredIcon name="user" size={14} color="var(--ink)" />
                <span>Continue with LinkedIn (Imports Headline)</span>
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '14px 0' }}>
              <div className="t-stitch" style={{ opacity: 0.25 }} />
              <span style={{ fontSize: 12, color: 'var(--n500)', whiteSpace: 'nowrap' }}>
                or continue with email
              </span>
              <div className="t-stitch" style={{ opacity: 0.25 }} />
            </div>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 13 }}>
              {mode === 'signup' && (
                <div>
                  <label htmlFor="auth-full-name" className="t-auth-field-label">
                    Full name
                  </label>
                  <input
                    id="auth-full-name"
                    className="t-auth-input"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Mostafa Ibrahim"
                    autoFocus
                  />
                </div>
              )}

              <div>
                <label htmlFor="auth-email" className="t-auth-field-label">
                  Email address
                </label>
                <input
                  id="auth-email"
                  type="email"
                  className="t-auth-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="mostafa@example.com"
                  autoFocus={mode === 'signin'}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
                  <label htmlFor="auth-password" className="t-auth-field-label" style={{ marginBottom: 0 }}>
                    Password
                  </label>
                  {mode === 'signin' && (
                    <button
                      type="button"
                      onClick={() => navigateTo(`/forgot-password${email ? `?email=${encodeURIComponent(email)}` : ''}`)}
                      className="t-auth-link-btn"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>

                <div className="t-auth-pass-wrap">
                  <input
                    id="auth-password"
                    type={showPass ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="t-auth-pass-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass((v) => !v)}
                    className="t-atelier-icon-btn"
                    aria-label={showPass ? 'Hide password' : 'Show password'}
                    title={showPass ? 'Hide password' : 'Show password'}
                  >
                    <TailoredIcon name={showPass ? 'hide' : 'eye'} size={14} color="var(--n700)" />
                  </button>
                </div>

                {mode === 'signup' && password.length > 0 && (
                  <div
                    className="t-mono"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 6,
                      fontSize: 11,
                      marginTop: 6,
                      color: passScore >= 2 ? 'var(--green)' : 'var(--ink)',
                    }}
                  >
                    {passScore >= 2 ? (
                      <span className="t-signal-up" aria-hidden="true" />
                    ) : (
                      <span className="t-atelier-fit-dot" style={{ background: 'var(--amber)' }} />
                    )}
                    <span>
                      Strength: {passScore >= 3 ? 'Strong' : passScore === 2 ? 'Good' : 'Use 8+ chars & a number'}
                    </span>
                  </div>
                )}
              </div>

              {errorMsg && (
                <div
                  role="alert"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '9px 12px',
                    borderRadius: '4px 10px 4px 4px',
                    background: 'rgba(143, 29, 44, 0.09)',
                    color: 'var(--alarm)',
                    fontSize: 13,
                    fontWeight: 500,
                  }}
                >
                  <span className="t-signal-down" aria-hidden="true" />
                  <span>{errorMsg}</span>
                </div>
              )}

              <button
                type="submit"
                className="t-atelier-btn-primary"
                style={{ width: '100%', justifyContent: 'center', padding: '11px 16px', marginTop: 4, fontSize: 14 }}
              >
                {mode === 'signin' ? 'Sign In' : 'Create Account & Build Profile'}
              </button>

              <div style={{ fontSize: 12, color: 'var(--n500)', textAlign: 'center', marginTop: 4 }}>
                Private by design — your data is never sold.{' '}
                <button type="button" onClick={() => navigateTo('/privacy')} className="t-auth-link-btn">
                  Privacy
                </button>{' '}
                ·{' '}
                <button type="button" onClick={() => navigateTo('/terms')} className="t-auth-link-btn">
                  Terms
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
};
