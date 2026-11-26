import React, { useState, useEffect, useMemo } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { ResizableSplitPane } from '../components/common/ResizableSplitPane';
import { EmptyState } from '../brand/BrandElements';
import { TailoredIcon } from '../brand/TailoredIcons';

export const NotificationsPage: React.FC = () => {
  const {
    notifications,
    markNotificationRead,
    markAllNotificationsRead,
    snoozeNotification,
    navigateTo,
    radarJobs,
    openJobInStudio,
    openJobInCoverLetters,
    pipelineItems,
  } = useWorkspace();

  const [categoryFilter, setCategoryFilter] = useState<'all' | 'match' | 'followup' | 'document' | 'credit'>('all');
  const [selectedId, setSelectedId] = useState<string>(notifications[0]?.id || '');

  const visibleNotifs = useMemo(
    () =>
      notifications.filter((n) =>
        categoryFilter === 'all' ? true : n.category === categoryFilter
      ),
    [notifications, categoryFilter]
  );

  const activeNotif = visibleNotifs.find((n) => n.id === selectedId) || visibleNotifs[0] || null;
  const unreadCount = notifications.filter((n) => !n.read).length;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target && ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) return;
      if (visibleNotifs.length === 0) return;

      const idx = visibleNotifs.findIndex((n) => n.id === activeNotif?.id);
      if (e.key.toLowerCase() === 'j') {
        const next = visibleNotifs[Math.min(visibleNotifs.length - 1, Math.max(0, idx + 1))];
        if (next) setSelectedId(next.id);
      } else if (e.key.toLowerCase() === 'k') {
        const prev = visibleNotifs[Math.max(0, idx - 1)];
        if (prev) setSelectedId(prev.id);
      } else if (e.key.toLowerCase() === 'e' && activeNotif) {
        markNotificationRead(activeNotif.id);
      } else if (e.key.toLowerCase() === 's' && activeNotif) {
        snoozeNotification(activeNotif.id, 'Snoozed 2 days');
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [visibleNotifs, activeNotif, markNotificationRead, snoozeNotification]);

  const handleResolveAction = () => {
    if (!activeNotif) return;
    markNotificationRead(activeNotif.id);
    if (activeNotif.category === 'match') {
      const target = radarJobs.find((j) => j.id === activeNotif.jobId) || radarJobs[0];
      if (target) openJobInStudio(target);
      else navigateTo(activeNotif.targetPath);
    } else if (activeNotif.category === 'followup') {
      const pipe = pipelineItems.find((p) => p.status === 'applied') || pipelineItems[0];
      if (pipe) openJobInCoverLetters(pipe.job, { mode: 'followup' });
      else navigateTo('/pipeline');
    } else {
      navigateTo(activeNotif.targetPath);
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Header Toolbar */}
      <div
        style={{
          background: 'var(--paper)',
          borderBottom: '1.5px solid var(--ink)',
          padding: '10px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <h1 style={{ fontSize: 22, margin: 0 }}>Alerts &amp; Triage Inbox</h1>
          <span className="t-mono" style={{ fontSize: 11.5, color: 'var(--n500)' }}>
            {unreadCount} unread · J/K navigate · E mark done · S snooze
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {(['all', 'match', 'followup', 'document', 'credit'] as const).map((cat) => (
            <button
              key={cat}
              type="button"
              className={`t-chip ${categoryFilter === cat ? 't-chip--notch' : ''}`}
              style={{
                cursor: 'pointer',
                padding: '6px 12px',
                background: categoryFilter === cat ? 'var(--ink)' : 'var(--chalk)',
                color: categoryFilter === cat ? 'var(--chalk)' : 'var(--ink)',
              }}
              onClick={() => setCategoryFilter(cat)}
            >
              {cat === 'all'
                ? 'All'
                : cat === 'match'
                  ? 'Radar Matches'
                  : cat === 'followup'
                    ? 'Follow-ups'
                    : cat === 'document'
                      ? 'Documents'
                      : 'Credits'}
            </button>
          ))}
          <button type="button" className="t-btn t-btn--outline t-btn--sm" onClick={markAllNotificationsRead}>
            Mark All Read
          </button>
        </div>
      </div>

      {/* 40% / 60% Triage Split */}
      {visibleNotifs.length === 0 ? (
        <div style={{ flex: 1, padding: 32 }}>
          <EmptyState
            icon="bell"
            headline="Inbox zero — all alerts triaged"
            subtext="High-signal Radar drops and 7-day pipeline reminders appear here automatically."
            ctaLabel="Browse Job Radar"
            onCta={() => navigateTo('/radar')}
          />
        </div>
      ) : (
        <ResizableSplitPane
          storageKey="notifications_split"
          defaultLeftPct={40}
          minLeftPx={320}
          minRightPx={420}
          left={
            <div>
              {visibleNotifs.map((n) => {
                const active = activeNotif?.id === n.id;
                return (
                  <div
                    key={n.id}
                    className={`t-list-row ${active ? 't-list-row--active' : ''}`}
                    style={{ opacity: n.read ? 0.68 : 1 }}
                    onClick={() => {
                      setSelectedId(n.id);
                      markNotificationRead(n.id);
                    }}
                  >
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {!n.read && (
                          <span style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--thread)', flexShrink: 0 }} />
                        )}
                        <span style={{ fontWeight: n.read ? 500 : 700, fontSize: 14 }}>{n.title}</span>
                      </div>
                      <div className="t-mono" style={{ fontSize: 11, color: 'var(--n500)', marginTop: 3 }}>
                        {n.category.toUpperCase()} · {n.timestamp} {n.snoozedUntil ? `· ${n.snoozedUntil}` : ''}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          }
          right={
            activeNotif ? (
              <div style={{ padding: '30px 36px', background: 'var(--paper)', minHeight: '100%' }}>
                <span className="t-eyebrow">{activeNotif.category} Signal · {activeNotif.timestamp}</span>
                <h2 style={{ fontSize: 28, marginTop: 6, marginBottom: 12 }}>{activeNotif.title}</h2>
                <p style={{ fontSize: 15, lineHeight: 1.65, color: 'var(--n700)', maxWidth: 560, marginBottom: 22 }}>
                  {activeNotif.subtitle}
                </p>

                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', paddingTop: 18, borderTop: '1px solid var(--n300)' }}>
                  <button type="button" className="t-btn t-btn--primary" onClick={handleResolveAction}>
                    {activeNotif.actionLabel}
                    <TailoredIcon name="chevronRight" size={14} color="var(--ink)" />
                  </button>
                  <button
                    type="button"
                    className="t-btn t-btn--outline"
                    onClick={() => snoozeNotification(activeNotif.id, 'Snoozed 2 days')}
                  >
                    <TailoredIcon name="clock" size={14} />
                    Snooze 2 Days (S)
                  </button>
                  <button
                    type="button"
                    className="t-btn t-btn--ghost"
                    onClick={() => markNotificationRead(activeNotif.id)}
                  >
                    Mark Done (E)
                  </button>
                </div>
              </div>
            ) : null
          }
        />
      )}
    </div>
  );
};
