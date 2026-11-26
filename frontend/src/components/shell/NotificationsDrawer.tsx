import React from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { TailoredIcon } from '../../brand/TailoredIcons';

export const NotificationsDrawer: React.FC = () => {
  const {
    isNotificationsDrawerOpen,
    setIsNotificationsDrawerOpen,
    notifications,
    markNotificationRead,
    markAllNotificationsRead,
    snoozeNotification,
    navigateTo,
    dir,
  } = useWorkspace();

  if (!isNotificationsDrawerOpen) return null;

  const unread = notifications.filter((n) => !n.read).length;

  return (
    <div className="t-drawer-backdrop" onClick={() => setIsNotificationsDrawerOpen(false)}>
      <aside
        className={`t-drawer ${dir === 'ltr' ? 't-drawer--right' : ''}`}
        onClick={(e) => e.stopPropagation()}
        style={{ padding: 24, gap: 16 }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingBottom: 14,
            borderBottom: '1.5px solid var(--ink)',
          }}
        >
          <div>
            <span className="t-eyebrow">Alerts</span>
            <h2 style={{ fontSize: 22, marginTop: 4 }}>Notifications ({unread} unread)</h2>
          </div>
          <button
            type="button"
            onClick={() => setIsNotificationsDrawerOpen(false)}
            className="t-btn t-btn--ghost t-btn--sm"
          >
            <TailoredIcon name="close" size={16} />
          </button>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button type="button" onClick={markAllNotificationsRead} className="t-btn t-btn--subtle t-btn--sm">
            Mark all read
          </button>
          <button
            type="button"
            onClick={() => {
              setIsNotificationsDrawerOpen(false);
              navigateTo('/notifications');
            }}
            className="t-btn t-btn--outline t-btn--sm"
          >
            Full Inbox
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {notifications.map((n) => (
            <div
              key={n.id}
              className="t-card--flat"
              style={{
                padding: 14,
                borderLeft: `3px solid ${n.read ? 'var(--n300)' : 'var(--thread)'}`,
                background: n.read ? 'var(--chalk)' : 'var(--paper)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginBottom: 4 }}>
                <span className="t-label" style={{ color: 'var(--n500)' }}>
                  {n.category} · {n.timestamp}
                </span>
                {n.snoozedUntil && (
                  <span className="t-chip t-chip--mist">Snoozed: {n.snoozedUntil}</span>
                )}
              </div>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{n.title}</div>
              <div style={{ fontSize: 13, color: 'var(--n700)', marginBottom: 10 }}>{n.subtitle}</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="t-btn t-btn--primary t-btn--sm"
                  onClick={() => {
                    markNotificationRead(n.id);
                    setIsNotificationsDrawerOpen(false);
                    navigateTo(n.targetPath);
                  }}
                >
                  {n.actionLabel}
                </button>
                <button
                  type="button"
                  className="t-btn t-btn--subtle t-btn--sm"
                  onClick={() => snoozeNotification(n.id, '3 Days')}
                >
                  Snooze 3d
                </button>
              </div>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
};

export const ShortcutsHelpModal: React.FC = () => {
  const { isShortcutsHelpOpen, setIsShortcutsHelpOpen } = useWorkspace();
  if (!isShortcutsHelpOpen) return null;

  const rows = [
    ['Ctrl/Cmd + K', 'Open Universal Command Palette (or paste any job URL)'],
    ['?', 'Toggle this keyboard shortcuts reference'],
    ['J / K', 'Move down / up through jobs, pipeline rows, or alerts'],
    ['Space', 'Open Quick-Peek preview drawer on focused item'],
    ['X', 'Hide irrelevant job on Radar (with Undo)'],
    ['B', 'Save / Bookmark job to Interest List'],
    ['] / Alt + S', 'Collapse or Swap AI Coach side in CV & Cover Letter Studio'],
    ['Enter / Esc / R', 'Apply / Skip / Refine active AI proposal card'],
    ['Ctrl/Cmd + S', 'Save Master Profile changes'],
  ];

  return (
    <div className="t-backdrop" onClick={() => setIsShortcutsHelpOpen(false)}>
      <div
        className="t-modal"
        style={{ width: '100%', maxWidth: 560, padding: 28 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <span className="t-eyebrow">Ergonomics</span>
            <h2 style={{ fontSize: 26, marginTop: 4 }}>Keyboard Shortcuts</h2>
          </div>
          <button
            type="button"
            onClick={() => setIsShortcutsHelpOpen(false)}
            className="t-btn t-btn--ghost t-btn--sm"
          >
            <TailoredIcon name="close" size={16} />
          </button>
        </div>
        <div className="t-stitch" style={{ marginBottom: 14 }} />
        <table className="t-table">
          <tbody>
            {rows.map(([key, desc]) => (
              <tr key={key}>
                <td className="t-mono" style={{ width: 170, fontWeight: 600 }}>
                  {key}
                </td>
                <td>{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
