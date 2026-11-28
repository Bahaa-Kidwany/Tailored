import { apiFetch, apiFetchRaw, setAuthTokens } from './apiClient';

export interface AuthUserInfo {
  id: string;
  email: string;
  full_name: string;
  email_verified: boolean;
  role: string;
}

export interface AuthTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  session_id: string;
  user: AuthUserInfo;
  dev_otp?: string;
}

export interface WorkspacePreferencesPayload {
  default_home_route: string;
  list_density: 'cozy' | 'dense';
  default_studio_intensity: 'Surgical' | 'Metrics+' | 'Executive';
  preferred_currency: 'EGP' | 'SAR' | 'AED' | 'USD';
  chat_side: 'left' | 'right';
  collapsed_rail: boolean;
}

export interface PrivacyConsentsPayload {
  analytics_micro_signals: boolean;
  ai_passive_learning: boolean;
  proactive_nudges: boolean;
}

export interface AccountSecurityStatus {
  email: string;
  email_verified: boolean;
  has_password: boolean;
  two_factor_enabled: boolean;
  connected_providers: string[];
  can_unlink_oauth: boolean;
}

export const AuthAPI = {
  async register(email: string, password: string, full_name: string): Promise<AuthTokenResponse> {
    const res = await apiFetch<AuthTokenResponse>('/auth/register', {
      method: 'POST',
      body: { email, password, full_name, device_label: navigator.userAgent.slice(0, 60) },
      featureKey: 'auth.register',
      skipAuth: true,
    });
    setAuthTokens(res.access_token, res.refresh_token);
    return res;
  },

  async login(email: string, password: string, totp_code?: string): Promise<AuthTokenResponse> {
    const res = await apiFetch<AuthTokenResponse>('/auth/login', {
      method: 'POST',
      body: { email, password, totp_code, device_label: navigator.userAgent.slice(0, 60) },
      featureKey: 'auth.login.password',
      skipAuth: true,
    });
    setAuthTokens(res.access_token, res.refresh_token);
    return res;
  },

  async oauthCallback(provider: 'google' | 'linkedin', provider_user_id: string, email: string, full_name: string) {
    const res = await apiFetch<AuthTokenResponse>(`/auth/oauth/${provider}/callback`, {
      method: 'POST',
      body: { provider_user_id, email, full_name },
      featureKey: 'auth.login.oauth',
      skipAuth: true,
    });
    setAuthTokens(res.access_token, res.refresh_token);
    return res;
  },

  async logout(): Promise<void> {
    try {
      await apiFetch('/auth/logout', { method: 'POST', featureKey: 'auth.session.revoke', skipAuthRefresh: true });
    } catch {
      // always clear local session
    } finally {
      setAuthTokens(null, null);
    }
  },

  async verifyEmail(email: string, code: string): Promise<{ verified: boolean }> {
    return apiFetch('/auth/verify-email', {
      method: 'POST',
      body: { email, code },
      featureKey: 'auth.otp.verify',
      skipAuth: true,
    });
  },

  async resendOtp(email: string, purpose: string = 'verify_email'): Promise<{ sent: boolean; dev_otp?: string }> {
    return apiFetch('/auth/otp/resend', { method: 'POST', body: { email, purpose }, skipAuth: true });
  },

  async forgotPassword(email: string): Promise<{ sent: boolean; dev_otp?: string }> {
    return apiFetch('/auth/forgot-password', { method: 'POST', body: { email }, skipAuth: true });
  },

  async resetPassword(email: string, code: string, new_password: string): Promise<{ reset: boolean }> {
    return apiFetch('/auth/reset-password', {
      method: 'POST',
      body: { email, code, new_password },
      featureKey: 'auth.password.reset',
      skipAuth: true,
    });
  },

  async getSecurityStatus(): Promise<AccountSecurityStatus> {
    return apiFetch('/account/security');
  },

  async changePassword(new_password: string, current_password?: string): Promise<{ updated: boolean }> {
    return apiFetch('/account/change-password', {
      method: 'POST',
      body: { current_password, new_password },
    });
  },

  async unlinkOAuth(provider: string): Promise<{ unlinked: string }> {
    return apiFetch(`/account/oauth/${provider}`, { method: 'DELETE' });
  },

  async setup2fa(): Promise<{ secret: string; otpauth_uri: string; recovery_codes: string[] }> {
    return apiFetch('/account/2fa/setup', { method: 'POST' });
  },

  async enable2fa(code: string): Promise<{ enabled: boolean }> {
    return apiFetch('/account/2fa/enable', {
      method: 'POST',
      body: { code },
      featureKey: 'auth.2fa.enable',
    });
  },

  async disable2fa(code: string): Promise<{ enabled: boolean }> {
    return apiFetch('/account/2fa/disable', { method: 'POST', body: { code } });
  },

  async listSessions(): Promise<Array<{ id: string; device: string; location: string; last_active: string; current: boolean }>> {
    return apiFetch('/account/sessions');
  },

  async revokeSession(sessionId: string): Promise<void> {
    await apiFetch(`/account/sessions/${sessionId}`, {
      method: 'DELETE',
      featureKey: 'auth.session.revoke',
    });
  },

  async getPreferences(): Promise<WorkspacePreferencesPayload> {
    return apiFetch('/account/preferences');
  },

  async updatePreferences(patch: Partial<WorkspacePreferencesPayload>): Promise<WorkspacePreferencesPayload> {
    return apiFetch('/account/preferences', {
      method: 'PATCH',
      body: patch,
      featureKey: 'account.preferences.update',
    });
  },

  async getPrivacy(): Promise<PrivacyConsentsPayload> {
    return apiFetch('/account/privacy');
  },

  async updatePrivacy(patch: Partial<PrivacyConsentsPayload>): Promise<PrivacyConsentsPayload> {
    return apiFetch('/account/privacy', {
      method: 'PATCH',
      body: patch,
      featureKey: 'account.privacy.update',
    });
  },

  async getFlags(): Promise<Record<string, { enabled: boolean; rollout_percent: number }>> {
    return apiFetch('/flags', { skipAuth: true });
  },

  async exportArchive(): Promise<Blob> {
    const req = await apiFetch<{ export_id: string; download_url: string }>('/account/export', {
      method: 'POST',
      featureKey: 'account.gdpr.export',
    });
    const res = await apiFetchRaw(`/account/export/${req.export_id}`);
    if (!res.ok) throw new Error(`Export failed (${res.status})`);
    return res.blob();
  },

  async deleteAccount(confirm: string = 'DELETE', password?: string): Promise<void> {
    await apiFetch('/account', {
      method: 'DELETE',
      body: { confirm, password },
      featureKey: 'account.gdpr.erase',
    });
    setAuthTokens(null, null);
  },
};
