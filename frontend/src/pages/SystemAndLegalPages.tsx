import React from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { BrandLockup, LayplanPattern } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';
import { SAMPLE_PROFILE } from '../services/profileApi';

const SUGGESTED_ROUTES = [
  { route: '/dashboard', keywords: ['dash', 'home', 'over'] },
  { route: '/radar', keywords: ['rad', 'job', 'find', 'search'] },
  { route: '/radar?tab=saved', keywords: ['int', 'save', 'bench', 'short'] },
  { route: '/studio', keywords: ['stud', 'cv', 'tailor', 'edit', 'lib', 'cvs', 'doc'] },
  { route: '/cover-letters', keywords: ['cov', 'let', 'mail'] },
  { route: '/pipeline', keywords: ['pip', 'crm', 'track', 'app'] },
  { route: '/profile', keywords: ['prof', 'vault', 'master'] },
  { route: '/plans', keywords: ['plan', 'cred', 'pay', 'bill'] },
  { route: '/account', keywords: ['acc', 'set', 'sec'] },
];

export const NotFoundPage: React.FC = () => {
  const { currentPath, navigateTo, dir } = useWorkspace();
  const q = currentPath.toLowerCase();
  const smartMatch =
    SUGGESTED_ROUTES.find((r) => r.keywords.some((k) => q.includes(k)))?.route || '/dashboard';

  return (
    <div style={{ minHeight: '100vh', background: 'var(--chalk)', color: 'var(--ink)' }}>
      <header
        style={{
          height: 52,
          background: 'var(--ink)',
          color: 'var(--chalk)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 28px',
        }}
      >
        <button
          type="button"
          onClick={() => navigateTo('/')}
          style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex' }}
        >
          <BrandLockup variant="horizontal" mode="knock" size={24} color="var(--chalk)" dir={dir} />
        </button>
        <button type="button" className="t-btn t-btn--chalk-outline t-btn--sm" onClick={() => navigateTo('/dashboard')}>
          Dashboard
        </button>
      </header>

      <main style={{ maxWidth: 660, margin: '64px auto', padding: '0 24px' }}>
        <div className="t-card" style={{ padding: '38px 36px', position: 'relative', overflow: 'hidden' }}>
          <LayplanPattern opacity={0.06} color="var(--ink)" />
          <div style={{ position: 'relative', zIndex: 2 }}>
            <span className="t-eyebrow">Error 404 · Broken Pattern Seam</span>
            <h1 style={{ fontSize: 38, marginTop: 8, marginBottom: 10 }}>
              We couldn&apos;t stitch <span className="t-mono" style={{ fontSize: 28 }}>{currentPath}</span>.
            </h1>
            <p style={{ color: 'var(--n500)', fontSize: 15, lineHeight: 1.6, marginBottom: 24 }}>
              We checked our atelier routes and that page doesn&apos;t exist. Your Master Profile, saved CVs, and credit balance remain untouched.
            </p>

            <div className="t-alert" style={{ marginBottom: 22 }}>
              <div className="t-label" style={{ marginBottom: 4 }}>Did you mean</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="t-mono" style={{ fontWeight: 600 }}>{smartMatch}</span>
                <button type="button" className="t-btn t-btn--primary t-btn--sm" onClick={() => navigateTo(smartMatch)}>
                  Jump to {smartMatch} →
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button type="button" className="t-btn t-btn--ink" onClick={() => navigateTo('/dashboard')}>
                Dashboard
              </button>
              <button type="button" className="t-btn t-btn--outline" onClick={() => navigateTo('/radar')}>
                Job Radar
              </button>
              <button type="button" className="t-btn t-btn--outline" onClick={() => navigateTo('/studio')}>
                CV Studio
              </button>
              <button type="button" className="t-btn t-btn--outline" onClick={() => navigateTo('/pipeline')}>
                Pipeline
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export const ServerErrorView: React.FC<{ onReset?: () => void }> = ({ onReset }) => {
  const { currentProfile, navigateTo, dir } = useWorkspace();

  const downloadBackup = () => {
    const data = JSON.stringify(currentProfile?.profile || SAMPLE_PROFILE, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'tailored_recovery_backup.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--chalk)', color: 'var(--ink)' }}>
      <header
        style={{
          height: 52,
          background: 'var(--ink)',
          color: 'var(--chalk)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 28px',
        }}
      >
        <BrandLockup variant="horizontal" mode="knock" size={24} color="var(--chalk)" dir={dir} />
        <button type="button" className="t-btn t-btn--chalk-outline t-btn--sm" onClick={() => navigateTo('/dashboard')}>
          Dashboard
        </button>
      </header>
      <div style={{ padding: '64px 24px' }}>
        <div className="t-card" style={{ maxWidth: 620, margin: '0 auto', padding: '36px 32px', borderColor: 'var(--alarm)' }}>
          <span className="t-eyebrow" style={{ color: 'var(--alarm)' }}>Error 500 · Safe Interruption</span>
          <h1 style={{ fontSize: 32, marginTop: 8, marginBottom: 10 }}>
            Something interrupted this stitch.
          </h1>
          <p style={{ color: 'var(--n700)', fontSize: 15, lineHeight: 1.6, marginBottom: 18 }}>
            <strong>0 credits were deducted.</strong> Our side failed cleanly and your unsaved Master Profile &amp; drafts are intact in local storage.
          </p>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button
              type="button"
              className="t-btn t-btn--primary"
              onClick={() => {
                if (onReset) onReset();
                else window.location.assign('/dashboard');
              }}
            >
              Reload Safely
            </button>
            <button type="button" className="t-btn t-btn--outline" onClick={downloadBackup}>
              Download Local JSON Backup
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

interface BoundaryState {
  hasError: boolean;
}

export class ServerErrorBoundary extends React.Component<{ children: React.ReactNode }, BoundaryState> {
  state: BoundaryState = { hasError: false };

  static getDerivedStateFromError(): BoundaryState {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <ServerErrorView onReset={() => this.setState({ hasError: false })} />;
    }
    return this.props.children;
  }
}

export const MaintenancePage: React.FC = () => {
  const { navigateTo, dir } = useWorkspace();
  return (
    <div style={{ minHeight: '100vh', background: 'var(--chalk)', color: 'var(--ink)' }}>
      <header
        style={{
          height: 52,
          background: 'var(--ink)',
          color: 'var(--chalk)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 28px',
        }}
      >
        <BrandLockup variant="horizontal" mode="knock" size={24} color="var(--chalk)" dir={dir} />
        <button type="button" className="t-btn t-btn--chalk-outline t-btn--sm" onClick={() => navigateTo('/studio')}>
          Cached CVs
        </button>
      </header>
      <div style={{ padding: '72px 24px' }}>
        <div className="t-card" style={{ maxWidth: 600, margin: '0 auto', padding: '36px 32px' }}>
          <span className="t-eyebrow">Scheduled Maintenance</span>
          <h1 style={{ fontSize: 32, marginTop: 8, marginBottom: 10 }}>
            Tailored Atelier is upgrading LaTeX workers.
          </h1>
          <p style={{ color: 'var(--n700)', fontSize: 14.5, lineHeight: 1.6, marginBottom: 20 }}>
            We are tuning our PDF compilation engines. Estimated return: under 12 minutes. Existing cached drafts remain readable below.
          </p>
          <button type="button" className="t-btn t-btn--ink" onClick={() => navigateTo('/studio')}>
            Open Cached Saved CVs
          </button>
        </div>
      </div>
    </div>
  );
};

export const OfflineFallbackPage: React.FC = () => {
  const { navigateTo, isOnline, dir } = useWorkspace();
  return (
    <div style={{ minHeight: '100vh', background: 'var(--chalk)', color: 'var(--ink)' }}>
      <header
        style={{
          height: 52,
          background: 'var(--ink)',
          color: 'var(--chalk)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 28px',
        }}
      >
        <BrandLockup variant="horizontal" mode="knock" size={24} color="var(--chalk)" dir={dir} />
        <button type="button" className="t-btn t-btn--chalk-outline t-btn--sm" onClick={() => navigateTo('/dashboard')}>
          Dashboard
        </button>
      </header>
      <div style={{ padding: '72px 24px' }}>
        <div className="t-card" style={{ maxWidth: 620, margin: '0 auto', padding: '36px 32px', borderLeft: '4px solid var(--amber)' }}>
          <span className="t-eyebrow">Offline Resilience Mode</span>
          <h1 style={{ fontSize: 32, marginTop: 8, marginBottom: 10 }}>
            {isOnline ? 'Connection restored.' : 'You are currently offline.'}
          </h1>
          <p style={{ color: 'var(--n700)', fontSize: 14.5, lineHeight: 1.6, marginBottom: 18 }}>
            Your CV edits, Pipeline tracking, and Master Profile changes are stored locally and will sync cleanly when connection returns. AI Coach streaming and live job scrapers are temporarily paused.
          </p>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button type="button" className="t-btn t-btn--primary" onClick={() => navigateTo('/dashboard')}>
              Retry &amp; Open Dashboard
            </button>
            <button type="button" className="t-btn t-btn--outline" onClick={() => navigateTo('/studio')}>
              Open Cached Saved CVs
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export const LegalDocPage: React.FC<{ mode: 'privacy' | 'terms' }> = ({ mode }) => {
  const { navigateTo, dir } = useWorkspace();
  const isPrivacy = mode === 'privacy';

  return (
    <div style={{ minHeight: '100vh', background: 'var(--chalk)', color: 'var(--ink)' }}>
      <header
        style={{
          height: 52,
          background: 'var(--ink)',
          color: 'var(--chalk)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 28px',
        }}
      >
        <button
          type="button"
          onClick={() => navigateTo('/')}
          style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex' }}
        >
          <BrandLockup variant="horizontal" mode="knock" size={24} color="var(--chalk)" dir={dir} />
        </button>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            type="button"
            className="t-btn t-btn--ghost t-btn--sm"
            style={{ color: 'var(--chalk)' }}
            onClick={() => navigateTo(isPrivacy ? '/terms' : '/privacy')}
          >
            {isPrivacy ? 'Terms of Service' : 'Privacy Policy'}
          </button>
          <button type="button" className="t-btn t-btn--chalk-outline t-btn--sm" onClick={() => navigateTo('/dashboard')}>
            Workspace
          </button>
        </div>
      </header>

      <main style={{ maxWidth: 980, margin: '0 auto', padding: '38px 24px 80px', display: 'grid', gridTemplateColumns: '220px 1fr', gap: 36 }}>
        <aside style={{ position: 'sticky', top: 24, alignSelf: 'start' }}>
          <span className="t-eyebrow">Contents</span>
          <ul style={{ listStyle: 'none', padding: 0, marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13.5 }}>
            <li><a href="#guarantee" style={{ color: 'var(--ink)', textDecoration: 'none', fontWeight: 600 }}>1. Plain-English Guarantee</a></li>
            <li><a href="#truth" style={{ color: 'var(--n700)', textDecoration: 'none' }}>2. Anti-Fabrication Policy</a></li>
            <li><a href="#credits" style={{ color: 'var(--n700)', textDecoration: 'none' }}>3. Credit & Refund Fairness</a></li>
            <li><a href="#export" style={{ color: 'var(--n700)', textDecoration: 'none' }}>4. Data Export & Deletion</a></li>
          </ul>
        </aside>

        <article>
          <span className="t-eyebrow">{isPrivacy ? 'Privacy Policy · Effective 2026' : 'Terms of Service · Effective 2026'}</span>
          <h1 style={{ fontSize: 38, marginTop: 6, marginBottom: 18 }}>
            {isPrivacy ? 'Your career record belongs strictly to you.' : 'Clear, honest terms with zero subscription traps.'}
          </h1>

          {/* Plain-English Tailoring Guarantee Box */}
          <div id="guarantee" className="t-card" style={{ padding: '22px 24px', borderLeft: '4px solid var(--thread)', marginBottom: 28 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <TailoredIcon name="shield" size={16} color="var(--thread)" />
              <span className="t-label">Plain-English Tailoring Guarantee</span>
            </div>
            <p style={{ margin: 0, fontSize: 14.5, lineHeight: 1.6 }}>
              We never sell candidate profiles to third-party recruiters, we never train public foundation models on your private resume data, and Tailored Studio refuses to invent unverified jobs, degrees, or employers on your CV.
            </p>
          </div>

          <section id="truth" style={{ marginBottom: 24 }}>
            <h2 style={{ fontSize: 22, marginBottom: 8 }}>2. Fact-Locked Tailoring Architecture</h2>
            <p style={{ color: 'var(--n700)', lineHeight: 1.65 }}>
              Every AI-rewritten summary and experience bullet is verified against your Master Profile Vault. If a job asks for a metric or framework not found in your work history, Coach asks you first rather than guessing.
            </p>
          </section>

          <section id="credits" style={{ marginBottom: 24 }}>
            <h2 style={{ fontSize: 22, marginBottom: 8 }}>3. Non-Expiring Credits & Zero Double-Charges</h2>
            <p style={{ color: 'var(--n700)', lineHeight: 1.65 }}>
              Purchased credits never expire. Unlocking a CV (1 credit) or Cover Letter (1 credit) for a job ID grants unlimited free edits, AI Coach refinements, and PDF/.tex exports for that job forever. Failed runs automatically cost 0 credits.
            </p>
          </section>

          <section id="export">
            <h2 style={{ fontSize: 22, marginBottom: 8 }}>4. Immediate Portability & Permanent Deletion</h2>
            <p style={{ color: 'var(--n700)', lineHeight: 1.65 }}>
              You can export your complete Master Profile JSON archive or permanently erase all stored records inside Account Settings at any moment.
            </p>
          </section>
        </article>
      </main>
    </div>
  );
};
