/**
 * Jobs API Client for Tailored Job Radar & Automated Ingestion
 */

import { apiFetchRaw, getAccessToken } from './apiClient';

export interface JobItem {
  id: number;
  server_id?: string;
  source_id: string;
  title: string;
  company_name: string;
  location: string;
  url: string;
  raw_description: string;
  fit_score: number;
  is_high_match: boolean;
  source_type: string;
  parsed_skills: string[];
  responsibilities: string[];
  location_type: string;
  created_at: string;
  recruiter_email?: string | null;
}

const JOB_ID_MAP_KEY = 'tailored_job_uuid_map_v1';

function hashToSafeInt(val: string): number {
  let h = 2166136261;
  for (let i = 0; i < val.length; i += 1) {
    h ^= val.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 1) % 90000000 + 10000;
}

function loadIdMap(): Record<string, string> {
  try {
    const raw = localStorage.getItem(JOB_ID_MAP_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveIdMapping(numId: number, serverId: string): void {
  try {
    const m = loadIdMap();
    m[String(numId)] = serverId;
    localStorage.setItem(JOB_ID_MAP_KEY, JSON.stringify(m));
  } catch {
    // ignore storage quota
  }
}

export function resolveServerJobId(jobId: number | string, explicitServerId?: string): string {
  if (explicitServerId) return explicitServerId;
  const s = String(jobId);
  if (/^[0-9a-f]{8}-[0-9a-f]{4}-/i.test(s)) return s;
  const map = loadIdMap();
  return map[s] || s;
}

export function normalizeServerJob(raw: any): JobItem {
  const rawId = raw?.id ?? raw?.source_id ?? Date.now();
  const isDigits = typeof rawId === 'number' || /^\d+$/.test(String(rawId));
  const numericId = isDigits ? Number(rawId) : hashToSafeInt(String(rawId));
  const serverId = typeof rawId === 'string' && !/^\d+$/.test(rawId) ? rawId : raw?.server_id;
  if (serverId) {
    saveIdMapping(numericId, serverId);
  }
  return {
    id: numericId,
    server_id: serverId || (isDigits ? undefined : String(rawId)),
    source_id: String(raw?.source_id || rawId),
    title: String(raw?.title || 'Engineering Role'),
    company_name: String(raw?.company_name || 'Company'),
    location: String(raw?.location || 'MENA / Remote'),
    url: String(raw?.url || ''),
    raw_description: String(raw?.raw_description || ''),
    fit_score: Number(raw?.fit_score ?? 80),
    is_high_match: Boolean(raw?.is_high_match ?? (Number(raw?.fit_score ?? 80) >= 80)),
    source_type: String(raw?.source_type || 'web'),
    parsed_skills: Array.isArray(raw?.parsed_skills) ? raw.parsed_skills : [],
    responsibilities: Array.isArray(raw?.responsibilities) ? raw.responsibilities : [],
    location_type: String(raw?.location_type || raw?.work_mode || 'Hybrid'),
    created_at: String(raw?.created_at || new Date().toISOString()),
    recruiter_email: raw?.recruiter_email ?? null,
  };
}

export function extractEmail(text: string): string | null {
  if (!text) return null;
  const match = text.match(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/);
  if (match) {
    const email = match[0];
    if (!/\.(png|jpg|jpeg|gif|svg|webp)$/i.test(email)) {
      return email;
    }
  }
  return null;
}

export interface AutoSearchParams {
  profile_id?: number;
  persona_id?: string;
  query?: string;
  location?: string;
  min_score?: number;
  enable_live_apify?: boolean;
  source?: string;
}

export interface IngestUrlParams {
  url: string;
  profile_id?: number;
  persona_id?: string;
}

export interface ExtractDescriptionParams {
  description: string;
  company_name?: string;
  title?: string;
  url?: string;
  profile_id?: number;
  persona_id?: string;
}

export interface JobFilters {
  query?: string;
  location?: string;
  min_score?: number;
  source?: string;
  limit?: number;
  skip?: number;
}

// Fallback high-quality curated dataset for offline resilience
const FALLBACK_RADAR_JOBS: JobItem[] = [
  {
    id: 101,
    source_id: 'linkedin_mena_101',
    title: 'Lead Data Scientist (Dynamic Pricing & Fleet Optimization)',
    company_name: 'Swvl',
    location: 'Cairo, Egypt (Hybrid)',
    url: 'https://www.linkedin.com/jobs/view/3920192801',
    raw_description:
      'Swvl is seeking a Lead Data Scientist to build dynamic route pricing regression models and predictive demand forecasting algorithms. You will work with Python, PyTorch, SQL, and FastAPI. Experience deploying ML microservices using Docker and PostgreSQL required. 3+ years experience.',
    fit_score: 94.2,
    is_high_match: true,
    source_type: 'linkedin',
    parsed_skills: ['Python', 'PyTorch', 'SQL', 'FastAPI', 'Docker', 'PostgreSQL'],
    responsibilities: [
      'Architect dynamic route pricing algorithms',
      'Deploy low-latency inference endpoints with FastAPI',
      'Optimize fleet capacity using predictive regression',
    ],
    location_type: 'Hybrid',
    created_at: new Date().toISOString(),
  },
  {
    id: 102,
    source_id: 'linkedin_mena_102',
    title: 'Senior Machine Learning Engineer (Search & Recommendations)',
    company_name: 'Noon',
    location: 'Riyadh, Saudi Arabia',
    url: 'https://www.linkedin.com/jobs/view/3920192802',
    raw_description:
      'Join Noon in Riyadh as a Senior ML Engineer. We are designing high-throughput product recommendation engines and customer churn early-warning predictors. Tech stack: Python, PyTorch, HuggingFace, Docker, FastAPI, and PostgreSQL. 3+ years experience. Competitive tax-free package.',
    fit_score: 89.5,
    is_high_match: true,
    source_type: 'linkedin',
    parsed_skills: ['Machine Learning', 'Python', 'PyTorch', 'HuggingFace', 'Docker', 'FastAPI'],
    responsibilities: [
      'Scale product search and personalized recommendation models',
      'Build feature stores and continuous ML training pipelines',
      'Deploy real-time inference containers on Kubernetes',
    ],
    location_type: 'On-site',
    created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
  },
  {
    id: 103,
    source_id: 'wuzzuf_mena_103',
    title: 'Senior Product Data Analyst (Cross-functional Growth)',
    company_name: 'Fawry Fintech',
    location: 'Cairo, Egypt',
    url: 'https://wuzzuf.net/jobs/p/fawry-data-analyst-103',
    raw_description:
      'Fawry is hiring a Senior Product Data Analyst to transform relational database transactions into executive decision dashboards. Must be fluent in complex SQL, PostgreSQL, Python (Pandas), Tableau, and Power BI. Experience formulating KPI metrics and cohort retention analyses required.',
    fit_score: 86.8,
    is_high_match: true,
    source_type: 'wuzzuf',
    parsed_skills: ['SQL', 'PostgreSQL', 'Python', 'Pandas', 'Tableau', 'Power BI'],
    responsibilities: [
      'Formulate executive growth metrics and cohort retention models',
      'Write optimized analytical SQL queries over multi-terabyte tables',
      'Design executive Tableau and Metabase business intelligence dashboards',
    ],
    location_type: 'Hybrid',
    created_at: new Date(Date.now() - 3600000 * 8).toISOString(),
  },
  {
    id: 104,
    source_id: 'linkedin_mena_104',
    title: 'Staff AI & Inference Systems Engineer',
    company_name: 'Datadog',
    location: 'Worldwide (Remote)',
    url: 'https://www.linkedin.com/jobs/view/3920192804',
    raw_description:
      'Datadog is looking for a Staff AI Engineer to optimize production LLM inference pipelines, RAG systems, and vector search backends using Python, FastAPI, Docker, and PyTorch. 100% remote worldwide.',
    fit_score: 79.4,
    is_high_match: false,
    source_type: 'linkedin',
    parsed_skills: ['Python', 'FastAPI', 'Docker', 'PyTorch', 'RAG', 'Vector Search'],
    responsibilities: [
      'Optimize latency for distributed inference endpoints',
      'Implement telemetry and observability for AI pipelines',
    ],
    location_type: 'Remote',
    created_at: new Date(Date.now() - 3600000 * 18).toISOString(),
  },
  {
    id: 105,
    source_id: 'wuzzuf_mena_105',
    title: 'AI & Computer Vision Specialist',
    company_name: 'Vodafone Intelligent Solutions (_VOIS)',
    location: 'Cairo, Egypt',
    url: 'https://wuzzuf.net/jobs/p/vois-computer-vision-105',
    raw_description:
      '_VOIS is expanding our core AI center of excellence. Looking for an AI Specialist skilled in Deep Learning, PyTorch, OpenCV, Python, and Docker containerization. 2-4 years experience. Hybrid work model.',
    fit_score: 77.0,
    is_high_match: false,
    source_type: 'wuzzuf',
    parsed_skills: ['Deep Learning', 'PyTorch', 'Python', 'Docker', 'OpenCV'],
    responsibilities: [
      'Develop computer vision models for automated document verification',
      'Deploy PyTorch inference containers into enterprise clusters',
    ],
    location_type: 'Hybrid',
    created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
  },
  {
    id: 106,
    source_id: 'linkedin_mena_106',
    title: 'Business Intelligence & Analytics Specialist',
    company_name: 'Careem (Uber)',
    location: 'Riyadh, Saudi Arabia',
    url: 'https://www.linkedin.com/jobs/view/3920192806',
    raw_description:
      'Careem is looking for a BI Specialist to build real-time ride tracking and captain retention dashboards. Requirements: SQL, Power BI, Python, Metabase, and A/B Testing metric formulation. 2+ years experience in Riyadh.',
    fit_score: 74.5,
    is_high_match: false,
    source_type: 'linkedin',
    parsed_skills: ['SQL', 'Power BI', 'Python', 'Metabase', 'A/B Testing'],
    responsibilities: [
      'Build executive dashboards tracking captain earnings and fulfillment rates',
      'Design experimentation A/B test frameworks for dispatching logic',
    ],
    location_type: 'On-site',
    created_at: new Date(Date.now() - 3600000 * 32).toISOString(),
  },
];

export const JobsAPI = {
  /**
   * Automatically derives queries from user profile and runs scraping + fit scoring
   */
  async triggerAutoSearch(params: AutoSearchParams): Promise<{ jobs: JobItem[]; isOffline: boolean }> {
    try {
      const res = await apiFetchRaw('/jobs/auto-search', {
        method: 'POST',
        body: params,
        featureKey: 'jobs.radar.search',
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const jobs = Array.isArray(data) ? data.map(normalizeServerJob) : [];
      return { jobs, isOffline: false };
    } catch (err) {
      console.warn('Backend auto-search unreachable. Using curated local dataset:', err);
      // Filter fallback jobs if query or location specified
      let filtered = [...FALLBACK_RADAR_JOBS];
      if (params.source && params.source !== 'all') {
        const src = params.source.toLowerCase();
        filtered = filtered.filter((j) => j.source_type.toLowerCase() === src);
      }
      if (params.query) {
        const q = params.query.toLowerCase();
        filtered = filtered.filter(
          (j) => j.title.toLowerCase().includes(q) || j.company_name.toLowerCase().includes(q)
        );
      }
      return { jobs: filtered.length > 0 ? filtered : FALLBACK_RADAR_JOBS, isOffline: true };
    }
  },

  /**
   * Ingests and scores a job posting directly from a provided URL (LinkedIn, Wuzzuf, etc.)
   */
  async ingestJobFromUrl(params: IngestUrlParams): Promise<{ job: JobItem; isOffline: boolean }> {
    try {
      const res = await apiFetchRaw('/jobs/ingest-url', {
        method: 'POST',
        body: params,
        featureKey: 'jobs.ingest.url',
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return { job: normalizeServerJob(data), isOffline: false };
    } catch (err) {
      console.warn('Backend URL ingestion unavailable, resolving via local heuristics:', err);
      // Fallback matching against curated dataset or synthesizing a job item
      const clean = params.url.toLowerCase();
      const existing = FALLBACK_RADAR_JOBS.find(
        (j) => j.url.toLowerCase() === clean || clean.includes(j.url.toLowerCase())
      );
      if (existing) {
        return { job: existing, isOffline: true };
      }

      // Synthesize clean fallback job item
      const isLinkedinPost =
        clean.includes('/posts/') ||
        clean.includes('/feed/update/') ||
        clean.includes('activity-') ||
        clean.includes('activity:');
      const isLinkedin = clean.includes('linkedin.com') || clean.includes('lnkd.in');
      const isWuzzuf = clean.includes('wuzzuf.net');
      const domain = clean.replace(/https?:\/\//, '').split('/')[0].replace('www.', '');
      const pathParts = clean.split('/').filter(Boolean);
      const slug = pathParts[pathParts.length - 1] || 'opportunity';
      const titleWords = slug
        .replace(/[-_]+/g, ' ')
        .replace(/activity\s*\d+/gi, '')
        .replace(/\d+/g, '')
        .trim();
      const baseTitle =
        titleWords.length > 3
          ? titleWords
              .split(' ')
              .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
              .join(' ')
          : isLinkedinPost
          ? 'Recruiter Hiring Opportunity'
          : 'Ingested Career Opportunity';

      const title = isLinkedinPost && !baseTitle.toLowerCase().includes('recruiter post')
        ? `${baseTitle} (Recruiter Post)`
        : baseTitle;

      const fallbackJob: JobItem = {
        id: Math.floor(Math.random() * 90000) + 10000,
        source_id: isLinkedinPost ? `linkedin_post_${Date.now()}` : `url_ingested_${Date.now()}`,
        title,
        company_name: isLinkedinPost
          ? 'LinkedIn Recruiter'
          : isLinkedin
          ? 'LinkedIn Job Role'
          : isWuzzuf
          ? 'Wuzzuf Employer'
          : domain.split('.')[0].toUpperCase(),
        location: isWuzzuf ? 'Cairo, Egypt' : 'Global / Remote',
        url: params.url,
        raw_description: `Position: ${title}. Ingested directly from URL: ${params.url}. Tailored has extracted key requirements for candidate alignment.`,
        fit_score: 88.5,
        is_high_match: true,
        source_type: isLinkedinPost ? 'linkedin_posts' : isLinkedin ? 'linkedin' : isWuzzuf ? 'wuzzuf' : 'web',
        parsed_skills: ['Python', 'SQL', 'FastAPI', 'Docker', 'PostgreSQL'],
        responsibilities: [
          `Execute high-stakes engineering requirements as a ${title}.`,
          'Collaborate cross-functionally to achieve architectural and product goals.',
        ],
        location_type: 'Hybrid',
        created_at: new Date().toISOString(),
      };
      return { job: fallbackJob, isOffline: true };
    }
  },

  /**
   * Auto-extracts structured job requirements and recruiter contact from a pasted raw description.
   */
  async extractJobFromDescription(params: ExtractDescriptionParams): Promise<{ job: JobItem; isOffline: boolean }> {
    try {
      const res = await apiFetchRaw('/jobs/extract-description', {
        method: 'POST',
        body: params,
        featureKey: 'jobs.ingest.description',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const raw = await res.json();
      return { job: normalizeServerJob(raw), isOffline: false };
    } catch {
      // Offline fallback heuristic
      const email = extractEmail(params.description);
      const titleMatch = params.description.match(
        /(?:hiring(?:\s+for)?|looking\s+for\s+(?:a|an)?|position\s*:|role\s*:|title\s*:)\s*([A-Za-z0-9\s/&+\-_()]{3,60})/i
      );
      const inferredTitle = params.title || (titleMatch ? titleMatch[1].trim() : 'Senior Technical Engineer');
      const companyMatch = params.description.match(
        /(?:at|@|company\s*:?)\s*([A-Z][A-Za-z0-9&.\-_]{2,30})/
      );
      const inferredCompany =
        params.company_name ||
        (companyMatch
          ? companyMatch[1].trim()
          : email
          ? email.split('@')[1].split('.')[0].toUpperCase()
          : 'Target Organization');

      const fallbackJob: JobItem = {
        id: Date.now(),
        source_id: `offline_recruiter_${Date.now()}`,
        title: inferredTitle,
        company_name: inferredCompany,
        location: 'Remote / Hybrid',
        url: params.url || '',
        raw_description: params.description,
        fit_score: 88.0,
        is_high_match: true,
        source_type: 'recruiter_post',
        parsed_skills: ['Python', 'SQL', 'FastAPI', 'Docker'],
        responsibilities: ['Architect scalable systems', 'Collaborate with cross-functional teams'],
        location_type: 'Hybrid',
        created_at: new Date().toISOString(),
        recruiter_email: email,
      };
      return { job: fallbackJob, isOffline: true };
    }
  },

  /**
   * Fetches saved jobs with query, location, and min_score filters
   */
  async listJobs(filters: JobFilters = {}): Promise<{ jobs: JobItem[]; isOffline: boolean }> {
    try {
      const queryParams = new URLSearchParams();
      if (filters.query) queryParams.set('query', filters.query);
      if (filters.location) queryParams.set('location', filters.location);
      if (filters.min_score) queryParams.set('min_score', filters.min_score.toString());
      if (filters.source) queryParams.set('source', filters.source);
      if (filters.limit) queryParams.set('limit', filters.limit.toString());
      if (filters.skip) queryParams.set('skip', filters.skip.toString());

      const qs = queryParams.toString();
      const hasToken = Boolean(getAccessToken());
      const endpoint = hasToken ? `/jobs${qs ? `?${qs}` : ''}` : '/explore/jobs';
      const res = await apiFetchRaw(endpoint, { skipAuth: !hasToken });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const jobs = Array.isArray(data) ? data.map(normalizeServerJob) : [];
      return { jobs, isOffline: false };
    } catch {
      let filtered = [...FALLBACK_RADAR_JOBS];
      if (filters.query) {
        const q = filters.query.toLowerCase();
        filtered = filtered.filter(
          (j) => j.title.toLowerCase().includes(q) || j.company_name.toLowerCase().includes(q)
        );
      }
      if (filters.location && filters.location !== 'all') {
        const loc = filters.location.toLowerCase();
        filtered = filtered.filter((j) => j.location.toLowerCase().includes(loc));
      }
      if (filters.min_score) {
        filtered = filtered.filter((j) => j.fit_score >= (filters.min_score || 0));
      }
      if (filters.source && filters.source !== 'all') {
        filtered = filtered.filter((j) => j.source_type.toLowerCase() === filters.source?.toLowerCase());
      }
      return { jobs: filtered, isOffline: true };
    }
  },

  /**
   * Retrieves single job detail
   */
  async getJobDetail(id: number): Promise<JobItem | null> {
    try {
      const serverId = resolveServerJobId(id);
      const res = await apiFetchRaw(`/jobs/${serverId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const raw = await res.json();
      return normalizeServerJob(raw);
    } catch {
      return FALLBACK_RADAR_JOBS.find((j) => j.id === id) || null;
    }
  },

  async saveInterestRemote(jobId: number, serverId?: string): Promise<void> {
    if (!getAccessToken()) return;
    const target = resolveServerJobId(jobId, serverId);
    await apiFetchRaw(`/interest/${target}`, { method: 'POST', featureKey: 'jobs.interest.save' }).catch(() => {});
  },

  async removeInterestRemote(jobId: number, serverId?: string): Promise<void> {
    if (!getAccessToken()) return;
    const target = resolveServerJobId(jobId, serverId);
    await apiFetchRaw(`/interest/${target}`, { method: 'DELETE', featureKey: 'jobs.interest.remove' }).catch(() => {});
  },

  async hideJobRemote(jobId: number, serverId?: string): Promise<void> {
    if (!getAccessToken()) return;
    const target = resolveServerJobId(jobId, serverId);
    await apiFetchRaw(`/jobs/${target}/hide`, { method: 'POST', featureKey: 'jobs.radar.hide' }).catch(() => {});
  },

  async unhideJobRemote(jobId: number, serverId?: string): Promise<void> {
    if (!getAccessToken()) return;
    const target = resolveServerJobId(jobId, serverId);
    await apiFetchRaw(`/jobs/${target}/hide`, { method: 'DELETE', featureKey: 'jobs.radar.unhide' }).catch(() => {});
  },
};
