import { API_BASE, apiFetch, getAccessToken } from './apiClient';
import type { NotificationItem } from '../context/WorkspaceContext';

export const NotificationsAPI = {
  async list(category?: string, unreadOnly: boolean = false): Promise<NotificationItem[]> {
    const params = new URLSearchParams();
    if (category && category !== 'all') params.set('category', category);
    if (unreadOnly) params.set('unread_only', 'true');
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiFetch(`/notifications${qs}`);
  },

  async markRead(notifId: string): Promise<void> {
    await apiFetch(`/notifications/${notifId}/read`, {
      method: 'PATCH',
      featureKey: 'notifications.inbox.read',
    });
  },

  async snooze(notifId: string, hours: number = 72): Promise<void> {
    await apiFetch(`/notifications/${notifId}/snooze`, {
      method: 'PATCH',
      body: { hours },
      featureKey: 'notifications.snooze',
    });
  },

  async markAllRead(): Promise<void> {
    await apiFetch('/notifications/mark-all-read', { method: 'POST' });
  },

  subscribeStream(onNotification: (item: NotificationItem) => void): () => void {
    const token = getAccessToken();
    if (!token || typeof EventSource === 'undefined') {
      return () => {};
    }
    const source = new EventSource(`${API_BASE}/notifications/stream?token=${encodeURIComponent(token)}`);
    source.addEventListener('notification', (ev) => {
      try {
        const parsed = JSON.parse((ev as MessageEvent).data);
        const item = parsed.data || parsed;
        if (item?.id) onNotification(item as NotificationItem);
      } catch {
        // ignore parse errors
      }
    });
    return () => {
      source.close();
    };
  },
};
