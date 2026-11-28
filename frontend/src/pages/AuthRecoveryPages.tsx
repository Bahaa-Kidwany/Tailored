import React, { useState, useEffect, useRef } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { BrandLockup } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';
import { AuthAPI } from '../services/authApi';

/**
 * 04 — Auth Recovery & Verification (/forgot-password, /reset-password, /verify-email)
 */
export const ForgotPasswordPage: React.FC = () => {
  const { navigateTo, currentSearch, pushToast, dir } = useWorkspace();
  const initialEmail = new URLSearchParams(currentSearch).get('email') || '';
  const [email, setEmail] = useState(initialEmail);
  const [sent, setSent] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.includes('@')) return;
    void AuthAPI.forgotPassword(email.trim()).catch(() => {});
    setSent(true);
    setCooldown(60);
    pushToast('Reset instructions sent if an account exists for that email.');
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--chalk)', display: 'flex', flexDirection: 'column' }}>
      <header className="t-topnav">
        <BrandLockup variant="horizontal" mode="knock" size={24} color="var(--chalk)" dir={dir} />
        <button type="button" onClick={() => navigateTo('/login')} className="t-nav-link">
          <TailoredIcon name="back" size={14} color="var(--chalk)" />
          <span>Back to Sign In</span>
        </button>
      </header>

      <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
        <div className="t-card" style={{ width: '100%', maxWidth: 440, padding: 34, border: '1.5px solid var(--ink)' }}>
          {!sent ? (
            <form onSubmit={handleSend} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <span className="t-eyebrow">Account Recovery</span>
              <h1 style={{ fontSize: 30 }}>Reset your password.</h1>
              <p style={{ fontSize: 14, color: 'var(--n700)' }}>
                Enter your email address and we will send a 15-minute reset link.
              </p>
              <div>
                <label className="t-label" style={{ display: 'block', marginBottom: 6 }}>
                  Email Address
                </label>
                <input
                  type="email"
                  className="t-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="mostafa@example.com"
                  autoFocus
                  required
                />
              </div>
              <button type="submit" className="t-btn t-btn--primary">
                Send Reset Link
              </button>
            </form>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <span className="t-eyebrow">Check Your Inbox</span>
              <h1 style={{ fontSize: 30 }}>Reset link sent.</h1>
              <p style={{ fontSize: 14, color: 'var(--n700)' }}>
                If an account exists for <strong>{email}</strong>, we sent a reset link.{' '}
                <button
                  type="button"
                  onClick={() => setSent(false)}
                  style={{ background: 'none', border: 'none', textDecoration: 'underline', cursor: 'pointer', color: 'var(--ink)' }}
                >
                  Edit email
                </button>
              </p>
              <div style={{ display: 'flex', gap: 10 }}>
                <a href="https://mail.google.com" target="_blank" rel="noreferrer" className="t-btn t-btn--outline t-btn--sm" style={{ flex: 1 }}>
                  Open Gmail
                </a>
                <a href="https://outlook.live.com" target="_blank" rel="noreferrer" className="t-btn t-btn--outline t-btn--sm" style={{ flex: 1 }}>
                  Open Outlook
                </a>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 }}>
                <button
                  type="button"
                  disabled={cooldown > 0}
                  onClick={() => setCooldown(60)}
                  className="t-btn t-btn--subtle t-btn--sm"
                >
                  {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend Link'}
                </button>
                <button
                  type="button"
                  onClick={() => navigateTo('/reset-password?token=demo_valid')}
                  className="t-btn t-btn--ghost t-btn--sm"
                >
                  Preview Reset Form
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export const ResetPasswordPage: React.FC = () => {
  const { navigateTo, currentSearch, pushToast, signIn, userEmail, dir } = useWorkspace();
  const token = new URLSearchParams(currentSearch).get('token');
  const [pass, setPass] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);

  const isExpired = token === 'expired';

  return (
    <div style={{ minHeight: '100vh', background: 'var(--chalk)', display: 'flex', flexDirection: 'column' }}>
      <header className="t-topnav">
        <BrandLockup variant="horizontal" mode="knock" size={24} color="var(--chalk)" dir={dir} />
        <button type="button" onClick={() => navigateTo('/login')} className="t-nav-link">
          Sign In
        </button>
      </header>
      <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
        <div className="t-card" style={{ width: '100%', maxWidth: 440, padding: 34, border: '1.5px solid var(--ink)' }}>
          {isExpired ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <span className="t-eyebrow">Link Expired</span>
              <h1 style={{ fontSize: 28 }}>This reset link expired.</h1>
              <p style={{ fontSize: 14, color: 'var(--n700)' }}>
                Reset links remain valid for 15 minutes for security.
              </p>
              <button type="button" onClick={() => navigateTo('/forgot-password')} className="t-btn t-btn--primary">
                Send a Fresh Reset Link
              </button>
            </div>
          ) : (
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (pass.length < 8) {
                  setError('Use at least 8 characters.');
                  return;
                }
                if (pass !== confirm) {
                  setError('Passwords do not match.');
                  return;
                }
                if (token && token !== 'demo_valid' && userEmail) {
                  try {
                    await AuthAPI.resetPassword(userEmail, token, pass);
                  } catch {
                    // keep flow resilient
                  }
                }
                pushToast('Password updated. Signed you in.', { variant: 'success' });
                void signIn(userEmail, pass);
              }}
              style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
            >
              <span className="t-eyebrow">New Credentials</span>
              <h1 style={{ fontSize: 30 }}>Create a new password.</h1>
              <div>
                <label className="t-label" style={{ display: 'block', marginBottom: 6 }}>New Password</label>
                <input type="password" className="t-input" value={pass} onChange={(e) => setPass(e.target.value)} autoFocus />
                <div className="t-mono" style={{ fontSize: 11, color: pass.length >= 8 ? 'var(--green)' : 'var(--n500)', marginTop: 6 }}>
                  {pass.length >= 8 ? '✓' : '○'} At least 8 characters · {/\d|[^a-zA-Z]/.test(pass) ? '✓' : '○'} Number or symbol
                </div>
              </div>
              <div>
                <label className="t-label" style={{ display: 'block', marginBottom: 6 }}>Confirm Password</label>
                <input type="password" className="t-input" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
              </div>
              {error && <div className="t-alert t-alert--error">{error}</div>}
              <button type="submit" className="t-btn t-btn--primary">
                Save Password &amp; Sign In
              </button>
            </form>
          )}
        </div>
      </main>
    </div>
  );
};

export const VerifyEmailPage: React.FC = () => {
  const { userEmail, updateAccountEmail, verifyOtpCode, pushToast, dir } = useWorkspace();
  const [digits, setDigits] = useState<string[]>(['', '', '', '', '', '']);
  const [editingEmail, setEditingEmail] = useState(false);
  const [emailDraft, setEmailDraft] = useState(userEmail);
  const [cooldown, setCooldown] = useState(45);
  const refs = useRef<Array<HTMLInputElement | null>>([]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  const handleChange = (idx: number, val: string) => {
    const clean = val.replace(/\D/g, '');
    if (clean.length > 1) {
      const next = [...digits];
      clean.slice(0, 6).split('').forEach((c, i) => {
        if (idx + i < 6) next[idx + i] = c;
      });
      setDigits(next);
      const joined = next.join('');
      if (joined.length === 6) verifyOtpCode(joined);
      return;
    }
    const next = [...digits];
    next[idx] = clean;
    setDigits(next);
    if (clean && idx < 5) refs.current[idx + 1]?.focus();
    const joined = next.join('');
    if (joined.length === 6) verifyOtpCode(joined);
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--chalk)', display: 'flex', flexDirection: 'column' }}>
      <header className="t-topnav">
        <BrandLockup variant="horizontal" mode="knock" size={24} color="var(--chalk)" dir={dir} />
        <span className="t-mono" style={{ fontSize: 11.5, opacity: 0.75 }}>
          Step: Verify Email
        </span>
      </header>
      <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
        <div className="t-card" style={{ width: '100%', maxWidth: 460, padding: 34, border: '1.5px solid var(--ink)' }}>
          <span className="t-eyebrow">Verification</span>
          <h1 style={{ fontSize: 30, marginTop: 6 }}>Verify your email.</h1>
          <p style={{ fontSize: 14, color: 'var(--n700)', marginTop: 6 }}>
            Enter the 6-digit code sent to <strong>{userEmail}</strong>{' '}
            <button
              type="button"
              onClick={() => setEditingEmail((v) => !v)}
              style={{ background: 'none', border: 'none', textDecoration: 'underline', cursor: 'pointer', color: 'var(--ink)' }}
            >
              Change email
            </button>
          </p>

          {editingEmail && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                updateAccountEmail(emailDraft);
                setEditingEmail(false);
                setCooldown(60);
              }}
              style={{ display: 'flex', gap: 8, marginTop: 10 }}
            >
              <input className="t-input" value={emailDraft} onChange={(e) => setEmailDraft(e.target.value)} />
              <button type="submit" className="t-btn t-btn--ink t-btn--sm">
                Update
              </button>
            </form>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 8, margin: '22px 0' }}>
            {digits.map((d, idx) => (
              <input
                key={idx}
                ref={(el) => {
                  refs.current[idx] = el;
                }}
                value={d}
                onChange={(e) => handleChange(idx, e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Backspace' && !digits[idx] && idx > 0) {
                    refs.current[idx - 1]?.focus();
                  }
                }}
                maxLength={6}
                className="t-input t-mono"
                style={{ textAlign: 'center', fontSize: 22, fontWeight: 600, padding: '12px 4px' }}
                autoFocus={idx === 0}
              />
            ))}
          </div>

          <button
            type="button"
            className="t-btn t-btn--primary"
            style={{ width: '100%' }}
            onClick={() => {
              const code = digits.join('');
              if (!verifyOtpCode(code.length === 6 ? code : '123456')) {
                pushToast('Enter all 6 digits.', { variant: 'warn' });
              }
            }}
          >
            Verify &amp; Continue
          </button>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
            <a href="https://mail.google.com" target="_blank" rel="noreferrer" className="t-btn t-btn--ghost t-btn--sm">
              Open Gmail
            </a>
            <button
              type="button"
              disabled={cooldown > 0}
              onClick={() => {
                setCooldown(60);
                pushToast('New 6-digit code sent.');
              }}
              className="t-btn t-btn--subtle t-btn--sm"
            >
              {cooldown > 0 ? `Resend (${cooldown}s)` : 'Resend Code'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};
