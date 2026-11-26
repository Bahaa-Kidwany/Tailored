import React, { useRef, useState } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { AtelierFrenchCurveBackdrop, BrandLockup } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';
import { ProfileAPI } from '../services/profileApi';
import { FeatureShowcaseSection } from '../components/landing/LandingFeatureDemos';
import { useRevealOnScroll } from '../components/landing/useRevealOnScroll';

/**
 * 01 — Marketing Landing (/)
 * Follows ATELIER_V2_UI_ENHANCEMENT_GUIDE.md:
 * - Solid pattern-free 54px --ink header with sentence-case IBM Plex Sans controls
 * - AtelierFrenchCurveBackdrop on continuous --ink hero & closing CTA (zero spinning elements, zero grid)
 * - Semantic directional arrows (▲ green positives, ▼ red negatives)
 * - Scroll-revealed large-format real workspace video showcases
 */
export const LandingPage: React.FC = () => {
  const {
    navigateTo,
    isAuthenticated,
    setPendingIntent,
    ingestJobUrlOrText,
    saveProfile,
    currentProfile,
    pushToast,
    dir,
  } = useWorkspace();

  const [commandInput, setCommandInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const { ref: comparisonRef, visible: comparisonVisible } = useRevealOnScroll<HTMLElement>();
  const { ref: closingRef, visible: closingVisible } = useRevealOnScroll<HTMLElement>();

  const trimmed = commandInput.trim();
  const detectedMode = /^https?:\/\//i.test(trimmed)
    ? 'Link detected · Scrape & score fit'
    : trimmed.length > 100 || trimmed.includes('\n')
      ? 'Job description detected · Extract & score'
      : /^(find|show|roles|looking)/i.test(trimmed)
        ? 'AI career query'
        : 'Role search';

  const handleOmniSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isProcessing) return;
    setIsProcessing(true);
    try {
      if (!trimmed) {
        navigateTo(isAuthenticated ? '/radar' : '/explore');
        return;
      }
      if (/^https?:\/\//i.test(trimmed)) {
        if (!isAuthenticated) {
          setPendingIntent({ type: 'ingest_url', url: trimmed, label: 'Ingest & score pasted job link' });
          navigateTo('/register');
          return;
        }
        await ingestJobUrlOrText(trimmed, { onlySaveInterest: true });
        navigateTo('/radar?tab=saved');
        return;
      }
      if (trimmed.length > 100 || trimmed.includes('\n')) {
        if (!isAuthenticated) {
          setPendingIntent({ type: 'ingest_jd', label: 'Extract pasted job description' });
          navigateTo('/register');
          return;
        }
        await ingestJobUrlOrText(trimmed, { onlySaveInterest: true });
        navigateTo('/radar?tab=saved');
        return;
      }
      if (isAuthenticated) {
        navigateTo(`/radar?q=${encodeURIComponent(trimmed)}`);
      } else {
        navigateTo(`/explore?q=${encodeURIComponent(trimmed)}`);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUploadCv = async (file: File) => {
    setIsProcessing(true);
    try {
      const text = await file.text();
      const parsed = await ProfileAPI.parseLatex(text);
      if (parsed.success && parsed.profile && currentProfile?.profile) {
        await saveProfile({
          ...currentProfile.profile,
          ...parsed.profile,
          personal_info: parsed.profile.personal_info || currentProfile.profile.personal_info,
        });
      }
      if (!isAuthenticated) {
        setPendingIntent({ type: 'cv_upload', label: `Uploaded ${file.name}` });
        navigateTo('/register');
      } else {
        navigateTo('/onboarding');
      }
      pushToast(`Parsed ${file.name} cleanly.`, { variant: 'success' });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', color: 'var(--ink)', fontFamily: 'var(--font-sans)' }}>
      {/* Solid Pattern-Free 54px Sticky Header */}
      <header
        style={{
          height: 54,
          background: 'var(--ink)',
          color: 'var(--chalk)',
          padding: '0 32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          zIndex: 45,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
          <BrandLockup variant="horizontal" mode="thread" size={24} color="var(--chalk)" dir={dir} />
          <nav style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <a href="#comparison" className="t-landing-nav-link">
              Why Tailored
            </a>
            <a href="#features" className="t-landing-nav-link">
              Features
            </a>
            <button type="button" className="t-landing-nav-link" onClick={() => navigateTo('/explore')}>
              Explore live jobs
            </button>
          </nav>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {isAuthenticated ? (
            <button
              type="button"
              className="t-atelier-btn-primary"
              onClick={() => navigateTo('/dashboard')}
            >
              Open Dashboard
            </button>
          ) : (
            <>
              <button type="button" className="t-landing-nav-link" onClick={() => navigateTo('/login')}>
                Sign in
              </button>
              <button
                type="button"
                className="t-atelier-btn-primary"
                onClick={() => navigateTo('/register')}
              >
                Get started
              </button>
            </>
          )}
        </div>
      </header>

      {/* Hero Stage: Continuous --ink + Static AtelierFrenchCurveBackdrop */}
      <section
        style={{
          position: 'relative',
          background: 'var(--ink)',
          color: 'var(--chalk)',
          padding: '82px 32px 92px',
          overflow: 'hidden',
        }}
      >
        <AtelierFrenchCurveBackdrop />

        <div style={{ position: 'relative', zIndex: 1, maxWidth: 880, margin: '0 auto', textAlign: 'center' }}>
          <span className="t-eyebrow-dash t-eyebrow-dash--dark" style={{ marginBottom: 18 }}>
            Career Atelier · Built for Egypt &amp; The Gulf
          </span>

          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 64,
              lineHeight: 0.98,
              fontWeight: 500,
              color: 'var(--chalk)',
              margin: '0 0 20px',
            }}
          >
            One master profile. <br />
            Every application <em>cut to fit</em>.
          </h1>

          <p
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: 18.5,
              lineHeight: 1.58,
              color: 'var(--chalk)',
              opacity: 0.82,
              maxWidth: 640,
              margin: '0 auto 36px',
            }}
          >
            Score LinkedIn and Wuzzuf roles before applying, audit surgical LaTeX CV diffs side-by-side,
            and send paired cover letters directly — without inventing a single claim.
          </p>

          {/* Detached Borderless --paper Omni-Bar */}
          <form
            onSubmit={handleOmniSubmit}
            style={{
              maxWidth: 800,
              margin: '0 auto',
              background: 'var(--paper)',
              color: 'var(--ink)',
              borderRadius: '6px 26px 6px 6px',
              boxShadow: '0 28px 60px -16px rgba(0, 0, 0, 0.58)',
              padding: 8,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const f = e.dataTransfer.files[0];
              if (f) handleUploadCv(f);
            }}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".tex,.pdf,.docx,.txt"
              style={{ display: 'none' }}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleUploadCv(f);
              }}
            />
            <button
              type="button"
              className="t-atelier-btn-tonal"
              title="Drop or upload CV (.tex, .pdf, .docx)"
              onClick={() => fileRef.current?.click()}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}
            >
              <TailoredIcon name="upload" size={16} color="var(--ink)" />
              Upload CV
            </button>
            <input
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              placeholder="Paste a LinkedIn / Wuzzuf link, job description, or search roles…"
              style={{
                flex: 1,
                minWidth: 0,
                border: 'none',
                outline: 'none',
                background: 'transparent',
                fontFamily: 'var(--font-sans)',
                fontSize: 15,
                color: 'var(--ink)',
                padding: '10px 8px',
              }}
            />
            <button
              type="submit"
              className="t-atelier-btn-primary"
              disabled={isProcessing}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 20px' }}
            >
              <TailoredIcon name="radar" size={16} color="#ffffff" />
              {isProcessing ? 'Working…' : 'Tailor role'}
            </button>
          </form>

          <div
            style={{
              marginTop: 14,
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              gap: 16,
              flexWrap: 'wrap',
              fontSize: 12.5,
              color: 'var(--chalk)',
              opacity: 0.72,
            }}
          >
            <span>{detectedMode}</span>
            <span>·</span>
            <a href="#features" style={{ color: 'var(--kraft)', textDecoration: 'none', fontWeight: 500 }}>
              Watch live workspace demos ↓
            </a>
          </div>
        </div>
      </section>

      {/* Band 2 — Semantic Comparison (▼ Red Negatives vs ▲ Green Positives) */}
      <section
        id="comparison"
        ref={comparisonRef}
        style={{ background: 'var(--chalk)', padding: '78px 32px' }}
      >
        <div
          className={`t-landing-reveal ${comparisonVisible ? 'is-visible' : ''}`}
          style={{ maxWidth: 1080, margin: '0 auto' }}
        >
          <div style={{ maxWidth: 640, marginBottom: 32 }}>
            <span className="t-eyebrow-dash" style={{ marginBottom: 10 }}>
              The difference
            </span>
            <h2
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 38,
                lineHeight: 1.08,
                color: 'var(--ink)',
                margin: 0,
              }}
            >
              Built to replace guesswork with surgical precision.
            </h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24 }}>
            {/* Negatives Card — Red ▼ */}
            <div className="t-tonal-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <span className="t-signal-down" aria-hidden="true" />
                <span style={{ fontFamily: 'var(--font-display)', fontSize: 21, fontWeight: 600 }}>
                  Generic job hunting
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {[
                  'Sending the same generic PDF to every opening',
                  'Black-box AI rewrites that invent skills you do not have',
                  'Lost CV versions and forgotten email follow-ups',
                ].map((neg) => (
                  <div
                    key={neg}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: '10px 12px',
                      borderRadius: 8,
                      background: 'rgba(143, 29, 44, 0.055)',
                      fontSize: 14.5,
                      color: 'var(--ink)',
                    }}
                  >
                    <span className="t-signal-down" aria-hidden="true" />
                    <span>{neg}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Positives Card — Green ▲ */}
            <div className="t-tonal-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <span className="t-signal-up" aria-hidden="true" />
                <span style={{ fontFamily: 'var(--font-display)', fontSize: 21, fontWeight: 600 }}>
                  The Tailored Atelier
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {[
                  'Transparent 9-pillar fit scoring before you invest time',
                  'Line-by-line red/green diffs synced with live LaTeX & PDF',
                  'Paired cover letters, direct outreach & follow-up tracking',
                ].map((pos) => (
                  <div
                    key={pos}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: '10px 12px',
                      borderRadius: 8,
                      background: 'rgba(30, 138, 90, 0.075)',
                      fontSize: 14.5,
                      color: 'var(--ink)',
                    }}
                  >
                    <span className="t-signal-up" aria-hidden="true" />
                    <span>{pos}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Bands 3..6 — Scroll-Revealing Large-Format Workspace Video Showcases */}
      <div id="features">
        <FeatureShowcaseSection
          indexLabel="01"
          routeLabel="Job Radar"
          title="See every strength and gap before you apply."
          subtitle="Ingest LinkedIn or Wuzzuf links—or browse scored regional openings—with clear green advantages and honest red skill gaps."
          videoSrc="/demos/radar.mp4"
          positives={['9-pillar fit scoring', '100% grounded in profile']}
          negatives={['Flags missing stack gaps']}
          surface="paper"
        />

        <FeatureShowcaseSection
          indexLabel="02"
          routeLabel="CV Studio"
          title="Audit surgical diffs beside live Overleaf-style LaTeX."
          subtitle="Apply or skip individual bullet proposals with instant undo, then fine-tune .tex code right next to the compiled paper preview."
          videoSrc="/demos/studio.mp4"
          positives={['Line-by-line diff audit', 'Live .tex split + PDF']}
          surface="chalk"
        />

        <FeatureShowcaseSection
          indexLabel="03"
          routeLabel="Cover Letters"
          title="Drop any link, screenshot, or brief. Send with your CV."
          subtitle="Every tailored letter pairs directly with your matching Studio CV so you can refine the pitch and send outreach in one place."
          videoSrc="/demos/cover-letters.mp4"
          positives={['Non-destructive history', 'Direct email + CV attached']}
          surface="paper"
        />

        <FeatureShowcaseSection
          indexLabel="04"
          routeLabel="Application Pipeline"
          title="Every CV, letter, and follow-up linked in one track."
          subtitle="Move cleanly between Split and Kanban Board views with connected application packages and timely follow-up reminders."
          videoSrc="/demos/pipeline.mp4"
          positives={['Paired CV + letter package', 'Split & Board views']}
          surface="chalk"
        />
      </div>

      {/* Closing CTA Band */}
      <section
        ref={closingRef}
        style={{
          position: 'relative',
          background: 'var(--ink)',
          color: 'var(--chalk)',
          padding: '84px 32px',
          overflow: 'hidden',
        }}
      >
        <AtelierFrenchCurveBackdrop />

        <div
          className={`t-landing-reveal ${closingVisible ? 'is-visible' : ''}`}
          style={{
            position: 'relative',
            zIndex: 1,
            maxWidth: 820,
            margin: '0 auto',
            textAlign: 'center',
          }}
        >
          <span className="t-eyebrow-dash t-eyebrow-dash--dark" style={{ marginBottom: 14 }}>
            Ready when you are
          </span>
          <h2
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 44,
              lineHeight: 1.05,
              fontWeight: 500,
              color: 'var(--chalk)',
              margin: '0 0 16px',
            }}
          >
            Stop sending the same PDF to a hundred doors.
          </h2>
          <p
            style={{
              fontSize: 17,
              lineHeight: 1.55,
              color: 'var(--chalk)',
              opacity: 0.8,
              margin: '0 auto 30px',
              maxWidth: 560,
            }}
          >
            Build your Master Profile once and tailor every CV and cover letter with precision.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 12, flexWrap: 'wrap' }}>
            <button
              type="button"
              className="t-atelier-btn-primary"
              style={{ padding: '12px 24px', fontSize: 15 }}
              onClick={() => navigateTo(isAuthenticated ? '/dashboard' : '/register')}
            >
              {isAuthenticated ? 'Open Dashboard' : 'Start tailoring'}
            </button>
            <button
              type="button"
              className="t-atelier-btn-tonal"
              style={{ padding: '12px 24px', fontSize: 15 }}
              onClick={() => navigateTo('/explore')}
            >
              Explore live roles
            </button>
          </div>
        </div>
      </section>

      {/* Quiet Footer */}
      <footer
        style={{
          background: 'var(--ink)',
          borderTop: '1px solid rgba(229, 224, 218, 0.1)',
          padding: '24px 32px',
          color: 'var(--chalk)',
        }}
      >
        <div
          style={{
            maxWidth: 1080,
            margin: '0 auto',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 16,
            fontSize: 13,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, opacity: 0.82 }}>
            <BrandLockup variant="symbol" mode="thread" size={20} color="var(--chalk)" />
            <span>Tailored · Precision Career Atelier</span>
          </div>
          <div style={{ display: 'flex', gap: 18 }}>
            <button type="button" onClick={() => navigateTo('/privacy')} className="t-landing-nav-link">
              Privacy
            </button>
            <button type="button" onClick={() => navigateTo('/terms')} className="t-landing-nav-link">
              Terms
            </button>
            <button type="button" onClick={() => navigateTo('/explore')} className="t-landing-nav-link">
              Explore jobs
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};
