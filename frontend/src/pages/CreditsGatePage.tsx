import React from 'react';
import { CREDIT_PACKS, useWorkspace } from '../context/WorkspaceContext';
import { BrandLockup } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';
import { SAMPLE_PROFILE } from '../services/profileApi';

export const CreditsGatePage: React.FC = () => {
  const {
    currentProfile,
    creditBalance,
    creditCurrency,
    setCreditCurrency,
    purchaseCreditPack,
    fulfillPendingIntent,
    pendingIntent,
    navigateTo,
    dir,
  } = useWorkspace();

  const profile = currentProfile?.profile || SAMPLE_PROFILE;
  const primaryPersona =
    profile.career_personas.find((p) => p.is_primary) || profile.career_personas[0];

  return (
    <div style={{ minHeight: '100vh', background: 'var(--chalk)', color: 'var(--ink)' }}>
      {/* Top Minimal Brand Header */}
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
        <BrandLockup variant="horizontal" mode="knock" size={24} color="var(--chalk)" dir={dir} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', border: '1px solid var(--n700)' }}>
            {(['EGP', 'SAR', 'AED', 'USD'] as const).map((cur) => (
              <button
                key={cur}
                type="button"
                onClick={() => setCreditCurrency(cur)}
                className="t-mono"
                style={{
                  padding: '4px 9px',
                  fontSize: 11,
                  border: 'none',
                  cursor: 'pointer',
                  background: creditCurrency === cur ? 'var(--thread)' : 'transparent',
                  color: creditCurrency === cur ? 'var(--ink)' : 'var(--chalk)',
                  fontWeight: creditCurrency === cur ? 700 : 400,
                }}
              >
                {cur}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="t-btn t-btn--chalk-outline t-btn--sm"
            onClick={() => navigateTo('/dashboard')}
          >
            Enter Workspace
          </button>
        </div>
      </header>

      <main style={{ maxWidth: 1020, margin: '0 auto', padding: '40px 24px 80px' }}>
        {/* 1. Completion Affirmation Ribbon */}
        <div
          className="t-card"
          style={{
            background: 'var(--ink)',
            color: 'var(--chalk)',
            borderColor: 'var(--ink)',
            padding: '26px 32px',
            marginBottom: 28,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 20,
            flexWrap: 'wrap',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <TailoredIcon name="check" size={16} color="var(--green)" />
              <span className="t-mono" style={{ fontSize: 11.5, color: 'var(--kraft)', letterSpacing: '0.1em' }}>
                PROFILE READY · {profile.personal_info.full_name.toUpperCase()} · {primaryPersona?.target_title.toUpperCase()}
              </span>
            </div>
            <h1 style={{ fontSize: 32, color: 'var(--chalk)', margin: 0 }}>
              {creditBalance} Free Credits Loaded. Start tailoring right now.
            </h1>
            <p style={{ color: 'var(--n300)', fontSize: 14.5, marginTop: 8, maxWidth: 620 }}>
              Browsing Job Radar, 9-pillar fit scoring, re-compiling saved CVs, and tracking pipeline rounds are always 0 credits. Pay only when crafting a new role pack.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-end' }}>
            <button
              type="button"
              className="t-btn t-btn--primary t-btn--lg"
              onClick={fulfillPendingIntent}
            >
              {pendingIntent
                ? `Launch Queued Request (${creditBalance} cr ready)`
                : `Start Using My ${creditBalance} Free Credits`}
              <TailoredIcon name="chevronRight" size={15} color="var(--ink)" />
            </button>
            <span className="t-mono" style={{ fontSize: 11, color: 'var(--n300)' }}>
              Zero credit card required · Credits never expire
            </span>
          </div>
        </div>

        {/* 2. Credit Packs Grid — Tailored Brand Book v1.2 (p_ui.py 06.08) */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 14 }}>
          <div>
            <span className="t-eyebrow">Pay-As-You-Go · No Subscriptions</span>
            <h2 style={{ fontSize: 24, marginTop: 4 }}>Or top up additional credits anytime</h2>
          </div>
          <span className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
            Paymob · Meeza · Fawry · Stripe
          </span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: 14,
            marginBottom: 28,
          }}
        >
          {CREDIT_PACKS.map((pack) => {
            const p = pack.prices[creditCurrency];
            const isPopular = pack.popular;
            return (
              <div
                key={pack.id}
                className="t-card"
                style={{
                  background: isPopular ? 'var(--ink)' : 'var(--paper)',
                  color: isPopular ? 'var(--chalk)' : 'var(--ink)',
                  borderColor: isPopular ? 'var(--ink)' : 'var(--n300)',
                  padding: '22px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: 16,
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <span className="t-label" style={{ color: isPopular ? 'var(--kraft)' : 'var(--n500)' }}>
                      {pack.name}
                    </span>
                    {isPopular && (
                      <span
                        className="t-chip"
                        style={{
                          background: 'var(--thread)',
                          color: 'var(--ink)',
                          borderColor: 'var(--thread)',
                          fontSize: 9.5,
                        }}
                      >
                        Popular
                      </span>
                    )}
                  </div>
                  <div
                    style={{
                      fontFamily: 'var(--font-voice)',
                      fontSize: 34,
                      fontWeight: 600,
                      lineHeight: 1.05,
                    }}
                  >
                    {p.label}
                  </div>
                  <div className="t-mono" style={{ fontSize: 12, marginTop: 6, color: isPopular ? 'var(--chalk)' : 'var(--n700)' }}>
                    {pack.credits} credits · {p.perCredit}
                  </div>
                  <div style={{ fontSize: 13, color: isPopular ? 'var(--n300)' : 'var(--n500)', marginTop: 8 }}>
                    {pack.subtitle} ({pack.appsEquiv})
                  </div>
                </div>

                {pack.isFree ? (
                  <button
                    type="button"
                    className="t-btn t-btn--outline t-btn--sm"
                    onClick={fulfillPendingIntent}
                  >
                    Already Loaded
                  </button>
                ) : (
                  <button
                    type="button"
                    className={`t-btn t-btn--sm ${isPopular ? 't-btn--primary' : 't-btn--ink'}`}
                    onClick={() => {
                      purchaseCreditPack(pack.id);
                      fulfillPendingIntent();
                    }}
                  >
                    Buy {pack.credits} Credits
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {/* 3. Transparent Action Cost Table */}
        <div className="t-card" style={{ padding: '20px 24px' }}>
          <div className="t-label" style={{ marginBottom: 10 }}>Transparent Credit Accounting</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>Job Radar & Fit Dial</div>
              <div className="t-mono" style={{ fontSize: 12, color: 'var(--green)' }}>0 Credits (Free Forever)</div>
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>Tailored CV Generation</div>
              <div className="t-mono" style={{ fontSize: 12, color: 'var(--ink)' }}>1 Credit / Target Job</div>
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>AI Refine Iterations</div>
              <div className="t-mono" style={{ fontSize: 12, color: 'var(--green)' }}>Included · 0 Extra Credits</div>
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>Cover Letter Generation</div>
              <div className="t-mono" style={{ fontSize: 12, color: 'var(--ink)' }}>1 Credit / Target Job</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
