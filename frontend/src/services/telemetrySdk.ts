import { API_BASE, generateTraceparent, getAccessToken } from './apiClient';

const FORBIDDEN_KEYS = new Set([
  'email',
  'phone',
  'phone_number',
  'raw_cv',
  'latex_content',
  'password',
  'notes',
  'message_text',
]);

interface QueuedTelemetryEvent {
  event_id: string;
  occurred_at: string;
  session_id: string;
  feature_key: string;
  event_name: string;
  route: string;
  persona_track: string;
  job_id?: string;
  doc_id?: string;
  duration_ms: number;
  scroll_depth_pct: number;
  numeric_value: number;
  properties: Record<string, unknown>;
}

const SESSION_ID = (() => {
  try {
    const existing = sessionStorage.getItem('tailored_tel_sid');
    if (existing) return existing;
    const sid = crypto.randomUUID ? crypto.randomUUID() : `sess_${Date.now()}`;
    sessionStorage.setItem('tailored_tel_sid', sid);
    return sid;
  } catch {
    return `sess_${Date.now()}`;
  }
})();

let buffer: QueuedTelemetryEvent[] = [];
let flushTimer: number | null = null;
let microSignalsEnabled = true;

function scrub(props: Record<string, unknown> = {}): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(props)) {
    if (!FORBIDDEN_KEYS.has(k.toLowerCase())) {
      out[k] = v;
    }
  }
  return out;
}

async function flushQueue(useBeacon = false): Promise<void> {
  if (flushTimer !== null) {
    window.clearTimeout(flushTimer);
    flushTimer = null;
  }
  if (buffer.length === 0) return;

  const batch = buffer.splice(0, 50);
  const body = JSON.stringify({ events: batch });

  if (useBeacon && typeof navigator !== 'undefined' && navigator.sendBeacon) {
    try {
      const blob = new Blob([body], { type: 'application/json' });
      if (navigator.sendBeacon(`${API_BASE}/telemetry/events`, blob)) {
        return;
      }
    } catch {
      // fall through to keepalive fetch
    }
  }

  const token = getAccessToken();
  try {
    await fetch(`${API_BASE}/telemetry/events`, {
      method: 'POST',
      keepalive: true,
      headers: {
        'Content-Type': 'application/json',
        traceparent: generateTraceparent(),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body,
    });
  } catch {
    // non-fatal telemetry drop
  }
}

if (typeof window !== 'undefined') {
  window.addEventListener('pagehide', () => {
    void flushQueue(true);
  });
}

export const TelemetrySDK = {
  setConsent(enabled: boolean): void {
    microSignalsEnabled = enabled;
  },

  track(
    eventName: string,
    featureKey: string,
    opts: {
      isMicroSignal?: boolean;
      route?: string;
      personaTrack?: string;
      jobId?: string | number;
      docId?: string;
      durationMs?: number;
      scrollDepthPct?: number;
      numericValue?: number;
      properties?: Record<string, unknown>;
    } = {}
  ): void {
    if (opts.isMicroSignal && !microSignalsEnabled) return;

    const jobIdStr = opts.jobId !== undefined ? String(opts.jobId) : undefined;
    const isUuid = jobIdStr ? /^[0-9a-f]{8}-[0-9a-f]{4}-/i.test(jobIdStr) : false;

    buffer.push({
      event_id: crypto.randomUUID ? crypto.randomUUID() : `ev_${Date.now()}_${Math.random()}`,
      occurred_at: new Date().toISOString(),
      session_id: SESSION_ID,
      feature_key: featureKey,
      event_name: eventName,
      route: opts.route || (typeof window !== 'undefined' ? window.location.pathname : '/'),
      persona_track: opts.personaTrack || 'default',
      job_id: isUuid ? jobIdStr : undefined,
      doc_id: opts.docId,
      duration_ms: opts.durationMs ?? 0,
      scroll_depth_pct: opts.scrollDepthPct ?? 0,
      numeric_value: opts.numericValue ?? 0,
      properties: scrub(opts.properties),
    });

    if (buffer.length >= 15) {
      void flushQueue(false);
    } else if (flushTimer === null && typeof window !== 'undefined') {
      flushTimer = window.setTimeout(() => {
        void flushQueue(false);
      }, 5000);
    }
  },

  flush(): Promise<void> {
    return flushQueue(false);
  },
};
