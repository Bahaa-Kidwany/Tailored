import React, { useEffect } from 'react';
import { WorkspaceProvider, useWorkspace } from './context/WorkspaceContext';
import { AtelierSidebar } from './components/shell/AtelierSidebar';
import { IdentityDrawer } from './components/shell/IdentityDrawer';
import { CommandPalette } from './components/shell/CommandPalette';
import { NotificationsDrawer, ShortcutsHelpModal } from './components/shell/NotificationsDrawer';
import { ToastStack, OfflineBanner } from './components/shell/ToastStack';
import { QuickPeekJobDrawer } from './components/common/QuickPeekJobDrawer';
import { OutOfCreditsModal } from './components/common/OutOfCreditsModal';

import { LandingPage } from './pages/LandingPage';
import { GuestExplorePage } from './pages/GuestExplorePage';
import { AuthPage } from './pages/AuthPage';
import {
  ForgotPasswordPage,
  ResetPasswordPage,
  VerifyEmailPage,
} from './pages/AuthRecoveryPages';
import { OnboardingPage } from './pages/OnboardingPage';
import { CreditsGatePage } from './pages/CreditsGatePage';
import { DashboardPage } from './pages/DashboardPage';
import { RadarPage } from './pages/RadarPage';
import { JobDetailPage } from './pages/JobDetailPage';
import { CvStudioPage } from './pages/CvStudioPage';
import { CoverLetterStudioPage } from './pages/CoverLetterStudioPage';
import { PipelinePage } from './pages/PipelinePage';
import { ApplicationDetailPage } from './pages/ApplicationDetailPage';
import { MasterProfilePage } from './pages/MasterProfilePage';
import { PlansAndCreditsPage } from './pages/PlansAndCreditsPage';
import { AccountSettingsPage } from './pages/AccountSettingsPage';
import { NotificationsPage } from './pages/NotificationsPage';
import {
  NotFoundPage,
  ServerErrorView,
  ServerErrorBoundary,
  MaintenancePage,
  OfflineFallbackPage,
  LegalDocPage,
} from './pages/SystemAndLegalPages';

const WORKSPACE_SHELL_PREFIXES = [
  '/dashboard',
  '/radar',
  '/jobs',
  '/interest',
  '/studio',
  '/cover-letters',
  '/cvs',
  '/pipeline',
  '/profile',
  '/plans',
  '/account',
  '/notifications',
];

const AppRouter: React.FC = () => {
  const { currentPath, isAuthenticated, defaultHomeRoute, navigateTo } = useWorkspace();
  const clean = currentPath.length > 1 ? currentPath.replace(/\/+$/, '') : currentPath;

  useEffect(() => {
    if (clean === '/' && isAuthenticated) {
      navigateTo(defaultHomeRoute);
    }
  }, [clean, isAuthenticated, defaultHomeRoute, navigateTo]);

  const showWorkspaceShell =
    (clean === '/' && isAuthenticated) ||
    WORKSPACE_SHELL_PREFIXES.some(
      (prefix) => clean === prefix || clean.startsWith(`${prefix}/`)
    );
  const isDarkStudioRoute =
    (clean === '/' && isAuthenticated) ||
    clean === '/dashboard' ||
    clean === '/radar' ||
    clean === '/interest' ||
    clean === '/studio' ||
    clean === '/cvs' ||
    clean === '/cover-letters' ||
    clean === '/pipeline';

  const renderPage = () => {
    if (clean === '/') return isAuthenticated ? <DashboardPage /> : <LandingPage />;
    if (clean === '/explore') return <GuestExplorePage />;
    if (clean === '/login') return <AuthPage initialMode="signin" />;
    if (clean === '/register') return <AuthPage initialMode="signup" />;
    if (clean === '/forgot-password') return <ForgotPasswordPage />;
    if (clean === '/reset-password') return <ResetPasswordPage />;
    if (clean === '/verify-email') return <VerifyEmailPage />;
    if (clean === '/onboarding') return <OnboardingPage />;
    if (clean === '/trial') return <CreditsGatePage />;

    if (clean === '/dashboard') return <DashboardPage />;
    if (clean === '/radar') return <RadarPage />;
    if (/^\/jobs\/\d+$/.test(clean)) return <JobDetailPage />;
    if (clean === '/interest') return <RadarPage initialTab="saved" />;
    if (clean === '/cvs' || clean === '/studio') return <CvStudioPage />;
    if (clean === '/cover-letters') return <CoverLetterStudioPage />;
    if (clean === '/pipeline') return <PipelinePage />;
    if (/^\/pipeline\/[a-zA-Z0-9_-]+$/.test(clean)) return <ApplicationDetailPage />;
    if (clean === '/profile') return <MasterProfilePage />;
    if (clean === '/plans') return <PlansAndCreditsPage />;
    if (clean === '/account') return <AccountSettingsPage />;
    if (clean === '/notifications') return <NotificationsPage />;

    if (clean === '/500') return <ServerErrorView />;
    if (clean === '/maintenance') return <MaintenancePage />;
    if (clean === '/offline') return <OfflineFallbackPage />;
    if (clean === '/privacy') return <LegalDocPage mode="privacy" />;
    if (clean === '/terms') return <LegalDocPage mode="terms" />;
    return <NotFoundPage />;
  };

  return (
    <div className="t-app-shell">
      <OfflineBanner />
      {showWorkspaceShell ? (
        <div className={`t-workspace-frame ${isDarkStudioRoute ? 't-workspace-frame--dark' : ''}`}>
          <AtelierSidebar />
          <main className="t-workspace-main">{renderPage()}</main>
        </div>
      ) : (
        <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          {renderPage()}
        </div>
      )}

      {/* Global Atelier Overlays */}
      <IdentityDrawer />
      <CommandPalette />
      <NotificationsDrawer />
      <QuickPeekJobDrawer />
      <OutOfCreditsModal />
      <ShortcutsHelpModal />
      <ToastStack />
    </div>
  );
};

export function App() {
  return (
    <WorkspaceProvider>
      <ServerErrorBoundary>
        <AppRouter />
      </ServerErrorBoundary>
    </WorkspaceProvider>
  );
}

export default App;
