import React from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { TailoredIcon } from '../../brand/TailoredIcons';

export const ToastStack: React.FC = () => {
  const { toasts, dismissToast } = useWorkspace();
  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: 'fixed',
        right: 24,
        bottom: 24,
        zIndex: 90,
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        maxWidth: 420,
      }}
    >
      {toasts.map((t) => {
        const borderCol =
          t.variant === 'error'
            ? 'var(--alarm)'
            : t.variant === 'warn'
              ? 'var(--amber)'
              : t.variant === 'success'
                ? 'var(--green)'
                : 'var(--thread)';
        return (
          <div
            key={t.id}
            style={{
              background: 'var(--ink)',
              color: 'var(--chalk)',
              borderLeft: `4px solid ${borderCol}`,
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 14,
              fontSize: 13.5,
            }}
          >
            <span>{t.message}</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
              {t.onUndo && (
                <button
                  type="button"
                  onClick={() => {
                    t.onUndo?.();
                    dismissToast(t.id);
                  }}
                  style={{
                    background: 'var(--thread)',
                    color: 'var(--ink)',
                    border: 'none',
                    padding: '4px 10px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 11,
                    fontWeight: 600,
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                    cursor: 'pointer',
                  }}
                >
                  {t.undoLabel || 'Undo'}
                </button>
              )}
              <button
                type="button"
                onClick={() => dismissToast(t.id)}
                aria-label="Dismiss notification"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--chalk)',
                  opacity: 0.7,
                  cursor: 'pointer',
                  padding: 2,
                }}
              >
                <TailoredIcon name="close" size={14} color="var(--chalk)" />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export const OfflineBanner: React.FC = () => {
  const { isOnline } = useWorkspace();
  if (isOnline) return null;

  return (
    <div
      style={{
        background: 'var(--amber)',
        color: 'var(--ink)',
        padding: '8px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontFamily: 'var(--font-mono)',
        fontSize: 12,
        borderBottom: '1.5px solid var(--ink)',
      }}
    >
      <span>
        Offline mode — CV edits, Pipeline &amp; Profile changes are saving locally and will sync on
        reconnect.
      </span>
      <button
        type="button"
        onClick={() => window.location.reload()}
        className="t-btn t-btn--outline t-btn--sm"
      >
        Retry
      </button>
    </div>
  );
};
