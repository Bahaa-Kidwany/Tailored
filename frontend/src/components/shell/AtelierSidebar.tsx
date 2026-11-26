import React, { useState, useEffect, useRef } from 'react';
import { BrandLockup } from '../../brand/BrandElements';
import { TailoredIcon, type BrandIconName } from '../../brand/TailoredIcons';
import { useWorkspace } from '../../context/WorkspaceContext';

interface SidebarNavItem {
  path: string;
  label: string;
  arLabel: string;
  icon: BrandIconName;
  matchPrefix?: string;
}

const PRIMARY_ROUTES: SidebarNavItem[] = [
  { path: '/dashboard', label: 'Dashboard', arLabel: 'الرئيسية', icon: 'dashboard' },
  { path: '/radar', label: 'Job Radar', arLabel: 'الرادار', icon: 'radar', matchPrefix: '/jobs/' },
  { path: '/studio', label: 'CV Studio', arLabel: 'الاستوديو', icon: 'cv', matchPrefix: '/cvs' },
  { path: '/cover-letters', label: 'Cover Letters', arLabel: 'الخطابات', icon: 'coverLetter' },
  { path: '/pipeline', label: 'Pipeline', arLabel: 'المسار', icon: 'pipeline', matchPrefix: '/pipeline/' },
];

const ACCOUNT_ROUTES: SidebarNavItem[] = [
  { path: '/profile', label: 'Master Profile', arLabel: 'الملف الرئيسي', icon: 'profile' },
  { path: '/plans', label: 'Plans & Credits', arLabel: 'الرصيد والخطط', icon: 'credit' },
  { path: '/account', label: 'Account & Security', arLabel: 'الحساب والأمان', icon: 'settings' },
];

const SIDEBAR_STORAGE_KEY = 'tailored_sidebar_collapsed';

export const AtelierSidebar: React.FC = () => {
  const {
    currentPath,
    navigateTo,
    defaultHomeRoute,
    currentProfile,
    activePersonaId,
    activeRegionalPhone,
    userEmail,
    creditBalance,
    notifications,
    interestList,
    pipelineItems,
    setIsIdentityDrawerOpen,
    setIsCommandPaletteOpen,
    setIsNotificationsDrawerOpen,
    setIsShortcutsHelpOpen,
    signOut,
    dir,
    setDir,
  } = useWorkspace();

  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem(SIDEBAR_STORAGE_KEY) === '1';
    } catch {
      return false;
    }
  });
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const accountMenuRef = useRef<HTMLDivElement>(null);

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(SIDEBAR_STORAGE_KEY, next ? '1' : '0');
      } catch {
        // ignore storage restrictions
      }
      return next;
    });
  };

  useEffect(() => {
    const onMouseDown = (e: MouseEvent) => {
      if (accountMenuRef.current && !accountMenuRef.current.contains(e.target as Node)) {
        setAccountMenuOpen(false);
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setAccountMenuOpen(false);
        return;
      }
      const target = e.target as HTMLElement | null;
      const typing = target?.tagName === 'INPUT' || target?.tagName === 'TEXTAREA' || target?.tagName === 'SELECT' || target?.isContentEditable;
      if (typing) return;
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        toggleCollapsed();
      } else if (e.key === '[') {
        e.preventDefault();
        toggleCollapsed();
      }
    };
    window.addEventListener('mousedown', onMouseDown);
    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('keydown', onKeyDown);
    };
  }, []);

  const profile = currentProfile?.profile;
  const fullName = profile?.personal_info.full_name || 'Mostafa Ibrahim';
  const activePersona =
    profile?.career_personas.find((p) => p.persona_id === activePersonaId) ||
    profile?.career_personas[0];
  const initials = fullName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() || '')
    .join('');

  const unreadAlerts = notifications.filter((n) => !n.read).length;

  const isRouteActive = (item: SidebarNavItem) =>
    currentPath === item.path ||
    (item.path === '/radar' && currentPath === '/interest') ||
    (item.matchPrefix ? currentPath.startsWith(item.matchPrefix) : false);

  const getPrimaryBadge = (path: string): number | null => {
    if (path === '/radar' && interestList.length > 0) return interestList.length;
    if (path === '/pipeline' && pipelineItems.length > 0) return pipelineItems.length;
    return null;
  };

  return (
    <aside
      className={`t-atelier-sidebar ${collapsed ? 't-atelier-sidebar--collapsed' : ''}`}
      aria-label="Workspace sidebar"
    >
      {/* Top Brand Lockup + Collapse Toggle */}
      <div className="t-sidebar-head">
        <button
          type="button"
          className="t-sidebar-logo-btn"
          onClick={() => navigateTo(defaultHomeRoute)}
          title="Return to Workspace Home"
          aria-label="Tailored home"
        >
          <BrandLockup
            variant={collapsed ? 'symbol' : 'horizontal'}
            mode="knock"
            size={24}
            color="var(--chalk)"
            threadColor="var(--thread)"
            dir={dir}
          />
        </button>

        <button
          type="button"
          className="t-sidebar-collapse-btn"
          onClick={toggleCollapsed}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-expanded={!collapsed}
          title={collapsed ? 'Expand panel ([ or Ctrl+B)' : 'Collapse panel ([ or Ctrl+B)'}
        >
          <TailoredIcon
            name={collapsed ? 'expand' : 'collapse'}
            size={15}
            color="var(--chalk)"
          />
        </button>
      </div>

      {/* Borderless Quick Command Trigger */}
      <button
        type="button"
        className="t-sidebar-search"
        onClick={() => setIsCommandPaletteOpen(true)}
        title="Command Palette (Ctrl/Cmd + K)"
        aria-label="Open Command Palette"
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <TailoredIcon name="search" size={14} color="var(--chalk)" />
          {!collapsed && <span>{dir === 'rtl' ? 'بحث سريع...' : 'Quick jump...'}</span>}
        </span>
        {!collapsed && <span className="t-sidebar-kbd">⌘K</span>}
      </button>

      {/* Primary Workspace Navigation */}
      {!collapsed && (
        <div className="t-sidebar-section-label">
          {dir === 'rtl' ? 'مساحة العمل' : 'Workspace'}
        </div>
      )}
      <nav className="t-sidebar-nav" aria-label="Primary pages">
        {PRIMARY_ROUTES.map((item) => {
          const active = isRouteActive(item);
          const badge = getPrimaryBadge(item.path);
          const label = dir === 'rtl' ? item.arLabel : item.label;
          return (
            <button
              key={item.path}
              type="button"
              onClick={() => navigateTo(item.path)}
              className={`t-sidebar-item ${active ? 't-sidebar-item--active' : ''}`}
              title={collapsed ? label : undefined}
              aria-current={active ? 'page' : undefined}
            >
              <span className="t-sidebar-item-left">
                <TailoredIcon
                  name={item.icon}
                  size={16}
                  color={active ? 'var(--paper)' : 'var(--chalk)'}
                />
                {!collapsed && <span>{label}</span>}
              </span>
              {!collapsed && badge !== null && (
                <span className="t-sidebar-badge">{badge}</span>
              )}
              {collapsed && badge !== null && <span className="t-sidebar-mini-dot" />}
            </button>
          );
        })}
      </nav>

      {/* Bottom Account Management Dock */}
      <div className="t-sidebar-bottom">
        {!collapsed && (
          <div className="t-sidebar-section-label">
            {dir === 'rtl' ? 'الحساب والإعدادات' : 'Account'}
          </div>
        )}

        <nav className="t-sidebar-nav" aria-label="Account management">
          {ACCOUNT_ROUTES.map((item) => {
            const active = isRouteActive(item);
            const label = dir === 'rtl' ? item.arLabel : item.label;
            const isPlans = item.path === '/plans';
            return (
              <button
                key={item.path}
                type="button"
                onClick={() => navigateTo(item.path)}
                className={`t-sidebar-item ${active ? 't-sidebar-item--active' : ''}`}
                title={
                  collapsed
                    ? isPlans
                      ? `${label} (${creditBalance} cr)`
                      : label
                    : undefined
                }
                aria-current={active ? 'page' : undefined}
              >
                <span className="t-sidebar-item-left">
                  <TailoredIcon
                    name={item.icon}
                    size={16}
                    color={active ? 'var(--paper)' : 'var(--chalk)'}
                  />
                  {!collapsed && <span>{label}</span>}
                </span>
                {!collapsed && isPlans && (
                  <span
                    className="t-sidebar-badge"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 5,
                      color: creditBalance <= 2 ? 'var(--amber)' : 'var(--chalk)',
                    }}
                  >
                    {creditBalance === 0 && <span className="t-signal-down" aria-hidden="true" />}
                    <span>{creditBalance} cr</span>
                  </span>
                )}
              </button>
            );
          })}

          <button
            type="button"
            onClick={() => setIsNotificationsDrawerOpen(true)}
            className="t-sidebar-item"
            title={
              collapsed
                ? dir === 'rtl'
                  ? `التنبيهات (${unreadAlerts})`
                  : `Notifications (${unreadAlerts})`
                : undefined
            }
          >
            <span className="t-sidebar-item-left">
              <TailoredIcon name="bell" size={16} color="var(--chalk)" />
              {!collapsed && <span>{dir === 'rtl' ? 'التنبيهات' : 'Notifications'}</span>}
            </span>
            {!collapsed && unreadAlerts > 0 && (
              <span className="t-sidebar-badge t-sidebar-badge--alert">{unreadAlerts}</span>
            )}
            {collapsed && unreadAlerts > 0 && <span className="t-sidebar-mini-dot" />}
          </button>
        </nav>

        {/* Bottom Identity & Quick Account Menu */}
        <div className="t-sidebar-profile-wrap" ref={accountMenuRef}>
          <button
            type="button"
            className={`t-sidebar-profile-btn ${accountMenuOpen ? 't-sidebar-profile-btn--open' : ''}`}
            onClick={() => setAccountMenuOpen((v) => !v)}
            aria-haspopup="menu"
            aria-expanded={accountMenuOpen}
            title={collapsed ? `${fullName} · Account menu` : 'Open quick account actions'}
          >
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                minWidth: 0,
              }}
            >
              <span className="t-sidebar-avatar">{initials || 'M'}</span>
              {!collapsed && (
                <span style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                  <span
                    style={{
                      fontSize: 13,
                      fontWeight: 600,
                      color: 'var(--paper)',
                      lineHeight: 1.25,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {fullName}
                  </span>
                  <span
                    style={{
                      fontSize: 11.5,
                      color: 'var(--n500)',
                      lineHeight: 1.3,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {activePersona?.target_title || 'Candidate'} ·{' '}
                    <span className="t-mono" style={{ color: 'var(--kraft)', fontSize: 10.5 }}>
                      {activeRegionalPhone}
                    </span>
                  </span>
                </span>
              )}
            </span>
            {!collapsed && (
              <span
                style={{
                  transform: accountMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.16s ease',
                  flexShrink: 0,
                  display: 'inline-flex',
                }}
              >
                <TailoredIcon name="chevronDown" size={12} color="var(--chalk)" />
              </span>
            )}
          </button>

          {accountMenuOpen && (
            <div className="t-sidebar-account-menu" role="menu" aria-label="Account management">
              <div style={{ padding: '6px 10px 8px', marginBottom: 4, borderBottom: '1px solid rgba(26, 20, 18, 0.08)' }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)' }}>{fullName}</div>
                <div className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                  {userEmail}
                </div>
              </div>

              <button
                type="button"
                role="menuitem"
                className="t-atelier-menu-row"
                onClick={() => {
                  setAccountMenuOpen(false);
                  setIsIdentityDrawerOpen(true);
                }}
              >
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                  <TailoredIcon name="user" size={14} color="var(--ink)" />
                  <span>Switch Persona &amp; Phone</span>
                </span>
              </button>

              <button
                type="button"
                role="menuitem"
                className="t-atelier-menu-row"
                onClick={() => {
                  setDir(dir === 'ltr' ? 'rtl' : 'ltr');
                  setAccountMenuOpen(false);
                }}
              >
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                  <TailoredIcon name="globe" size={14} color="var(--ink)" />
                  <span>{dir === 'ltr' ? 'Switch to العربية (RTL)' : 'Switch to English (LTR)'}</span>
                </span>
              </button>

              <button
                type="button"
                role="menuitem"
                className="t-atelier-menu-row"
                onClick={() => {
                  setAccountMenuOpen(false);
                  setIsShortcutsHelpOpen(true);
                }}
              >
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                  <TailoredIcon name="command" size={14} color="var(--ink)" />
                  <span>Keyboard Shortcuts</span>
                </span>
              </button>

              <div style={{ height: 1, background: 'rgba(26, 20, 18, 0.08)', margin: '4px 6px' }} />

              <button
                type="button"
                role="menuitem"
                className="t-atelier-menu-row t-atelier-menu-row--danger"
                onClick={() => {
                  setAccountMenuOpen(false);
                  signOut();
                }}
              >
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                  <TailoredIcon name="logout" size={14} color="var(--alarm)" />
                  <span>Sign out</span>
                </span>
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
