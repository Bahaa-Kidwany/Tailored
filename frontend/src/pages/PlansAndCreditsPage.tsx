import React, { useState } from 'react';
import { CREDIT_PACKS, useWorkspace, type CreditPackOption } from '../context/WorkspaceContext';
import { TailoredIcon } from '../brand/TailoredIcons';

export const PlansAndCreditsPage: React.FC = () => {
  const {
    creditBalance,
    creditCurrency,
    setCreditCurrency,
    lowBalanceThreshold,
    setLowBalanceThreshold,
    creditLedger,
    purchaseCreditPack,
  } = useWorkspace();

  const [checkoutPack, setCheckoutPack] = useState<CreditPackOption | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<'card' | 'meeza' | 'fawry'>('card');

  const completeCheckout = () => {
    if (!checkoutPack) return;
    purchaseCreditPack(checkoutPack.id);
    setCheckoutPack(null);
  };

  return (
    <div className="t-page-fluid">
      {/* 1. Credit Wallet Hero Banner */}
      <section
        className="t-card"
        style={{
          background: 'var(--ink)',
          color: 'var(--chalk)',
          borderColor: 'var(--ink)',
          padding: '26px 30px',
          marginBottom: 24,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 20,
          flexWrap: 'wrap',
        }}
      >
        <div>
          <span className="t-mono" style={{ fontSize: 11, color: 'var(--kraft)', letterSpacing: '0.12em' }}>
            PAY-AS-YOU-GO WALLET · CREDITS NEVER EXPIRE
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginTop: 6 }}>
            <span style={{ fontFamily: 'var(--font-voice)', fontSize: 48, fontWeight: 600, color: 'var(--chalk)' }}>
              {creditBalance}
            </span>
            <span className="t-mono" style={{ fontSize: 14, color: 'var(--n300)' }}>
              AVAILABLE CREDITS (~{Math.max(1, Math.floor(creditBalance / 2))} full job applications)
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
          <div>
            <div className="t-mono" style={{ fontSize: 10.5, color: 'var(--n300)', marginBottom: 4 }}>
              LOW-BALANCE ALERT
            </div>
            <select
              className="t-select"
              style={{ width: 140, background: 'var(--ink-elevated)', color: 'var(--chalk)', borderColor: 'var(--n700)' }}
              value={lowBalanceThreshold}
              onChange={(e) => setLowBalanceThreshold(Number(e.target.value))}
            >
              <option value={1}>Below 1 credit</option>
              <option value={3}>Below 3 credits</option>
              <option value={5}>Below 5 credits</option>
            </select>
          </div>

          <div>
            <div className="t-mono" style={{ fontSize: 10.5, color: 'var(--n300)', marginBottom: 4 }}>CURRENCY</div>
            <div style={{ display: 'flex', border: '1px solid var(--n700)' }}>
              {(['EGP', 'SAR', 'AED', 'USD'] as const).map((cur) => (
                <button
                  key={cur}
                  type="button"
                  onClick={() => setCreditCurrency(cur)}
                  className="t-mono"
                  style={{
                    padding: '6px 11px',
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
          </div>
        </div>
      </section>

      {/* 2. Top-Up Credit Packs */}
      <h2 style={{ fontSize: 24, marginBottom: 14 }}>Purchase Non-Expiring Credit Packs</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 28 }}>
        {CREDIT_PACKS.map((pack) => {
          const price = pack.prices[creditCurrency];
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
                gap: 14,
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="t-label" style={{ color: isPopular ? 'var(--kraft)' : 'var(--n500)' }}>
                    {pack.name}
                  </span>
                  {isPopular && (
                    <span className="t-chip" style={{ background: 'var(--thread)', color: 'var(--ink)', borderColor: 'var(--thread)' }}>
                      Popular
                    </span>
                  )}
                </div>
                <div style={{ fontFamily: 'var(--font-voice)', fontSize: 32, fontWeight: 600, marginTop: 8 }}>
                  {price.label}
                </div>
                <div className="t-mono" style={{ fontSize: 12, marginTop: 4 }}>
                  {pack.credits} credits · {price.perCredit}
                </div>
                <div style={{ fontSize: 13, color: isPopular ? 'var(--n300)' : 'var(--n500)', marginTop: 6 }}>
                  {pack.appsEquiv}
                </div>
              </div>
              {pack.isFree ? (
                <span className="t-mono" style={{ fontSize: 11, color: 'var(--green)' }}>
                  Granted at registration
                </span>
              ) : (
                <button
                  type="button"
                  className={`t-btn t-btn--sm ${isPopular ? 't-btn--primary' : 't-btn--ink'}`}
                  onClick={() => setCheckoutPack(pack)}
                >
                  Select {pack.name}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* 3. Action Cost Schedule */}
      <section className="t-card" style={{ padding: '20px 24px', marginBottom: 24 }}>
        <div className="t-label" style={{ marginBottom: 10 }}>What Costs Credits vs What Is Always Free</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>Job Radar & 9-Pillar Audit</div>
            <div className="t-mono" style={{ fontSize: 12, color: 'var(--green)' }}>0 Credits · Always Free</div>
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>Generate Tailored CV</div>
            <div className="t-mono" style={{ fontSize: 12 }}>1 Credit / Target Role</div>
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>Chat Refinements & Re-PDF</div>
            <div className="t-mono" style={{ fontSize: 12, color: 'var(--green)' }}>0 Credits (Unlocked Forever)</div>
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>Generate Cover Letter</div>
            <div className="t-mono" style={{ fontSize: 12 }}>1 Credit / Target Role</div>
          </div>
        </div>
      </section>

      {/* 4. Transparent Usage Ledger */}
      <section className="t-card--flat" style={{ background: 'var(--paper)', padding: '20px 24px' }}>
        <div className="t-label" style={{ marginBottom: 12 }}>Credit Ledger & Receipt History</div>
        <table className="t-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Action</th>
              <th>Target Role / Pack</th>
              <th>Credits</th>
              <th>Balance After</th>
            </tr>
          </thead>
          <tbody>
            {creditLedger.map((row) => (
              <tr key={row.id}>
                <td className="t-mono" style={{ fontSize: 12 }}>{row.date}</td>
                <td style={{ fontWeight: 600 }}>{row.action}</td>
                <td style={{ color: 'var(--n700)' }}>{row.jobTarget}</td>
                <td className="t-mono" style={{ fontWeight: 600, color: row.delta >= 0 ? 'var(--green)' : 'var(--ink)' }}>
                  {row.delta >= 0 ? `+${row.delta}` : row.delta}
                </td>
                <td className="t-mono">{row.balanceAfter}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Inline Slide-Over Fast Checkout Drawer */}
      {checkoutPack && (
        <div className="t-drawer-backdrop" onClick={() => setCheckoutPack(null)}>
          <aside className="t-drawer t-drawer--right" style={{ width: 420, padding: 28, gap: 18 }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1.5px solid var(--ink)', paddingBottom: 12 }}>
              <div>
                <span className="t-eyebrow">Fast Wallet Top-Up</span>
                <h3 style={{ fontSize: 22, marginTop: 4 }}>{checkoutPack.name} Pack</h3>
              </div>
              <button type="button" className="t-btn t-btn--ghost t-btn--sm" onClick={() => setCheckoutPack(null)}>
                <TailoredIcon name="close" size={16} />
              </button>
            </div>

            <div className="t-card--flat" style={{ padding: 16, background: 'var(--chalk)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600 }}>
                <span>{checkoutPack.credits} Tailored Credits</span>
                <span>{checkoutPack.prices[creditCurrency].label}</span>
              </div>
              <div className="t-mono" style={{ fontSize: 11, color: 'var(--n500)', marginTop: 4 }}>
                No recurring subscription · Added instantly to wallet
              </div>
            </div>

            <div>
              <div className="t-label" style={{ marginBottom: 8 }}>Payment Method</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  { id: 'card' as const, label: 'Visa / Mastercard / Apple Pay (Stripe / Paymob)' },
                  { id: 'meeza' as const, label: 'Meeza / Egyptian Wallet' },
                  { id: 'fawry' as const, label: 'Fawry Pay Reference Code' },
                ].map((m) => (
                  <label key={m.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 10, border: '1px solid var(--n300)', cursor: 'pointer', fontSize: 13.5 }}>
                    <input
                      type="radio"
                      name="payMethod"
                      checked={paymentMethod === m.id}
                      onChange={() => setPaymentMethod(m.id)}
                    />
                    {m.label}
                  </label>
                ))}
              </div>
            </div>

            <button type="button" className="t-btn t-btn--primary t-btn--lg" onClick={completeCheckout}>
              Complete Purchase · {checkoutPack.prices[creditCurrency].label}
            </button>
          </aside>
        </div>
      )}
    </div>
  );
};
