export const API_BASE = '/api/v1';

const ACCESS_TOKEN_KEY = 'tailored_access_token_v1';
const REFRESH_TOKEN_KEY = 'tailored_refresh_token_v1';

export class ApiError extends Error {
  status: number;
  errorCode?: string;
  traceId?: string;
  metadata?: Record<string, unknown>;

  constructor(status: number, message: string, payload?: Record<string, unknown>) {
    super(message);
    this.status = status;
    this.errorCode = typeof payload?.error_code === 'string' ? payload.error_code : undefined;
    this.traceId = typeof payload?.trace_id === 'string' ? payload.trace_id : undefined;
    this.metadata = (payload?.metadata as Record<string, unknown>) || undefined;
  }
}

export function getAccessToken(): string | null {
  try {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setAuthTokens(accessToken: string | null, refreshToken?: string | null): void {
  try {
    if (accessToken) {
      localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    } else {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
    }
    if (refreshToken !== undefined) {
      if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
      } else {
        localStorage.removeItem(REFRESH_TOKEN_KEY);
      }
    }
  } catch {
    // ignore storage quota issues
  }
}

export function generateTraceparent(): string {
  const hex = (bytesLen: number) => {
    const arr = new Uint8Array(bytesLen);
    crypto.getRandomValues(arr);
    return Array.from(arr, (b) => b.toString(16).padStart(2, '0')).join('');
  };
  return `00-${hex(16)}-${hex(8)}-01`;
}

let refreshPromise: Promise<string | null> | null = null;

async function tryRefreshAccessToken(): Promise<string | null> {
  const rt = getRefreshToken();
  if (!rt) return null;
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', traceparent: generateTraceparent() },
        body: JSON.stringify({ refresh_token: rt }),
      });
      if (!res.ok) {
        setAuthTokens(null, null);
        return null;
      }
      const data = await res.json();
      setAuthTokens(data.access_token, data.refresh_token);
      return data.access_token as string;
    } catch {
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export interface ApiFetchOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  featureKey?: string;
  idempotencyKey?: string;
  skipAuth?: boolean;
  skipAuthRefresh?: boolean;
  timeoutMs?: number;
}

export async function apiFetchRaw(path: string, opts: ApiFetchOptions = {}): Promise<Response> {
  const url = path.startsWith('http') ? path : `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
  const headers: Record<string, string> = {
    traceparent: generateTraceparent(),
    ...(opts.headers || {}),
  };
  if (opts.body !== undefined && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  if (opts.featureKey) {
    headers['X-Feature-Key'] = opts.featureKey;
  }
  if (opts.idempotencyKey) {
    headers['Idempotency-Key'] = opts.idempotencyKey;
  }

  const token = !opts.skipAuth ? getAccessToken() : null;
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), opts.timeoutMs ?? 15000);

  try {
    let res = await fetch(url, {
      method: opts.method || 'GET',
      headers,
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
      signal: controller.signal,
    });

    if (res.status === 401 && !opts.skipAuth && !opts.skipAuthRefresh) {
      const nextToken = await tryRefreshAccessToken();
      if (nextToken) {
        headers['Authorization'] = `Bearer ${nextToken}`;
        res = await fetch(url, {
          method: opts.method || 'GET',
          headers,
          body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
        });
      }
    }
    return res;
  } finally {
    clearTimeout(timeout);
  }
}

export async function apiFetch<T = unknown>(path: string, opts: ApiFetchOptions = {}): Promise<T> {
  const res = await apiFetchRaw(path, opts);
  if (!res.ok) {
    let payload: Record<string, unknown> = {};
    try {
      payload = await res.json();
    } catch {
      // ignore non-json
    }
    const msg =
      (typeof payload.detail === 'string' && payload.detail) ||
      (typeof payload.title === 'string' && payload.title) ||
      `HTTP ${res.status}`;
    throw new ApiError(res.status, msg, payload);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
