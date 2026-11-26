import React, { useState } from 'react';
import { CREDIT_PACKS, useWorkspace, type CreditCurrency } from '../../context/WorkspaceContext';
import { TailoredIcon } from '../../brand/TailoredIcons';

export const OutOfCreditsModal: React.FC = () => {
  const {
    outOfCreditsState,
    closeOutOfCredits,
    creditBalance,
    creditCurrency,
    setCreditCurrency,
    purchaseCreditPack,
  } = useWorkspace();

  const [selectedPackId, setSelectedPackId] = useState('hunter');
  const [paymentMethod, setPaymentMethod] = useState<'card' | 'wallet' | 'fawry'>('card');

  if (!outOfCreditsState) return null;

  const paidPacks = CREDIT_PACKS.filter((p) => !p.isFree);
  const chosenPack = paidPacks.find((p) => p.id === selectedPackId) || paidPacks[1];

  return (
    <div className="t-backdrop" onClick={closeOutOfCredits}>
      <div
        className="t-modal"
        style={{ width: '100%', maxWidth: 740, padding: 34 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
          <div>
            <span className="t-eyebrow">Credits Exhausted</span>
            <h2 style={{ fontSize: 32, marginTop: 6 }}>
              Top up to continue <em>{outOfCreditsState.actionLabel}.</em>
            </h2>
          </div>
          <button type="button" onClick={closeOutOfCredits} className="t-btn t-btn--ghost t-btn--sm">
            <TailoredIcon name="close" size={16} />
          </button>
        </div>

        <div className="t-alert t-alert--warn" style={{ marginBottom: 20 }}>
          <div style={{ fontWeight: 600, fontSize: 13.5 }}>Your unsaved edits are preserved safely.</div>
          <div style={{ fontSize: 13, color: 'var(--n700)' }}>
            Balance: <span className="t-mono">{creditBalance} credits</span> · Action requires{' '}
            <span className="t-mono">{outOfCreditsState.requiredCredits} credit</span>. Credits never expire.
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <span className="t-label" style={{ color: 'var(--n500)' }}>
            Pay-As-You-Go Packs · No Subscription
          </span>
          <div style={{ display: 'flex', gap: 4 }}>
            {(['EGP', 'SAR', 'AED', 'USD'] as CreditCurrency[]).map((cur) => (
              <button
                key={cur}
                type="button"
                onClick={() => setCreditCurrency(cur)}
                className={`t-btn t-btn--sm ${creditCurrency === cur ? 't-btn--ink' : 't-btn--subtle'}`}
                style={{ padding: '4px 10px' }}
              >
                {cur}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
          {paidPacks.map((pk) => {
            const active = selectedPackId === pk.id;
            const price = pk.prices[creditCurrency];
            return (
              <button
                key={pk.id}
                type="button"
                onClick={() => setSelectedPackId(pk.id)}
                style={{
                  textAlign: 'left',
                  padding: 16,
                  background: active ? 'var(--ink)' : 'var(--chalk)',
                  color: active ? 'var(--chalk)' : 'var(--ink)',
                  border: active ? '2px solid var(--thread)' : '1.5px solid var(--n300)',
                  cursor: 'pointer',
                  position: 'relative',
                }}
              >
                {pk.popular && (
                  <span
                    className="t-label"
                    style={{
                      position: 'absolute',
                      top: -10,
                      right: 10,
                      background: 'var(--thread)',
                      color: 'var(--ink)',
                      padding: '2px 8px',
                      fontSize: 9.5,
                    }}
                  >
                    Popular
                  </span>
                )}
                <div className="t-label" style={{ opacity: 0.75 }}>
                  {pk.name}
                </div>
                <div style={{ fontFamily: 'var(--font-voice)', fontSize: 28, fontWeight: 600, marginTop: 4 }}>
                  {price.label}
                </div>
                <div className="t-mono" style={{ fontSize: 12, marginTop: 4 }}>
                  {pk.credits} credits · {pk.appsEquiv}
                </div>
              </button>
            );
          })}
        </div>

        <div style={{ marginBottom: 20 }}>
          <div className="t-label" style={{ color: 'var(--n500)', marginBottom: 8 }}>
            Payment Method ({creditCurrency === 'EGP' ? 'Paymob · VAT Inclusive' : 'Stripe / Apple Pay'})
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {[
              { id: 'card' as const, label: creditCurrency === 'EGP' ? 'Meeza / Card' : 'Card / Apple Pay' },
              { id: 'wallet' as const, label: creditCurrency === 'EGP' ? 'Vodafone Cash / InstaPay' : 'Google Pay' },
              { id: 'fawry' as const, label: 'Fawry Reference' },
            ].map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setPaymentMethod(m.id)}
                className={`t-btn t-btn--sm ${paymentMethod === m.id ? 't-btn--ink' : 't-btn--outline'}`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button type="button" onClick={closeOutOfCredits} className="t-btn t-btn--ghost">
            Cancel &amp; Keep Draft
          </button>
          <button
            type="button"
            className="t-btn t-btn--primary t-btn--lg"
            onClick={() => purchaseCreditPack(chosenPack.id)}
          >
            Pay {chosenPack.prices[creditCurrency].label} &amp; Resume
          </button>
        </div>
      </div>
    </div>
  );
};
