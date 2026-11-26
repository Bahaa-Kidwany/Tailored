import React from 'react';
import { BrandLockup } from '../../brand/BrandElements';
import { TailoredIcon } from '../../brand/TailoredIcons';
import { useWorkspace } from '../../context/WorkspaceContext';

const TOP_ROUTES = [
  { path: '/dashboard', label: 'Dashboard', arLabel: 'الرئيسية' },
  { path: '/radar', label: 'Radar', arLabel: 'الرادار' },
  { path: '/interest', label: 'Interest', arLabel: 'المحفوظة' },
  { path: '/studio', label: 'Studio', arLabel: 'الاستوديو' },
  { path: '/cover-letters', label: 'Letters', arLabel: 'الخطابات' },
  { path: '/pipeline', label: 'Pipeline', arLabel: 'المسار' },
];

export const BrandTopNav: React.FC = () => {
  const {
    currentPath,
    navigateTo,
    currentProfile,
    creditBalance,
    notifications,
    interestList,
    pipelineItems,
    setIsIdentityDrawerOpen,
    setIsCommandPaletteOpen,
    setIsNotificationsDrawerOpen,
    dir,
  } = useWorkspace();

  const fullName = currentProfile?.profile.personal_info.full_name || 'Mostafa Ibrahim';
  const initials = fullName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() || '')
    .join('');
  const unreadAlerts = notifications.filter((n) => !n.read).length;

  return (
    <header className="t-topnav">
      <div className="t-topnav-left">
        <button
          type="button"
          onClick={() => navigateTo('/')}
          style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: 0 }}
          title="Return to Landing Command Center"
        >
          <BrandLockup
            variant="horizontal"
            mode="knock"
            size={24}
            color="var(--chalk)"
            threadColor="var(--thread)"
            dir={dir}
          />
        </button>

        <div className="t-topnav-divider" />

        <nav className="t-topnav-links" aria-label="Workspace navigation">
          {TOP_ROUTES.map((item) => {
            const isActive =
              currentPath === item.path ||
              (item.path === '/radar' && currentPath.startsWith('/jobs/')) ||
              (item.path === '/pipeline' && currentPath.startsWith('/pipeline/'));
            const badge =
              item.path === '/interest' && interestList.length > 0
                ? interestList.length
                : item.path === '/pipeline' && pipelineItems.length > 0
                  ? pipelineItems.length
                  : null;
            return (
              <button
                key={item.path}
                type="button"
                onClick={() => navigateTo(item.path)}
                className={`t-nav-link ${isActive ? 't-nav-link--active' : ''}`}
              >
                <span>{dir === 'rtl' ? item.arLabel : item.label}</span>
                {badge !== null && <span className="t-nav-count">{badge}</span>}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="t-topnav-right">
        {/* Credit Wallet Pill (Mono tabular) */}
        <button
          type="button"
          onClick={() => navigateTo('/plans')}
          className="t-nav-link"
          style={{
            border: '1px solid var(--n700)',
            padding: '4px 10px',
            opacity: 1,
            color: creditBalance <= 2 ? 'var(--amber)' : 'var(--chalk)',
          }}
          title="View Credit Balance & Packs"
        >
          <TailoredIcon name="credit" size={14} color="currentColor" />
          <span>{creditBalance} CR</span>
        </button>

        {/* Notifications Quick Drawer */}
        <button
          type="button"
          onClick={() => setIsNotificationsDrawerOpen(true)}
          className="t-nav-link"
          style={{ position: 'relative', padding: '5px 8px' }}
          aria-label="Notifications"
          title="Notifications"
        >
          <TailoredIcon name="bell" size={16} color="var(--chalk)" />
          {unreadAlerts > 0 && (
            <span
              style={{
                background: 'var(--thread)',
                color: 'var(--ink)',
                fontSize: 10,
                fontWeight: 700,
                padding: '0 5px',
              }}
            >
              {unreadAlerts}
            </span>
          )}
        </button>

        {/* Cmd/Ctrl+K Palette */}
        <button
          type="button"
          onClick={() => setIsCommandPaletteOpen(true)}
          className="t-nav-link"
          style={{ border: '1px solid var(--n700)', padding: '4px 9px' }}
          title="Open Command Palette (Ctrl/Cmd + K)"
        >
          <TailoredIcon name="command" size={13} color="var(--chalk)" />
          <span>K</span>
        </button>

        {/* Official Circular Initial Avatar (p_ui.py line 39) */}
        <button
          type="button"
          onClick={() => setIsIdentityDrawerOpen(true)}
          className="t-avatar-btn"
          title="Identity, Persona, Regional Phone & Account"
          aria-label="Open identity and account drawer"
        >
          {initials || 'M'}
        </button>
      </div>
    </header>
  );
};
