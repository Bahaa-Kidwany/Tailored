import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  ProfileAPI,
  SAMPLE_PROFILE,
  type FullProfileResponse,
  type UserProfilePayload,
} from '../services/profileApi';
import { JobsAPI, extractEmail, type JobItem } from '../services/jobsApi';
import {
  CvFitAPI,
  cleanCompanyName,
  cleanTargetJobTitle,
  cvDetailToSummary,
  type CvFitDetail,
  type CvFitSummary,
} from '../services/cvFitApi';
import { CoverLetterAPI, type CoverLetterItem } from '../services/coverLetterApi';
import {
  PipelineStorage,
  type PipelineItem,
  type PipelineStatus,
} from '../services/pipelineStorage';
import type { AiChatMessage } from '../components/common/CalmAiCoachSidecar';

export type CreditCurrency = 'EGP' | 'SAR' | 'AED' | 'USD';

export interface CreditPackOption {
  id: string;
  name: string;
  subtitle: string;
  credits: number;
  appsEquiv: string;
  prices: Record<CreditCurrency, { amount: number; label: string; perCredit: string }>;
  popular?: boolean;
  isFree?: boolean;
}

export const CREDIT_PACKS: CreditPackOption[] = [
  {
    id: 'free',
    name: 'Free Starter',
    subtitle: 'Included at onboarding',
    credits: 2,
    appsEquiv: '1 complete application',
    isFree: true,
    prices: {
      EGP: { amount: 0, label: '0 EGP', perCredit: '0 EGP' },
      SAR: { amount: 0, label: '0 SAR', perCredit: '0 SAR' },
      AED: { amount: 0, label: '0 AED', perCredit: '0 AED' },
      USD: { amount: 0, label: '$0', perCredit: '$0' },
    },
  },
  {
    id: 'starter',
    name: 'Starter',
    subtitle: 'Quick apply pack',
    credits: 5,
    appsEquiv: '2–3 applications',
    prices: {
      EGP: { amount: 49, label: '49 EGP', perCredit: '9.8 EGP/cr' },
      SAR: { amount: 12, label: '12 SAR', perCredit: '2.4 SAR/cr' },
      AED: { amount: 12, label: '12 AED', perCredit: '2.4 AED/cr' },
      USD: { amount: 2.99, label: '$2.99', perCredit: '$0.60/cr' },
    },
  },
  {
    id: 'hunter',
    name: 'Hunter',
    subtitle: 'Active daily search',
    credits: 25,
    appsEquiv: '12–15 applications',
    popular: true,
    prices: {
      EGP: { amount: 179, label: '179 EGP', perCredit: '7.1 EGP/cr' },
      SAR: { amount: 35, label: '35 SAR', perCredit: '1.4 SAR/cr' },
      AED: { amount: 34, label: '34 AED', perCredit: '1.36 AED/cr' },
      USD: { amount: 8.99, label: '$8.99', perCredit: '$0.36/cr' },
    },
  },
  {
    id: 'sprint',
    name: 'Sprint',
    subtitle: 'Full job switch',
    credits: 70,
    appsEquiv: '35–40 applications',
    prices: {
      EGP: { amount: 399, label: '399 EGP', perCredit: '5.7 EGP/cr' },
      SAR: { amount: 75, label: '75 SAR', perCredit: '1.07 SAR/cr' },
      AED: { amount: 72, label: '72 AED', perCredit: '1.03 AED/cr' },
      USD: { amount: 18.99, label: '$18.99', perCredit: '$0.27/cr' },
    },
  },
];

export interface CreditLedgerEntry {
  id: string;
  date: string;
  action: string;
  jobTarget: string;
  delta: number;
  balanceAfter: number;
  docId?: string;
}

export interface NotificationItem {
  id: string;
  category: 'match' | 'followup' | 'document' | 'credit';
  title: string;
  subtitle: string;
  timestamp: string;
  read: boolean;
  snoozedUntil?: string | null;
  jobId?: number;
  pipelineId?: string;
  actionLabel: string;
  targetPath: string;
}

export interface PendingIntent {
  type: 'tailor_job' | 'ingest_url' | 'ingest_jd' | 'search' | 'cv_upload' | 'save_interest' | 'inspect_fit';
  jobId?: number;
  query?: string;
  url?: string;
  label?: string;
}

export interface ToastNotice {
  id: string;
  message: string;
  variant?: 'info' | 'success' | 'warn' | 'error';
  undoLabel?: string;
  onUndo?: () => void;
}

export interface ActiveSessionDevice {
  id: string;
  device: string;
  location: string;
  lastActive: string;
  current: boolean;
}

export interface OutOfCreditsState {
  actionLabel: string;
  requiredCredits: number;
  onResume: () => void;
}

export interface InterviewRoundNote {
  id: string;
  round: string;
  date: string;
  interviewer: string;
  notes: string;
}

export interface PipelineExtras {
  recruiterName?: string;
  followUpDate?: string;
  interviewDate?: string;
  compensationNotes?: string;
  rounds: InterviewRoundNote[];
  frozenPdfName?: string;
  frozenAt?: string;
}

const KNOWN_EXACT_ROUTES = new Set([
  '/',
  '/explore',
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/verify-email',
  '/onboarding',
  '/trial',
  '/dashboard',
  '/radar',
  '/interest',
  '/cvs',
  '/studio',
  '/cover-letters',
  '/pipeline',
  '/profile',
  '/plans',
  '/account',
  '/notifications',
  '/maintenance',
  '/offline',
  '/privacy',
  '/terms',
  '/404',
  '/500',
]);

export function isValidAppPath(pathname: string): boolean {
  const clean = pathname.length > 1 ? pathname.replace(/\/+$/, '') : pathname;
  if (KNOWN_EXACT_ROUTES.has(clean)) return true;
  if (/^\/jobs\/\d+$/.test(clean)) return true;
  if (/^\/pipeline\/[a-zA-Z0-9_-]+$/.test(clean)) return true;
  return false;
}

const DEFAULT_SAMPLE_JOBS: JobItem[] = [
  {
    id: 101,
    source_id: 'linkedin_mena_101',
    title: 'Lead Data Scientist (Dynamic Pricing & Fleet Optimization)',
    company_name: 'Swvl',
    location: 'Cairo, Egypt (Hybrid)',
    url: 'https://www.linkedin.com/jobs/view/3920192801',
    raw_description:
      'Swvl is seeking a Lead Data Scientist to build dynamic route pricing regression models and predictive demand forecasting algorithms with Python, PyTorch, SQL, FastAPI, Docker, PostgreSQL, and AWS ECS. 3+ years production ML experience.',
    fit_score: 94.2,
    is_high_match: true,
    source_type: 'linkedin',
    parsed_skills: ['Python', 'PyTorch', 'SQL', 'FastAPI', 'Docker', 'PostgreSQL', 'AWS ECS'],
    responsibilities: [
      'Architect dynamic route pricing regression engines across Cairo and MENA corridors',
      'Deploy low-latency FastAPI inference endpoints on containerized clusters',
      'Optimize fleet capacity and utilization with predictive demand models',
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
      'Join Noon in Riyadh as a Senior Machine Learning Engineer designing product search ranking and personalized recommendation engines using Python, PyTorch, HuggingFace, Docker, FastAPI, and Kubernetes. 4+ years experience.',
    fit_score: 89.5,
    is_high_match: true,
    source_type: 'linkedin',
    parsed_skills: ['Python', 'PyTorch', 'HuggingFace', 'FastAPI', 'Docker', 'Kubernetes'],
    responsibilities: [
      'Scale real-time search ranking and personalized product recommendation services',
      'Build feature stores and continuous model evaluation pipelines',
      'Deploy inference containers across high-throughput GCC retail traffic',
    ],
    location_type: 'On-site',
    created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
  },
  {
    id: 103,
    source_id: 'wuzzuf_mena_103',
    title: 'Senior Product Data Analyst (Cross-Functional Growth)',
    company_name: 'Fawry Fintech',
    location: 'Cairo, Egypt',
    url: 'https://wuzzuf.net/jobs/p/fawry-senior-product-data-analyst',
    raw_description:
      'Fawry is hiring a Senior Product Data Analyst to drive merchant conversion telemetry, cohort experiments, SQL warehousing, Python analytics, and executive KPI reporting across digital payments.',
    fit_score: 82.0,
    is_high_match: false,
    source_type: 'wuzzuf',
    parsed_skills: ['SQL', 'Python', 'PostgreSQL', 'Data Analytics', 'A/B Testing'],
    responsibilities: [
      'Own merchant payment funnel analytics and cohort retention metrics',
      'Partner with product squads to design A/B experiments and statistical evaluations',
    ],
    location_type: 'On-site',
    created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
  },
  {
    id: 104,
    source_id: 'linkedin_post_recruiter_104',
    title: 'Senior AI Systems Engineer (Direct Recruiter Post)',
    company_name: 'TechStart MENA',
    location: 'Remote (Egypt / KSA)',
    url: 'https://www.linkedin.com/feed/update/urn:li:activity:7192837465',
    raw_description:
      'Hiring immediately for a Senior AI Systems Engineer to build RAG evaluation harnesses, Python FastAPI orchestrators, and Dockerized LLM workflows. Send your tailored CV directly to sara.mansour@techstart-mena.io — 3+ years experience.',
    fit_score: 88.4,
    is_high_match: true,
    source_type: 'recruiter_post',
    parsed_skills: ['Python', 'FastAPI', 'Docker', 'PostgreSQL', 'LLMs'],
    responsibilities: [
      'Architect production LLM orchestration APIs and deterministic evaluation harnesses',
      'Collaborate directly with founders on enterprise Gulf deployments',
    ],
    location_type: 'Remote',
    created_at: new Date(Date.now() - 3600000 * 8).toISOString(),
    recruiter_email: 'sara.mansour@techstart-mena.io',
  },
  {
    id: 105,
    source_id: 'custom_post_105',
    title: 'Staff ML Platform Lead',
    company_name: 'Instabug',
    location: 'Cairo, Egypt (Hybrid)',
    url: 'https://www.linkedin.com/posts/instabug_ml-platform-lead-activity-719991122',
    raw_description:
      'We are looking for a Staff ML Platform Lead to scale anomaly detection pipelines over mobile telemetry using Python, PyTorch, Ray, Kafka, and Docker. Apply directly at careers@instabug-demo.io.',
    fit_score: 86.1,
    is_high_match: true,
    source_type: 'recruiter_post',
    parsed_skills: ['Python', 'PyTorch', 'Ray', 'Kafka', 'Docker', 'SQL'],
    responsibilities: [
      'Lead real-time crash anomaly clustering across millions of daily SDK events',
      'Mentor ML engineers on reproducible training and low-latency deployment',
    ],
    location_type: 'Hybrid',
    created_at: new Date(Date.now() - 3600000 * 72).toISOString(),
    recruiter_email: 'careers@instabug-demo.io',
  },
];

const DEFAULT_NOTIFICATIONS: NotificationItem[] = [
  {
    id: 'notif_1',
    category: 'match',
    title: '94% Strong Fit: Swvl — Lead Data Scientist',
    subtitle: 'Matched Python, PyTorch, FastAPI, SQL, Docker on Senior AI Engineer track.',
    timestamp: '2h ago',
    read: false,
    jobId: 101,
    actionLabel: 'Tailor CV · 1 cr',
    targetPath: '/studio?job_id=101',
  },
  {
    id: 'notif_2',
    category: 'followup',
    title: '7-Day Follow-Up Due: Instabug — Staff ML Platform Lead',
    subtitle: 'Applied 8 days ago to careers@instabug-demo.io with no logged reply yet.',
    timestamp: '6h ago',
    read: false,
    jobId: 105,
    pipelineId: 'pipe_105',
    actionLabel: 'Draft Follow-Up',
    targetPath: '/pipeline/pipe_105',
  },
  {
    id: 'notif_3',
    category: 'document',
    title: 'ATS PDF Compiled: TechStart MENA — Senior AI Systems Engineer',
    subtitle: 'Verified 1-page LaTeX compilation (91% page budget, zero overflow).',
    timestamp: 'Yesterday',
    read: true,
    jobId: 104,
    actionLabel: 'Open Studio',
    targetPath: '/studio?job_id=104',
  },
];

interface WorkspaceContextValue {
  // Routing
  currentPath: string;
  currentSearch: string;
  navigateTo: (path: string) => void;
  goBack: () => void;

  // Auth & Security
  isAuthenticated: boolean;
  userEmail: string;
  emailVerified: boolean;
  hasPassword: boolean;
  twoFactorEnabled: boolean;
  connectedSso: { google: boolean; linkedin: boolean };
  sessions: ActiveSessionDevice[];
  signIn: (email: string) => void;
  registerAccount: (fullName: string, email: string) => void;
  signOut: () => void;
  verifyOtpCode: (code: string) => boolean;
  updateAccountEmail: (email: string) => void;
  toggleTwoFactor: (enabled: boolean) => void;
  toggleSso: (provider: 'google' | 'linkedin') => void;
  revokeSession: (id: string) => void;

  // Pending Intent
  pendingIntent: PendingIntent | null;
  setPendingIntent: (intent: PendingIntent | null) => void;
  fulfillPendingIntent: () => void;

  // Profile & Active Persona
  currentProfile: FullProfileResponse | null;
  activePersonaId: string;
  setActivePersonaId: (id: string) => void;
  activeRegionalPhone: '+20' | '+966' | '+971';
  setActiveRegionalPhone: (code: '+20' | '+966' | '+971') => void;
  saveProfile: (payload: UserProfilePayload) => Promise<FullProfileResponse>;
  setPrimaryPersona: (personaId: string) => Promise<void>;

  // Credits Wallet
  creditBalance: number;
  creditCurrency: CreditCurrency;
  setCreditCurrency: (c: CreditCurrency) => void;
  lowBalanceThreshold: number;
  setLowBalanceThreshold: (n: number) => void;
  creditLedger: CreditLedgerEntry[];
  unlockedJobKeys: Set<string>;
  isJobUnlocked: (jobId: number, kind: 'cv' | 'cl') => boolean;
  requestCreditAction: (opts: {
    cost: number;
    unlockKey?: string;
    actionLabel: string;
    jobTarget: string;
    onAuthorized: () => Promise<void> | void;
  }) => Promise<void>;
  purchaseCreditPack: (packId: string) => void;

  // Jobs, Radar & Interest
  radarJobs: JobItem[];
  setRadarJobs: React.Dispatch<React.SetStateAction<JobItem[]>>;
  hiddenJobIds: Set<number>;
  hideJob: (jobId: number) => void;
  unhideJob: (jobId: number) => void;
  interestList: JobItem[];
  addToInterest: (job: JobItem) => void;
  removeFromInterest: (jobId: number) => void;
  ingestJobUrlOrText: (raw: string, opts?: { openInStudio?: boolean; onlySaveInterest?: boolean }) => Promise<JobItem | null>;
  runLiveSweep: (query?: string) => Promise<JobItem[]>;

  // Tailored CVs, Cover Letters & Continuous Studio Coach
  tailoredDocs: CvFitSummary[];
  activeStudioDoc: CvFitDetail | null;
  activeStudioJob: JobItem;
  setActiveStudioJob: (job: JobItem) => void;
  openJobInStudio: (job: JobItem, opts?: { skipCreditCheck?: boolean }) => Promise<void>;
  openJobInCoverLetters: (job: JobItem, opts?: { mode?: 'pitch' | 'letter' | 'followup' }) => void;
  openDocInStudio: (docId: string) => Promise<void>;
  registerStudioDoc: (detail: CvFitDetail) => void;
  deleteStudioDoc: (docId: string) => void;
  saveStudioDocUpdate: (detail: CvFitDetail) => void;
  forkSavedDoc: (docId: string) => Promise<void>;
  coverLetters: CoverLetterItem[];
  saveCoverLetter: (item: CoverLetterItem) => void;
  deleteCoverLetter: (docId: string) => void;
  coverLetterEntryMode: 'pitch' | 'letter' | 'followup';
  setCoverLetterEntryMode: (m: 'pitch' | 'letter' | 'followup') => void;
  coachThreads: Record<string, AiChatMessage[]>;
  updateCoachThread: (
    key: string,
    fallback: AiChatMessage[],
    updater: (curr: AiChatMessage[]) => AiChatMessage[]
  ) => void;
  resetCoachThread: (key: string, seed: AiChatMessage[]) => void;
  selectedCvByJob: Record<number, string>;
  setSelectedCvForJob: (jobId: number, cvId: string) => void;

  // Pipeline CRM
  pipelineItems: PipelineItem[];
  pipelineExtras: Record<string, PipelineExtras>;
  addToPipeline: (
    job: JobItem,
    status?: PipelineStatus,
    overrideEmail?: string | null,
    opts?: { tailoredCvDocId?: string | null; coverLetter?: CoverLetterItem | null; silent?: boolean }
  ) => PipelineItem | null;
  updatePipelineStage: (id: string, status: PipelineStatus) => void;
  updatePipelineEmail: (id: string, email: string) => void;
  updatePipelineExtras: (id: string, patch: Partial<PipelineExtras>) => void;
  removeFromPipeline: (id: string) => void;

  // Notifications
  notifications: NotificationItem[];
  markNotificationRead: (id: string) => void;
  markAllNotificationsRead: () => void;
  snoozeNotification: (id: string, label: string) => void;

  // Ergonomics, Overlays & Resilience
  dir: 'ltr' | 'rtl';
  setDir: (d: 'ltr' | 'rtl') => void;
  density: 'cozy' | 'compact';
  setDensity: (d: 'cozy' | 'compact') => void;
  defaultHomeRoute: '/dashboard' | '/radar' | '/studio';
  setDefaultHomeRoute: (r: '/dashboard' | '/radar' | '/studio') => void;
  defaultIntensity: 'Surgical' | 'Metrics+' | 'Executive';
  setDefaultIntensity: (i: 'Surgical' | 'Metrics+' | 'Executive') => void;
  notifThreshold: number;
  setNotifThreshold: (n: number) => void;
  notifCadence: 'instant' | 'daily' | 'off';
  setNotifCadence: (c: 'instant' | 'daily' | 'off') => void;
  resetAllPaneWidths: () => void;

  isIdentityDrawerOpen: boolean;
  setIsIdentityDrawerOpen: (b: boolean) => void;
  isCommandPaletteOpen: boolean;
  setIsCommandPaletteOpen: (b: boolean) => void;
  isNotificationsDrawerOpen: boolean;
  setIsNotificationsDrawerOpen: (b: boolean) => void;
  quickPeekJob: JobItem | null;
  setQuickPeekJob: (j: JobItem | null) => void;
  outOfCreditsState: OutOfCreditsState | null;
  closeOutOfCredits: () => void;
  isShortcutsHelpOpen: boolean;
  setIsShortcutsHelpOpen: (b: boolean) => void;

  toasts: ToastNotice[];
  pushToast: (message: string, opts?: { variant?: ToastNotice['variant']; undoLabel?: string; onUndo?: () => void }) => void;
  dismissToast: (id: string) => void;
  isOnline: boolean;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export const WorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [locationState, setLocationState] = useState<{ pathname: string; search: string }>(() => ({
    pathname: window.location.pathname || '/',
    search: window.location.search || '',
  }));
  const [prevPath, setPrevPath] = useState<string>('/dashboard');

  // Auth
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('tailored_auth_v2');
      return saved ? JSON.parse(saved).isAuthenticated : true;
    } catch {
      return true;
    }
  });
  const [userEmail, setUserEmail] = useState<string>('mostafa.eng@tailored.atelier');
  const [emailVerified, setEmailVerified] = useState<boolean>(true);
  const [hasPassword] = useState<boolean>(true);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState<boolean>(false);
  const [connectedSso, setConnectedSso] = useState({ google: true, linkedin: true });
  const [sessions, setSessions] = useState<ActiveSessionDevice[]>([
    { id: 'sess_1', device: 'Windows Desktop · Chrome', location: 'Cairo, Egypt', lastActive: 'Active now', current: true },
    { id: 'sess_2', device: 'MacBook Pro · Safari', location: 'Riyadh, KSA', lastActive: '3 days ago', current: false },
  ]);

  const [pendingIntent, setPendingIntent] = useState<PendingIntent | null>(null);

  // Profile
  const [currentProfile, setCurrentProfile] = useState<FullProfileResponse | null>({
    id: 1,
    profile: SAMPLE_PROFILE,
  });
  const [activePersonaId, setActivePersonaId] = useState<string>('data_scientist_track');
  const [activeRegionalPhone, setActiveRegionalPhone] = useState<'+20' | '+966' | '+971'>('+20');

  // Credits Wallet
  const [creditBalance, setCreditBalance] = useState<number>(() => {
    const raw = localStorage.getItem('tailored_credits_v2');
    return raw ? parseInt(raw, 10) : 14;
  });
  const [creditCurrency, setCreditCurrency] = useState<CreditCurrency>('EGP');
  const [lowBalanceThreshold, setLowBalanceThreshold] = useState<number>(2);
  const [unlockedJobKeys, setUnlockedJobKeys] = useState<Set<string>>(() => new Set(['cv_101', 'cl_101']));
  const [creditLedger, setCreditLedger] = useState<CreditLedgerEntry[]>([
    { id: 'led_1', date: 'Nov 20', action: 'Tailored CV (v1–v3)', jobTarget: 'Swvl — Lead Data Scientist', delta: -1, balanceAfter: 14, docId: 'doc_101' },
    { id: 'led_2', date: 'Nov 19', action: 'Cover Letter Draft', jobTarget: 'Swvl — Lead Data Scientist', delta: -1, balanceAfter: 15 },
    { id: 'led_3', date: 'Nov 15', action: 'Hunter Pack (Paymob #841)', jobTarget: '179 EGP Top-up', delta: 25, balanceAfter: 25 },
    { id: 'led_4', date: 'Nov 10', action: 'Free Starter Allocation', jobTarget: 'Onboarding Welcome', delta: 2, balanceAfter: 2 },
  ]);

  // Jobs & Interest
  const [radarJobs, setRadarJobs] = useState<JobItem[]>(DEFAULT_SAMPLE_JOBS);
  const [hiddenJobIds, setHiddenJobIds] = useState<Set<number>>(new Set());
  const [interestList, setInterestList] = useState<JobItem[]>(DEFAULT_SAMPLE_JOBS.slice(0, 4));

  // Docs & Studio
  const [tailoredDocs, setTailoredDocs] = useState<CvFitSummary[]>([]);
  const [activeStudioDoc, setActiveStudioDoc] = useState<CvFitDetail | null>(null);
  const [activeStudioJob, setActiveStudioJob] = useState<JobItem>(DEFAULT_SAMPLE_JOBS[0]);
  const [coverLetterEntryMode, setCoverLetterEntryMode] = useState<'pitch' | 'letter' | 'followup'>('pitch');
  const [coachThreads, setCoachThreads] = useState<Record<string, AiChatMessage[]>>({});
  const [selectedCvByJob, setSelectedCvByJob] = useState<Record<number, string>>({});
  const [coverLetters, setCoverLetters] = useState<CoverLetterItem[]>(() => [
    {
      doc_id: 'cl_101',
      job_id: 101,
      subject_line: 'Application: Lead Data Scientist — Ahmed El-Sayed',
      body_markdown:
        'Dear Swvl Talent Acquisition Team,\n\nHaving architected real-time route optimization services for high-volume mobility fleets, I am writing to express my strong interest in the Lead Data Scientist position at Swvl.\n\nIn my recent production deployments, I engineered PyTorch and FastAPI dynamic pricing endpoints across 1,400 daily routes, reducing route calculation latency by 42% while containerizing inference workloads on PostgreSQL and Docker.\n\nI would welcome the opportunity to discuss how this verified delivery experience translates to Swvl’s roadmap. My tailored 1-page ATS resume is attached for review.\n\nSincerely,\nAhmed El-Sayed · +20 100 482 9102',
      company_name: 'Swvl',
      job_title: 'Lead Data Scientist',
      recipient_email: '',
      source_label: 'Job Radar',
      created_at: new Date().toISOString(),
    },
    {
      doc_id: 'cl_104',
      job_id: 104,
      subject_line: 'Application: Senior AI Systems Engineer — Ahmed El-Sayed',
      body_markdown:
        'Dear Sara & TechStart MENA Team,\n\nBuilding low-latency Python and FastAPI orchestration APIs maps directly to TechStart MENA’s Senior AI Systems Engineer charter.\n\nMost recently at Swvl, I delivered production LLM/NLP workflows and deterministic evaluation harnesses running on Docker & PostgreSQL.\n\nMy tailored 1-page CV is attached for review—I’d welcome the chance to connect.\n\nBest,\nAhmed El-Sayed · +20 100 482 9102',
      company_name: 'TechStart MENA',
      job_title: 'Senior AI Systems Engineer',
      recipient_email: 'sara.mansour@techstart-mena.io',
      source_label: 'Direct Recruiter Post',
      created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    },
  ]);

  // Pipeline
  const [pipelineItems, setPipelineItems] = useState<PipelineItem[]>(() => {
    const existing = PipelineStorage.getItems();
    if (existing.length > 0) return existing;
    const seed: PipelineItem[] = [
      {
        id: 'pipe_104',
        job: DEFAULT_SAMPLE_JOBS[3],
        status: 'in_process',
        saved_at: new Date(Date.now() - 86400000 * 2).toISOString(),
        recruiter_email: 'sara.mansour@techstart-mena.io',
        tailored_cv_doc_id: 'doc_104',
        cover_letter: {
          doc_id: 'cl_104',
          job_id: 104,
          subject_line: 'Application: Senior AI Systems Engineer — Mostafa Ibrahim',
          body_markdown: 'Dear Sara,\n\nSharing my tailored CV for the Senior AI Systems Engineer opening at TechStart MENA...',
          company_name: 'TechStart MENA',
          job_title: 'Senior AI Systems Engineer',
          created_at: new Date().toISOString(),
        },
        notes: 'Matched Python, FastAPI, Docker; emphasize LLM evaluation harness.',
      },
      {
        id: 'pipe_105',
        job: DEFAULT_SAMPLE_JOBS[4],
        status: 'applied',
        saved_at: new Date(Date.now() - 86400000 * 9).toISOString(),
        applied_at: new Date(Date.now() - 86400000 * 8).toISOString(),
        recruiter_email: 'careers@instabug-demo.io',
        tailored_cv_doc_id: 'doc_105',
        notes: 'Applied 8 days ago — 7-day polite follow-up due today.',
      },
    ];
    PipelineStorage.saveItems(seed);
    return seed;
  });

  const [pipelineExtras, setPipelineExtras] = useState<Record<string, PipelineExtras>>(() => ({
    pipe_104: {
      recruiterName: 'Sara Mansour',
      followUpDate: 'Nov 24, 2026',
      rounds: [],
    },
    pipe_105: {
      recruiterName: 'Instabug Talent Team',
      followUpDate: 'Today (Due)',
      frozenPdfName: 'Mostafa_Ibrahim_CV_Instabug_v1.pdf',
      frozenAt: new Date(Date.now() - 86400000 * 8).toLocaleDateString(),
      rounds: [
        {
          id: 'r1',
          round: 'Prep Note · Potential Gap Check',
          date: 'Nov 12',
          interviewer: 'Platform Engineering',
          notes: 'Prepare Kafka telemetry throughput metrics and PyTorch anomaly clustering walkthrough.',
        },
      ],
    },
  }));

  // Notifications
  const [notifications, setNotifications] = useState<NotificationItem[]>(DEFAULT_NOTIFICATIONS);

  // Ergonomics & Overlays
  const [dir, setDirState] = useState<'ltr' | 'rtl'>(() =>
    (localStorage.getItem('tailored_dir_v2') as 'ltr' | 'rtl') || 'ltr'
  );
  const [density, setDensity] = useState<'cozy' | 'compact'>('cozy');
  const [defaultHomeRoute, setDefaultHomeRoute] = useState<'/dashboard' | '/radar' | '/studio'>('/dashboard');
  const [defaultIntensity, setDefaultIntensity] = useState<'Surgical' | 'Metrics+' | 'Executive'>('Surgical');
  const [notifThreshold, setNotifThreshold] = useState<number>(85);
  const [notifCadence, setNotifCadence] = useState<'instant' | 'daily' | 'off'>('daily');

  const [isIdentityDrawerOpen, setIsIdentityDrawerOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isNotificationsDrawerOpen, setIsNotificationsDrawerOpen] = useState(false);
  const [quickPeekJob, setQuickPeekJob] = useState<JobItem | null>(null);
  const [outOfCreditsState, setOutOfCreditsState] = useState<OutOfCreditsState | null>(null);
  const [isShortcutsHelpOpen, setIsShortcutsHelpOpen] = useState(false);
  const [toasts, setToasts] = useState<ToastNotice[]>([]);
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);

  useEffect(() => {
    document.documentElement.dir = dir;
    document.documentElement.lang = dir === 'rtl' ? 'ar' : 'en';
    localStorage.setItem('tailored_dir_v2', dir);
  }, [dir]);

  useEffect(() => {
    localStorage.setItem('tailored_credits_v2', String(creditBalance));
  }, [creditBalance]);

  useEffect(() => {
    const onOnline = () => setIsOnline(true);
    const onOffline = () => setIsOnline(false);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const pushToast = useCallback(
    (
      message: string,
      opts?: { variant?: ToastNotice['variant']; undoLabel?: string; onUndo?: () => void }
    ) => {
      const id = `toast_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
      setToasts((prev) => [...prev.slice(-2), { id, message, ...opts }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4800);
    },
    []
  );

  const navigateTo = useCallback(
    (fullTarget: string) => {
      const [rawPath, rawQuery] = fullTarget.split('?');
      const normalizedPath = rawPath.length > 1 ? rawPath.replace(/\/+$/, '') : rawPath || '/';
      const nextSearch = rawQuery ? `?${rawQuery}` : '';
      const fullUrl = `${normalizedPath}${nextSearch}`;

      if (locationState.pathname !== '/studio' && locationState.pathname !== '/cover-letters') {
        setPrevPath(`${locationState.pathname}${locationState.search}`);
      }
      if (window.location.pathname + window.location.search !== fullUrl) {
        window.history.pushState({}, '', fullUrl);
      }
      setLocationState({ pathname: normalizedPath, search: nextSearch });
      window.scrollTo({ top: 0, behavior: 'auto' });
    },
    [locationState.pathname, locationState.search]
  );

  const goBack = useCallback(() => {
    if (prevPath && prevPath !== '/studio' && prevPath !== '/cover-letters') {
      navigateTo(prevPath);
    } else {
      navigateTo('/dashboard');
    }
  }, [prevPath, navigateTo]);

  useEffect(() => {
    const onPop = () => {
      setLocationState({
        pathname: window.location.pathname || '/',
        search: window.location.search || '',
      });
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  // Global Cmd/Ctrl+K & `?` Shortcut Listener
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((v) => !v);
        return;
      }
      const tag = (e.target as HTMLElement)?.tagName;
      const isEditing = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || (e.target as HTMLElement)?.isContentEditable;
      if (!isEditing && e.key === '?') {
        e.preventDefault();
        setIsShortcutsHelpOpen((v) => !v);
      }
      if (e.key === 'Escape') {
        setIsCommandPaletteOpen(false);
        setIsIdentityDrawerOpen(false);
        setIsNotificationsDrawerOpen(false);
        setQuickPeekJob(null);
        setIsShortcutsHelpOpen(false);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  // Initial Backend Hydration (Graceful Offline Resilience)
  useEffect(() => {
    async function hydrate() {
      try {
        let profileId = 1;
        const { profiles } = await ProfileAPI.listProfiles();
        if (profiles.length > 0) {
          const full = await ProfileAPI.getProfile(profiles[0].id);
          if (full) {
            setCurrentProfile(full);
            profileId = full.id;
            const primary =
              full.profile.career_personas.find((p) => p.is_primary) || full.profile.career_personas[0];
            if (primary) setActivePersonaId(primary.persona_id);
          }
        }
        const { jobs } = await JobsAPI.listJobs();
        if (jobs.length > 0) {
          setRadarJobs(jobs);
          setInterestList((prev) => (prev.length ? prev : jobs.slice(0, 4)));
          setActiveStudioJob(jobs[0]);
        }
        const { docs } = await CvFitAPI.listCvFits(profileId);
        if (docs.length > 0) {
          setTailoredDocs(docs);
          const keys = new Set<string>(['cv_101', 'cl_101']);
          docs.forEach((d) => {
            if (d.job_id) keys.add(`cv_${d.job_id}`);
          });
          setUnlockedJobKeys(keys);
          const first = await CvFitAPI.getCvFit(docs[0].doc_id);
          if (first) setActiveStudioDoc(first);
        }
        const { coverLetters: letters } = await CoverLetterAPI.listCoverLetters();
        if (letters.length > 0) {
          setCoverLetters((prev) => {
            const seen = new Set(letters.map((l) => l.doc_id));
            return [...letters, ...prev.filter((p) => !seen.has(p.doc_id))];
          });
        }
      } catch {
        // Offline resilience already seeded cleanly
      }
    }
    hydrate();
  }, []);

  // Auth helpers
  const signIn = (email: string) => {
    setUserEmail(email || 'mostafa.eng@tailored.atelier');
    setIsAuthenticated(true);
    setEmailVerified(true);
    localStorage.setItem('tailored_auth_v2', JSON.stringify({ isAuthenticated: true }));
    if (pendingIntent) {
      fulfillPendingIntent();
    } else {
      navigateTo(defaultHomeRoute);
    }
  };

  const registerAccount = (_fullName: string, email: string) => {
    setUserEmail(email || 'mostafa.eng@tailored.atelier');
    setIsAuthenticated(true);
    setEmailVerified(false);
    localStorage.setItem('tailored_auth_v2', JSON.stringify({ isAuthenticated: true }));
    navigateTo('/verify-email');
  };

  const signOut = () => {
    setIsAuthenticated(false);
    localStorage.setItem('tailored_auth_v2', JSON.stringify({ isAuthenticated: false }));
    setIsIdentityDrawerOpen(false);
    navigateTo('/login');
  };

  const verifyOtpCode = (code: string) => {
    if (code.trim().length === 6) {
      setEmailVerified(true);
      pushToast('Email verified.', { variant: 'success' });
      navigateTo('/onboarding');
      return true;
    }
    return false;
  };

  const updateAccountEmail = (email: string) => {
    setUserEmail(email);
    pushToast(`Verification code sent to ${email}.`);
  };

  const toggleTwoFactor = (enabled: boolean) => {
    setTwoFactorEnabled(enabled);
    pushToast(enabled ? 'Two-factor authentication enabled.' : 'Two-factor authentication disabled.');
  };

  const toggleSso = (provider: 'google' | 'linkedin') => {
    if (connectedSso[provider] && !hasPassword && !connectedSso[provider === 'google' ? 'linkedin' : 'google']) {
      pushToast('Set an account password first so you stay signed in.', { variant: 'warn' });
      return;
    }
    setConnectedSso((prev) => ({ ...prev, [provider]: !prev[provider] }));
    pushToast(`${provider === 'google' ? 'Google' : 'LinkedIn'} connection updated.`);
  };

  const revokeSession = (id: string) => {
    setSessions((prev) => prev.filter((s) => s.id !== id));
    pushToast('Session signed out.');
  };

  // Profile actions
  const saveProfile = async (payload: UserProfilePayload): Promise<FullProfileResponse> => {
    try {
      const res = currentProfile?.id
        ? await ProfileAPI.updateProfile(currentProfile.id, payload)
        : await ProfileAPI.createProfile(payload);
      setCurrentProfile(res.data);
      const primary =
        res.data.profile.career_personas.find((p) => p.is_primary) || res.data.profile.career_personas[0];
      if (primary) setActivePersonaId(primary.persona_id);
      pushToast('Master Profile saved.', { variant: 'success' });
      return res.data;
    } catch {
      const fallback: FullProfileResponse = { id: currentProfile?.id || 1, profile: payload };
      setCurrentProfile(fallback);
      pushToast('Master Profile saved locally.', { variant: 'success' });
      return fallback;
    }
  };

  const setPrimaryPersona = async (personaId: string) => {
    setActivePersonaId(personaId);
    if (currentProfile?.id) {
      const updated = await ProfileAPI.setPrimaryPersona(currentProfile.id, personaId);
      if (updated) setCurrentProfile(updated);
    }
    pushToast('Active career persona updated.');
  };

  // Credit Helpers
  const isJobUnlocked = useCallback(
    (jobId: number, kind: 'cv' | 'cl') => unlockedJobKeys.has(`${kind}_${jobId}`),
    [unlockedJobKeys]
  );

  const requestCreditAction: WorkspaceContextValue['requestCreditAction'] = useCallback(
    async ({ cost, unlockKey, actionLabel, jobTarget, onAuthorized }) => {
      if (cost <= 0 || (unlockKey && unlockedJobKeys.has(unlockKey))) {
        await onAuthorized();
        return;
      }
      if (creditBalance < cost) {
        setOutOfCreditsState({
          actionLabel,
          requiredCredits: cost,
          onResume: async () => {
            setOutOfCreditsState(null);
            await onAuthorized();
          },
        });
        return;
      }
      const nextBal = creditBalance - cost;
      setCreditBalance(nextBal);
      if (unlockKey) {
        setUnlockedJobKeys((prev) => new Set(prev).add(unlockKey));
      }
      setCreditLedger((prev) => [
        {
          id: `led_${Date.now()}`,
          date: 'Today',
          action: actionLabel,
          jobTarget,
          delta: -cost,
          balanceAfter: nextBal,
        },
        ...prev,
      ]);
      await onAuthorized();
    },
    [creditBalance, unlockedJobKeys]
  );

  const purchaseCreditPack = (packId: string) => {
    const pack = CREDIT_PACKS.find((p) => p.id === packId);
    if (!pack || pack.isFree) return;
    const nextBal = creditBalance + pack.credits;
    setCreditBalance(nextBal);
    setCreditLedger((prev) => [
      {
        id: `led_${Date.now()}`,
        date: 'Today',
        action: `${pack.name} Pack (${pack.prices[creditCurrency].label})`,
        jobTarget: `${pack.credits} non-expiring credits`,
        delta: pack.credits,
        balanceAfter: nextBal,
      },
      ...prev,
    ]);
    pushToast(`Added ${pack.credits} credits to your wallet.`, { variant: 'success' });
    if (outOfCreditsState && nextBal >= outOfCreditsState.requiredCredits) {
      const resumeFn = outOfCreditsState.onResume;
      setOutOfCreditsState(null);
      setTimeout(() => resumeFn(), 120);
    }
  };

  // Jobs & Interest
  const addToInterest = useCallback(
    (job: JobItem) => {
      setInterestList((prev) => (prev.some((j) => j.id === job.id) ? prev : [job, ...prev]));
    },
    []
  );

  const removeFromInterest = useCallback(
    (jobId: number) => {
      const target = interestList.find((j) => j.id === jobId);
      setInterestList((prev) => prev.filter((j) => j.id !== jobId));
      if (target) {
        pushToast(`Removed ${cleanCompanyName(target.company_name)} from Interest List.`, {
          undoLabel: 'Undo',
          onUndo: () => setInterestList((prev) => [target, ...prev]),
        });
      }
    },
    [interestList, pushToast]
  );

  const hideJob = useCallback(
    (jobId: number) => {
      setHiddenJobIds((prev) => new Set(prev).add(jobId));
      pushToast('Job hidden from feed.', {
        undoLabel: 'Undo',
        onUndo: () =>
          setHiddenJobIds((prev) => {
            const next = new Set(prev);
            next.delete(jobId);
            return next;
          }),
      });
    },
    [pushToast]
  );

  const unhideJob = useCallback((jobId: number) => {
    setHiddenJobIds((prev) => {
      const next = new Set(prev);
      next.delete(jobId);
      return next;
    });
  }, []);

  const openJobInStudio = useCallback(
    async (job: JobItem, opts?: { skipCreditCheck?: boolean }) => {
      const execute = async () => {
        addToInterest(job);
        setActiveStudioJob(job);
        navigateTo(`/studio?job_id=${job.id}`);
        const existingSummary = tailoredDocs.find((d) => d.job_id === job.id);
        if (existingSummary) {
          const detail = await CvFitAPI.getCvFit(existingSummary.doc_id);
          if (detail) {
            setActiveStudioDoc(detail);
            return;
          }
        }
        try {
          const res = await CvFitAPI.tailorCv(
            {
              profile_id: currentProfile?.id || 1,
              persona_id: activePersonaId,
              job_id: job.id,
              job_title: cleanTargetJobTitle(job.title),
              company_name: cleanCompanyName(job.company_name),
              location: job.location,
              location_type: job.location_type,
              fit_score: job.fit_score,
              parsed_skills: job.parsed_skills || [],
              job_description_text: job.raw_description,
            },
            currentProfile?.profile || SAMPLE_PROFILE
          );
          setActiveStudioDoc(res.data);
          setTailoredDocs((prev) => [
            {
              doc_id: res.data.doc_id,
              profile_id: res.data.profile_id,
              persona_id: res.data.persona_id,
              job_id: res.data.job_id,
              status: res.data.status || 'tailored',
              tailoring_applied: true,
              job_title: res.data.job_title,
              company_name: res.data.company_name,
              location: res.data.location,
              fit_score: res.data.fit_score,
              parsed_skills: res.data.parsed_skills || [],
              compile_status: res.data.compile_status || 'ok',
              notes_count: res.data.notes?.length || 0,
              bullet_diffs_count: res.data.bullet_diffs?.length || 0,
              files: res.data.files || [],
              created_at: res.data.created_at,
              updated_at: res.data.updated_at,
            },
            ...prev.filter((d) => d.doc_id !== res.data.doc_id),
          ]);
        } catch {
          pushToast('Studio loaded using offline CV synthesizer.', { variant: 'warn' });
        }
      };

      if (opts?.skipCreditCheck) {
        await execute();
        return;
      }
      await requestCreditAction({
        cost: 1,
        unlockKey: `cv_${job.id}`,
        actionLabel: 'Tailor CV',
        jobTarget: `${cleanCompanyName(job.company_name)} — ${cleanTargetJobTitle(job.title)}`,
        onAuthorized: execute,
      });
    },
    [addToInterest, navigateTo, tailoredDocs, currentProfile, activePersonaId, requestCreditAction, pushToast]
  );

  const ingestJobUrlOrText = useCallback(
    async (raw: string, opts?: { openInStudio?: boolean; onlySaveInterest?: boolean }): Promise<JobItem | null> => {
      const trimmed = raw.trim();
      if (!trimmed) return null;
      const isUrl = /^https?:\/\//i.test(trimmed);
      const { job } = isUrl
        ? await JobsAPI.ingestJobFromUrl({ url: trimmed, profile_id: currentProfile?.id, persona_id: activePersonaId })
        : await JobsAPI.extractJobFromDescription({ description: trimmed, profile_id: currentProfile?.id, persona_id: activePersonaId });

      setRadarJobs((prev) => (prev.some((j) => j.id === job.id) ? prev : [job, ...prev]));
      addToInterest(job);
      pushToast(`Saved ${cleanCompanyName(job.company_name)} to Saved Shortlist.`, { variant: 'success' });
      if (opts?.openInStudio && !opts?.onlySaveInterest) {
        await openJobInStudio(job);
      }
      return job;
    },
    [currentProfile?.id, activePersonaId, addToInterest, pushToast, openJobInStudio]
  );

  const runLiveSweep = useCallback(
    async (query?: string) => {
      const { jobs } = await JobsAPI.triggerAutoSearch({
        profile_id: currentProfile?.id || 1,
        persona_id: activePersonaId,
        query: query || undefined,
      });
      if (jobs.length > 0) {
        setRadarJobs(jobs);
        pushToast(`Radar sweep finished — ${jobs.length} ranked opportunities.`, { variant: 'success' });
      }
      return jobs;
    },
    [currentProfile?.id, activePersonaId, pushToast]
  );

  const openDocInStudio = useCallback(
    async (docId: string) => {
      const detail = await CvFitAPI.getCvFit(docId);
      if (detail) {
        setActiveStudioDoc(detail);
        const matchedJob =
          radarJobs.find((j) => j.id === detail.job_id) ||
          interestList.find((j) => j.id === detail.job_id);
        if (matchedJob) {
          setActiveStudioJob(matchedJob);
        } else {
          setActiveStudioJob({
            id: detail.job_id || -Math.max(1, detail.doc_id.length),
            source_id: detail.doc_id,
            title: cleanTargetJobTitle(detail.job_title || 'Tailored Resume'),
            company_name: cleanCompanyName(detail.company_name || 'Saved CV'),
            location: detail.location || 'Cairo, Egypt',
            url: detail.company_website_url || '',
            raw_description: detail.job_description_text || `${detail.job_title || 'Resume'} for ${detail.company_name || 'Saved CV'}.`,
            fit_score: detail.fit_score ?? 90,
            is_high_match: (detail.fit_score ?? 90) >= 85,
            source_type: detail.generation_mode || 'saved_cv',
            parsed_skills: detail.parsed_skills || ['Python', 'FastAPI', 'Docker'],
            responsibilities: [],
            location_type: detail.location_type || 'Hybrid',
            created_at: detail.created_at,
          });
        }
      }
      navigateTo(`/studio?doc_id=${docId}`);
    },
    [radarJobs, interestList, navigateTo]
  );

  const registerStudioDoc = useCallback((detail: CvFitDetail) => {
    CvFitAPI.saveLocalDoc(detail);
    setActiveStudioDoc(detail);
    const summary = cvDetailToSummary(detail);
    setTailoredDocs((prev) => [summary, ...prev.filter((d) => d.doc_id !== detail.doc_id)]);
  }, []);

  const deleteStudioDoc = useCallback(
    (docId: string) => {
      const target = tailoredDocs.find((d) => d.doc_id === docId);
      CvFitAPI.removeLocalDoc(docId);
      setTailoredDocs((prev) => prev.filter((d) => d.doc_id !== docId));
      if (target) {
        pushToast(`Removed ${cleanCompanyName(target.company_name || 'CV')} from Saved CVs.`, {
          undoLabel: 'Undo',
          onUndo: () => setTailoredDocs((prev) => [target, ...prev.filter((d) => d.doc_id !== target.doc_id)]),
        });
      }
    },
    [tailoredDocs, pushToast]
  );

  const saveStudioDocUpdate = useCallback((detail: CvFitDetail) => {
    CvFitAPI.saveLocalDoc(detail);
    setActiveStudioDoc(detail);
    setTailoredDocs((prev) =>
      prev.map((d) =>
        d.doc_id === detail.doc_id
          ? {
              ...d,
              updated_at: new Date().toISOString(),
              bullet_diffs_count: detail.bullet_diffs.length,
              fit_score: detail.fit_score ?? d.fit_score,
            }
          : d
      )
    );
  }, []);

  const forkSavedDoc = useCallback(
    async (docId: string) => {
      const detail = await CvFitAPI.getCvFit(docId);
      if (!detail) return;
      const forked: CvFitDetail = {
        ...detail,
        doc_id: `${detail.doc_id}_fork_${Date.now()}`,
        status: 'draft',
        job_title: `${detail.job_title || 'Tailored CV'} (Fork)`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      CvFitAPI.saveLocalDoc(forked);
      setActiveStudioDoc(forked);
      setTailoredDocs((prev) => [cvDetailToSummary(forked), ...prev]);
      pushToast('Forked editable CV draft.', { variant: 'success' });
      navigateTo(`/studio?doc_id=${forked.doc_id}`);
    },
    [navigateTo, pushToast]
  );

  const openJobInCoverLetters = useCallback(
    (job: JobItem, opts?: { mode?: 'pitch' | 'letter' | 'followup' }) => {
      setActiveStudioJob(job);
      setCoverLetterEntryMode(opts?.mode || 'pitch');
      navigateTo(`/cover-letters?job_id=${job.id}`);
    },
    [navigateTo]
  );

  const updateCoachThread = useCallback(
    (
      key: string,
      fallback: AiChatMessage[],
      updater: (curr: AiChatMessage[]) => AiChatMessage[]
    ) => {
      setCoachThreads((prev) => ({
        ...prev,
        [key]: updater(prev[key] ?? fallback),
      }));
    },
    []
  );

  const resetCoachThread = useCallback((key: string, seed: AiChatMessage[]) => {
    setCoachThreads((prev) => ({ ...prev, [key]: seed }));
  }, []);

  const setSelectedCvForJob = useCallback((jobId: number, cvId: string) => {
    setSelectedCvByJob((prev) => ({ ...prev, [jobId]: cvId }));
  }, []);

  const saveCoverLetter = useCallback((item: CoverLetterItem) => {
    setCoverLetters((prev) =>
      prev.some((c) => c.doc_id === item.doc_id)
        ? prev.map((c) => (c.doc_id === item.doc_id ? item : c))
        : [item, ...prev]
    );
  }, []);

  const deleteCoverLetter = useCallback(
    (docId: string) => {
      const target = coverLetters.find((c) => c.doc_id === docId);
      setCoverLetters((prev) => prev.filter((c) => c.doc_id !== docId));
      if (target) {
        pushToast(`Removed ${cleanCompanyName(target.company_name || 'letter')} from Cover Letters history.`, {
          undoLabel: 'Undo',
          onUndo: () =>
            setCoverLetters((prev) => [target, ...prev.filter((c) => c.doc_id !== target.doc_id)]),
        });
      }
    },
    [coverLetters, pushToast]
  );

  // Pipeline CRUD (Unified across Direct Email & External Portal channels)
  const addToPipeline = useCallback(
    (
      job: JobItem,
      status: PipelineStatus = 'saved',
      overrideEmail?: string | null,
      opts?: { tailoredCvDocId?: string | null; coverLetter?: CoverLetterItem | null; silent?: boolean }
    ): PipelineItem | null => {
      const email = overrideEmail ?? job.recruiter_email ?? extractEmail(job.raw_description || '');
      const item = PipelineStorage.addOrUpdateJob(job, status, email, currentProfile?.id, {
        tailoredCvDocId: opts?.tailoredCvDocId,
        coverLetter: opts?.coverLetter,
      });
      setPipelineItems(PipelineStorage.getItems());
      if (status === 'applied' && item) {
        setPipelineExtras((prev) => ({
          ...prev,
          [item.id]: {
            ...(prev[item.id] || { rounds: [] }),
            frozenAt: new Date().toLocaleDateString(),
            frozenPdfName: `${(currentProfile?.profile.personal_info.full_name || 'Candidate').replace(/\s+/g, '_')}_CV.pdf`,
          },
        }));
      }
      if (!opts?.silent) {
        pushToast(`Added ${cleanCompanyName(job.company_name)} to Pipeline.`, { variant: 'success' });
      }
      return item;
    },
    [currentProfile, pushToast]
  );

  const updatePipelineStage = useCallback(
    (id: string, status: PipelineStatus) => {
      const prevItem = pipelineItems.find((i) => i.id === id);
      const prevStatus = prevItem?.status;
      PipelineStorage.updateStatus(id, status);
      setPipelineItems(PipelineStorage.getItems());
      if (status === 'applied') {
        setPipelineExtras((prev) => ({
          ...prev,
          [id]: {
            ...(prev[id] || { rounds: [] }),
            frozenAt: new Date().toLocaleDateString(),
            frozenPdfName: `${(currentProfile?.profile.personal_info.full_name || 'Candidate').replace(/\s+/g, '_')}_CV.pdf`,
          },
        }));
      }
      pushToast(`Stage updated to "${status.replace('_', ' ')}".`, {
        undoLabel: prevStatus ? 'Undo' : undefined,
        onUndo: prevStatus
          ? () => {
              PipelineStorage.updateStatus(id, prevStatus);
              setPipelineItems(PipelineStorage.getItems());
            }
          : undefined,
      });
    },
    [pipelineItems, currentProfile, pushToast]
  );

  const updatePipelineEmail = useCallback(
    (id: string, email: string) => {
      PipelineStorage.updateRecruiterEmail(id, email);
      setPipelineItems(PipelineStorage.getItems());
      pushToast('Recruiter email saved.');
    },
    [pushToast]
  );

  const updatePipelineExtras = useCallback((id: string, patch: Partial<PipelineExtras>) => {
    setPipelineExtras((prev) => ({
      ...prev,
      [id]: { ...(prev[id] || { rounds: [] }), ...patch },
    }));
  }, []);

  const removeFromPipeline = useCallback(
    (id: string) => {
      PipelineStorage.removeItem(id);
      setPipelineItems(PipelineStorage.getItems());
      pushToast('Removed from Pipeline.');
    },
    [pushToast]
  );

  // Notifications
  const markNotificationRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const markAllNotificationsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    pushToast('All notifications marked read.');
  };

  const snoozeNotification = (id: string, label: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true, snoozedUntil: label } : n))
    );
    pushToast(`Snoozed until ${label}.`);
  };

  const fulfillPendingIntent = useCallback(() => {
    const intent = pendingIntent;
    setPendingIntent(null);
    if (!intent) {
      navigateTo(defaultHomeRoute);
      return;
    }
    if (intent.type === 'tailor_job' && intent.jobId) {
      const target = radarJobs.find((j) => j.id === intent.jobId) || radarJobs[0];
      if (target) {
        openJobInStudio(target);
        return;
      }
    }
    if (intent.type === 'inspect_fit' && intent.jobId) {
      navigateTo(`/jobs/${intent.jobId}`);
      return;
    }
    if (intent.type === 'ingest_url' || intent.type === 'ingest_jd') {
      navigateTo('/radar?tab=saved');
      return;
    }
    if (intent.type === 'search') {
      navigateTo(`/radar${intent.query ? `?q=${encodeURIComponent(intent.query)}` : ''}`);
      return;
    }
    navigateTo(defaultHomeRoute);
  }, [pendingIntent, navigateTo, defaultHomeRoute, radarJobs, openJobInStudio]);

  const resetAllPaneWidths = () => {
    Object.keys(localStorage)
      .filter((k) => k.startsWith('tailored_split_'))
      .forEach((k) => localStorage.removeItem(k));
    pushToast('Reset all pane widths to ergonomic defaults.', { variant: 'success' });
  };

  return (
    <WorkspaceContext.Provider
      value={{
        currentPath: locationState.pathname,
        currentSearch: locationState.search,
        navigateTo,
        goBack,
        isAuthenticated,
        userEmail,
        emailVerified,
        hasPassword,
        twoFactorEnabled,
        connectedSso,
        sessions,
        signIn,
        registerAccount,
        signOut,
        verifyOtpCode,
        updateAccountEmail,
        toggleTwoFactor,
        toggleSso,
        revokeSession,
        pendingIntent,
        setPendingIntent,
        fulfillPendingIntent,
        currentProfile,
        activePersonaId,
        setActivePersonaId,
        activeRegionalPhone,
        setActiveRegionalPhone,
        saveProfile,
        setPrimaryPersona,
        creditBalance,
        creditCurrency,
        setCreditCurrency,
        lowBalanceThreshold,
        setLowBalanceThreshold,
        creditLedger,
        unlockedJobKeys,
        isJobUnlocked,
        requestCreditAction,
        purchaseCreditPack,
        radarJobs,
        setRadarJobs,
        hiddenJobIds,
        hideJob,
        unhideJob,
        interestList,
        addToInterest,
        removeFromInterest,
        ingestJobUrlOrText,
        runLiveSweep,
        tailoredDocs,
        activeStudioDoc,
        activeStudioJob,
        setActiveStudioJob,
        openJobInStudio,
        openJobInCoverLetters,
        openDocInStudio,
        registerStudioDoc,
        deleteStudioDoc,
        saveStudioDocUpdate,
        forkSavedDoc,
        coverLetters,
        saveCoverLetter,
        deleteCoverLetter,
        coverLetterEntryMode,
        setCoverLetterEntryMode,
        coachThreads,
        updateCoachThread,
        resetCoachThread,
        selectedCvByJob,
        setSelectedCvForJob,
        pipelineItems,
        pipelineExtras,
        addToPipeline,
        updatePipelineStage,
        updatePipelineEmail,
        updatePipelineExtras,
        removeFromPipeline,
        notifications,
        markNotificationRead,
        markAllNotificationsRead,
        snoozeNotification,
        dir,
        setDir: setDirState,
        density,
        setDensity,
        defaultHomeRoute,
        setDefaultHomeRoute,
        defaultIntensity,
        setDefaultIntensity,
        notifThreshold,
        setNotifThreshold,
        notifCadence,
        setNotifCadence,
        resetAllPaneWidths,
        isIdentityDrawerOpen,
        setIsIdentityDrawerOpen,
        isCommandPaletteOpen,
        setIsCommandPaletteOpen,
        isNotificationsDrawerOpen,
        setIsNotificationsDrawerOpen,
        quickPeekJob,
        setQuickPeekJob,
        outOfCreditsState,
        closeOutOfCredits: () => setOutOfCreditsState(null),
        isShortcutsHelpOpen,
        setIsShortcutsHelpOpen,
        toasts,
        pushToast,
        dismissToast,
        isOnline,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

export function useWorkspace(): WorkspaceContextValue {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error('useWorkspace must be used inside WorkspaceProvider');
  return ctx;
}
