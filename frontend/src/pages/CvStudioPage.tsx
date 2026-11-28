import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { ResizableSplitPane } from '../components/common/ResizableSplitPane';
import { SavedRoleDropdown } from '../components/common/SavedRoleDropdown';
import {
  TypewriterDropPlaceholder,
  type TypewriterPromptItem,
} from '../components/common/TypewriterDropPlaceholder';
import { TailoredIcon } from '../brand/TailoredIcons';
import { AtelierFrenchCurveBackdrop } from '../brand/BrandElements';
import {
  AtelierPreviewDrawer,
  type AtelierPreviewData,
} from '../components/studio/AtelierPreviewDrawer';
import { buildParsedCvSnapshot } from '../utils/cvSnapshotBuilder';
import {
  CalmAiCoachSidecar,
  type AiChatMessage,
  type AiResourceItem,
  type AiAuditItem,
} from '../components/common/CalmAiCoachSidecar';
import { SAMPLE_PROFILE, type CareerPersona, type UserProfilePayload } from '../services/profileApi';
import { evaluateAllPersonas } from '../utils/fitEngine';
import { buildWorkspaceCoachReply } from '../utils/workspaceCoachEngine';
import { parseCoverLetterDropInput } from '../utils/coverLetterTargetParser';
import { parseLatexCvClient } from '../utils/latexCvParser';
import {
  buildCanonicalCvLatex,
  computeLatexLineDiff,
  parseLatexToCv,
  type ParsedLatexCv,
} from '../utils/latexLiveSync';
import {
  CvFitAPI,
  cleanCompanyName,
  cleanTargetJobTitle,
  stripLeadingRoleFromBioClient,
  type CvFitDetail,
} from '../services/cvFitApi';
import type { JobItem } from '../services/jobsApi';
import { resolveServerJobId } from '../services/jobsApi';
import { AgentAPI } from '../services/agentApi';
import { getAccessToken } from '../services/apiClient';
import { TelemetrySDK } from '../services/telemetrySdk';

interface VersionSnapshot {
  version: number;
  label: string;
  summary: string;
  bullets: string[];
  latex?: string;
}

interface AttachedCvDropFile {
  kind: 'tex' | 'pdf' | 'image';
  name: string;
  previewUrl: string;
  rawText: string;
}

const CV_DROP_PROMPTS: TypewriterPromptItem[] = [
  { icon: 'upload', text: 'Drop a PDF or .tex resume to import...' },
  { icon: 'link', text: 'Paste a job link to tailor a fresh CV...' },
  { icon: 'cv', text: 'Paste a full job description...' },
  { icon: 'image', text: 'Drop or Ctrl+V a job post screenshot...' },
];

function formatShortCvDate(iso?: string): string {
  if (!iso) return 'Draft';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return 'Draft';
  const diffDays = Math.floor((Date.now() - d.getTime()) / 86400000);
  if (diffDays <= 0) return 'Today';
  if (diffDays === 1) return '1d ago';
  if (diffDays < 14) return `${diffDays}d ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function extractPdfPlainTextBestEffort(buffer: ArrayBuffer): string {
  try {
    const bytes = new Uint8Array(buffer.slice(0, 260000));
    const decoder = new TextDecoder('latin1');
    const raw = decoder.decode(bytes);
    const parenMatches = raw.match(/\(([^()\\]{3,140})\)/g) || [];
    const candidateChunks = parenMatches
      .map((m) => m.slice(1, -1))
      .filter((s) => /[a-zA-Z]{2,}/.test(s) && !/^(Type|Font|Filter|FlateDecode|Obj|Endobj|XRef|MediaBox|Resources|PDF-)/i.test(s));
    if (candidateChunks.length >= 4) {
      return candidateChunks.join(' ').replace(/\s+/g, ' ').trim().slice(0, 2400);
    }
    const readableRuns = raw.match(/[A-Za-z][A-Za-z0-9.,;:!?@+\-/()% ]{8,140}/g) || [];
    const filtered = readableRuns.filter(
      (s) => !/(endobj|stream|endstream|flatedecode|fontdescriptor|catalog|pages|mediabox|procset|helvetica)/i.test(s)
    );
    return filtered.slice(0, 28).join('\n').trim();
  } catch {
    return '';
  }
}

function cleanFileBaseTitle(fileName: string, fallback: string): string {
  const base = fileName
    .replace(/\.(tex|pdf|txt|md)$/i, '')
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return base || fallback;
}

function buildImportedTexCvDetail(params: {
  fileName: string;
  texContent: string;
  profile: UserProfilePayload;
  personaId?: string;
}): CvFitDetail {
  const now = new Date().toISOString();
  const stamp = Date.now();
  const parsedClient = parseLatexCvClient(params.texContent);
  const titleLabel = cleanFileBaseTitle(params.fileName, 'Imported LaTeX CV');
  const firstPersona = parsedClient.profile.career_personas?.[0];
  const skills =
    firstPersona?.skills_and_tools?.core_skills?.slice(0, 6) || ['LaTeX', 'Python', 'FastAPI', 'SQL'];
  return {
    doc_id: `local-tex-${stamp}`,
    profile_id: 1,
    persona_id: params.personaId || firstPersona?.persona_id || 'data_scientist_track',
    status: 'draft',
    generation_mode: 'imported_tex',
    tailoring_applied: true,
    job_title: titleLabel,
    company_name: 'Imported .tex',
    location: 'Editable Source',
    location_type: 'Local',
    fit_score: 90,
    parsed_skills: skills,
    compile_status: 'ok',
    base_cv_tex_sha256: `tex-${stamp}`,
    base_latex_content: params.texContent,
    tailored_latex_content: params.texContent,
    bullet_diffs: [],
    notes: [`Imported ${params.fileName} directly into live LaTeX split editor (0 cr).`],
    errors: [],
    files: [
      { kind: 'tex', filename: params.fileName, download_path: `/api/v1/cv-fit/local-tex-${stamp}/download/tex` },
      { kind: 'pdf', filename: `${titleLabel.replace(/\s+/g, '_')}.pdf`, download_path: `/api/v1/cv-fit/local-tex-${stamp}/download/pdf` },
    ],
    created_at: now,
    updated_at: now,
  };
}

function buildImportedPdfCvDetail(params: {
  fileName: string;
  extractedText: string;
  profile: UserProfilePayload;
  activePersona?: CareerPersona;
  phoneDisplay: string;
  locationLabel: string;
}): CvFitDetail {
  const now = new Date().toISOString();
  const stamp = Date.now();
  const titleLabel = cleanFileBaseTitle(params.fileName, 'Imported PDF Resume');
  const persona = params.activePersona || params.profile.career_personas[0];
  const baseSummary = stripLeadingRoleFromBioClient(persona?.summary_bio || '') ||
    'Senior Data Scientist & AI Systems Engineer delivering production modeling and scalable API systems.';
  const extractedSnippet = params.extractedText
    .split(/[\n.]/)
    .map((s) => s.trim())
    .filter((s) => s.length >= 28 && s.length <= 180)
    .slice(0, 2);
  const bullets =
    extractedSnippet.length > 0
      ? extractedSnippet
      : persona?.experience_highlights.map((e) => e.achievements[0]).filter(Boolean) || [
        'Architected end-to-end automated customer scoring and demand forecasting pipelines in Python & FastAPI.',
      ];
  const latex = buildCanonicalCvLatex({
    profile: params.profile,
    activePersona: persona,
    phoneDisplay: params.phoneDisplay,
    locationLabel: params.locationLabel,
    summaryText: baseSummary,
    bullets,
  });
  return {
    doc_id: `local-pdf-${stamp}`,
    profile_id: 1,
    persona_id: persona?.persona_id || 'data_scientist_track',
    status: 'draft',
    generation_mode: 'imported_pdf',
    tailoring_applied: true,
    job_title: titleLabel,
    company_name: 'Imported PDF',
    location: params.locationLabel,
    location_type: 'Local',
    fit_score: 88,
    parsed_skills: persona?.skills_and_tools.core_skills.slice(0, 6) || ['Python', 'FastAPI', 'SQL', 'Docker'],
    compile_status: 'ok',
    base_cv_tex_sha256: `pdf-${stamp}`,
    base_latex_content: latex,
    tailored_latex_content: latex,
    bullet_diffs: bullets.map((b, i) => ({
      section: 'experience',
      original_bullet: persona?.experience_highlights[i]?.achievements[0] || b,
      tailored_bullet: b,
      rationale: `Imported from ${params.fileName} into editable ATS LaTeX.`,
    })),
    notes: [`Converted ${params.fileName} into editable LaTeX & Paper view (0 cr).`],
    errors: [],
    files: [
      { kind: 'tex', filename: 'imported_cv.tex', download_path: `/api/v1/cv-fit/local-pdf-${stamp}/download/tex` },
      { kind: 'pdf', filename: params.fileName, download_path: `/api/v1/cv-fit/local-pdf-${stamp}/download/pdf` },
    ],
    created_at: now,
    updated_at: now,
  };
}

function buildBlankLatexCvDetail(params: {
  profile: UserProfilePayload;
  activePersona?: CareerPersona;
  phoneDisplay: string;
  locationLabel: string;
}): CvFitDetail {
  const now = new Date().toISOString();
  const stamp = Date.now();
  const persona = params.activePersona || params.profile.career_personas[0];
  const baseSummary = stripLeadingRoleFromBioClient(persona?.summary_bio || '') ||
    'Senior Data Scientist & AI Systems Engineer delivering production regression engines and API workflows.';
  const bullets =
    persona?.experience_highlights.map((e) => e.achievements[0]).filter(Boolean) || [
      'Architected end-to-end automated customer scoring and demand forecasting pipelines in Python & FastAPI.',
    ];
  const latex = buildCanonicalCvLatex({
    profile: params.profile,
    activePersona: persona,
    phoneDisplay: params.phoneDisplay,
    locationLabel: params.locationLabel,
    summaryText: baseSummary,
    bullets,
  });
  return {
    doc_id: `local-blank-${stamp}`,
    profile_id: 1,
    persona_id: persona?.persona_id || 'data_scientist_track',
    status: 'draft',
    generation_mode: 'blank_latex',
    tailoring_applied: true,
    job_title: persona?.target_title || 'Blank LaTeX Resume',
    company_name: 'Custom Draft',
    location: params.locationLabel,
    location_type: 'Local',
    fit_score: 86,
    parsed_skills: persona?.skills_and_tools.core_skills.slice(0, 6) || ['Python', 'FastAPI', 'SQL'],
    compile_status: 'ok',
    base_cv_tex_sha256: `blank-${stamp}`,
    base_latex_content: latex,
    tailored_latex_content: latex,
    bullet_diffs: bullets.map((b) => ({
      section: 'experience',
      original_bullet: b,
      tailored_bullet: b,
      rationale: 'Clean customizable LaTeX baseline.',
    })),
    notes: ['Clean editable LaTeX resume draft (0 cr).'],
    errors: [],
    files: [
      { kind: 'tex', filename: 'custom_cv.tex', download_path: `/api/v1/cv-fit/local-blank-${stamp}/download/tex` },
      { kind: 'pdf', filename: 'custom_cv.pdf', download_path: `/api/v1/cv-fit/local-blank-${stamp}/download/pdf` },
    ],
    created_at: now,
    updated_at: now,
  };
}

function buildSyntheticJobFromDoc(detail: CvFitDetail): JobItem {
  return {
    id: detail.job_id || -Math.max(1, detail.doc_id.length),
    source_id: detail.doc_id,
    title: cleanTargetJobTitle(detail.job_title || 'Tailored Resume'),
    company_name: cleanCompanyName(detail.company_name || 'Custom Draft'),
    location: detail.location || 'Cairo, Egypt',
    url: detail.company_website_url || '',
    raw_description:
      detail.job_description_text ||
      `${detail.job_title || 'Resume'} (${detail.company_name || 'Custom Draft'}).`,
    fit_score: detail.fit_score ?? 88,
    is_high_match: (detail.fit_score ?? 88) >= 85,
    source_type: detail.generation_mode || 'saved_cv',
    parsed_skills: detail.parsed_skills || ['Python', 'FastAPI', 'Docker'],
    responsibilities: [],
    location_type: detail.location_type || 'Hybrid',
    created_at: detail.created_at,
  };
}

function buildDroppedTargetJobRecord(params: {
  company: string;
  role: string;
  location: string;
  url: string;
  skills: string[];
  summaryDescription: string;
  recipientEmail: string;
  sourceKind: string;
}): JobItem {
  const stamp = Date.now();
  return {
    id: stamp,
    source_id: `cv_drop_${stamp}`,
    title: params.role,
    company_name: params.company,
    location: params.location,
    url: params.url,
    raw_description: params.summaryDescription,
    fit_score: 91,
    is_high_match: true,
    source_type: `custom_${params.sourceKind}`,
    parsed_skills: params.skills,
    responsibilities: [],
    location_type: /remote/i.test(params.location) ? 'Remote' : 'Hybrid',
    created_at: new Date().toISOString(),
    recruiter_email: params.recipientEmail || null,
  };
}

function buildCleanLeadRewrite(original: string): string {
  const clean = original.trim();
  if (!clean) return '';
  if (/^Developed and deployed\b/i.test(clean)) {
    return clean.replace(/^Developed and deployed\b/i, 'Engineered and shipped');
  }
  if (/^Developed a\b/i.test(clean)) {
    return clean.replace(/^Developed a\b/i, 'Architected a production');
  }
  if (/^Developed\b/i.test(clean)) {
    return clean.replace(/^Developed\b/i, 'Engineered');
  }
  if (/^Built\b/i.test(clean)) {
    return clean.replace(/^Built\b/i, 'Architected');
  }
  if (/^Worked on\b/i.test(clean)) {
    return clean.replace(/^Worked on\b/i, 'Delivered');
  }
  if (/^Created\b/i.test(clean)) {
    return clean.replace(/^Created\b/i, 'Designed');
  }
  return clean.replace(/\s+using\s+/i, ' powered by ');
}

export const CvStudioPage: React.FC = () => {
  const {
    goBack,
    currentProfile,
    activePersonaId,
    setActivePersonaId,
    activeRegionalPhone,
    setActiveRegionalPhone,
    activeStudioJob,
    setActiveStudioJob,
    activeStudioDoc,
    saveStudioDocUpdate,
    tailoredDocs,
    coverLetters,
    radarJobs,
    setRadarJobs,
    interestList,
    pipelineItems,
    ingestJobUrlOrText,
    openDocInStudio,
    registerStudioDoc,
    deleteStudioDoc,
    forkSavedDoc,
    openJobInStudio,
    openJobInCoverLetters,
    addToPipeline,
    coachThreads,
    updateCoachThread,
    resetCoachThread,
    setSelectedCvForJob,
    isJobUnlocked,
    pushToast,
  } = useWorkspace();

  const profile = currentProfile?.profile || SAMPLE_PROFILE;
  const activePersona =
    profile.career_personas.find((p) => p.persona_id === activePersonaId) ||
    profile.career_personas[0];

  const docKey = activeStudioDoc?.doc_id || `job_${activeStudioJob.id}`;

  const [cvLibraryOpen, setCvLibraryOpen] = useState(true);
  const [isBlankCvMode, setIsBlankCvMode] = useState(false);
  const [cvDropInput, setCvDropInput] = useState('');
  const [cvDraggingOver, setCvDraggingOver] = useState(false);
  const [cvAttachedFile, setCvAttachedFile] = useState<AttachedCvDropFile | null>(null);
  const [isCreatingCv, setIsCreatingCv] = useState(false);
  const [blankPersonaMenuOpen, setBlankPersonaMenuOpen] = useState(false);

  const [viewMode, setViewMode] = useState<'paper' | 'diff' | 'tex'>('paper');
  const [swapSides, setSwapSides] = useState(false);
  const [coachCollapsed, setCoachCollapsed] = useState(false);

  const [identityMenuOpen, setIdentityMenuOpen] = useState(false);
  const [jobMenuOpen, setJobMenuOpen] = useState(false);
  const [customizeOpen, setCustomizeOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [quickJdPaste, setQuickJdPaste] = useState('');

  const [zoomPct, setZoomPct] = useState<number>(100);
  const [paperDensity, setPaperDensity] = useState<'cozy' | 'compact'>('cozy');
  const [tailorIntensity, setTailorIntensity] = useState<'Surgical' | 'Metrics+' | 'Executive'>('Surgical');

  const phoneDisplay =
    activeRegionalPhone === '+20'
      ? '+20 100 482 9102'
      : activeRegionalPhone === '+966'
        ? '+966 54 391 8820'
        : '+971 50 987 6543';

  const locationLabel =
    activeRegionalPhone === '+966'
      ? 'Riyadh, KSA'
      : activeRegionalPhone === '+971'
        ? 'Dubai, UAE'
        : 'Cairo, Egypt';

  const baseInitialBullets = useMemo(() => {
    const diffs = activeStudioDoc?.bullet_diffs?.map((b) => b.tailored_bullet) || [];
    if (diffs.length > 0) return diffs;
    const fromExp = (activePersona?.experience_highlights || []).map((e) => e.achievements[0]).filter(Boolean);
    return fromExp.length > 0
      ? fromExp
      : [
        'Architected end-to-end automated customer scoring and demand forecasting pipelines in Python & FastAPI.',
        'Deployed containerized ML inference workers on Docker & PostgreSQL reducing p95 latency by 38%.',
      ];
  }, [activeStudioDoc, activePersona]);

  const baseInitialSummary = useMemo(() => {
    const stripped = stripLeadingRoleFromBioClient(activePersona?.summary_bio || '');
    const normalized = stripped ? stripped.charAt(0).toUpperCase() + stripped.slice(1) : '';
    return (
      normalized ||
      'Senior Data Scientist & AI Systems Engineer delivering production regression engines, FastAPI inference pipelines, and scalable analytics.'
    );
  }, [activePersona]);

  const isImportedCustomDoc =
    activeStudioDoc?.generation_mode === 'imported_tex' ||
    activeStudioDoc?.generation_mode === 'imported_pdf' ||
    activeStudioDoc?.generation_mode === 'blank_latex';

  const importedDocParsed = useMemo(() => {
    if (!isImportedCustomDoc || !activeStudioDoc?.tailored_latex_content) return null;
    const seedFallback = buildParsedCvSnapshot({
      profile,
      personaId: activeStudioDoc.persona_id || activePersona?.persona_id,
      activeRegionalPhone,
      docDetail: activeStudioDoc,
    });
    return parseLatexToCv(activeStudioDoc.tailored_latex_content, seedFallback);
  }, [isImportedCustomDoc, activeStudioDoc, profile, activePersona?.persona_id, activeRegionalPhone]);

  const initialSummary =
    isImportedCustomDoc && importedDocParsed?.summary ? importedDocParsed.summary : baseInitialSummary;
  const initialBullets =
    isImportedCustomDoc && importedDocParsed?.flatBullets?.length
      ? importedDocParsed.flatBullets
      : baseInitialBullets;

  const [jobOverrides, setJobOverrides] = useState<Record<string, { summary: string; bullets: string[] }>>({});
  const [latexOverrides, setLatexOverrides] = useState<Record<string, string>>({});
  const [texCursorPos, setTexCursorPos] = useState<{ line: number; col: number }>({ line: 1, col: 1 });
  const [texSyncPulse, setTexSyncPulse] = useState(false);

  const summaryText = jobOverrides[docKey]?.summary ?? initialSummary;
  const bullets = jobOverrides[docKey]?.bullets ?? initialBullets;

  const setSummaryForJob = (nextSummary: string, keepLatex = false) => {
    setJobOverrides((prev) => ({
      ...prev,
      [docKey]: {
        summary: nextSummary,
        bullets: prev[docKey]?.bullets ?? initialBullets,
      },
    }));
    if (!keepLatex) {
      setLatexOverrides((prev) => {
        if (!(docKey in prev)) return prev;
        const copy = { ...prev };
        delete copy[docKey];
        return copy;
      });
    }
  };

  const setBulletsForJob = (nextBullets: string[], keepLatex = false) => {
    setJobOverrides((prev) => ({
      ...prev,
      [docKey]: {
        summary: prev[docKey]?.summary ?? initialSummary,
        bullets: nextBullets,
      },
    }));
    if (!keepLatex) {
      setLatexOverrides((prev) => {
        if (!(docKey in prev)) return prev;
        const copy = { ...prev };
        delete copy[docKey];
        return copy;
      });
    }
  };

  const [editingAnchor, setEditingAnchor] = useState<string | null>(null);
  const [editBuffer, setEditBuffer] = useState<string>('');
  const [highlightedAnchor, setHighlightedAnchor] = useState<string | null>(null);
  const [appliedAnchorId, setAppliedAnchorId] = useState<string | null>(null);
  const [fitPulse, setFitPulse] = useState(false);
  const [focusedAnchor, setFocusedAnchor] = useState<{ id: string; label: string } | null>(null);
  const [activePreview, setActivePreview] = useState<AtelierPreviewData | null>(null);
  const [threadScope, setThreadScope] = useState<'role' | 'workspace'>('role');

  const headerRef = useRef<HTMLElement>(null);
  const anchorRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const texGutterRef = useRef<HTMLDivElement>(null);
  const texEditorRef = useRef<HTMLTextAreaElement>(null);
  const cvFileInputRef = useRef<HTMLInputElement>(null);
  const cvDropTextareaRef = useRef<HTMLTextAreaElement>(null);
  const cvListRef = useRef<HTMLDivElement>(null);
  const wasCoachOpenBeforeTexRef = useRef<boolean>(true);
  const wasLibraryOpenBeforeTexRef = useRef<boolean>(true);
  const appliedTimerRef = useRef<number | null>(null);
  const pulseTimerRef = useRef<number | null>(null);
  const texPulseTimerRef = useRef<number | null>(null);

  const scrollCvLibraryToTop = () => {
    window.requestAnimationFrame(() => {
      if (cvListRef.current) {
        cvListRef.current.scrollTop = 0;
      }
    });
  };

  useEffect(() => {
    const onMouseDown = (e: MouseEvent) => {
      if (headerRef.current && !headerRef.current.contains(e.target as Node)) {
        setIdentityMenuOpen(false);
        setJobMenuOpen(false);
        setCustomizeOpen(false);
        setExportOpen(false);
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIdentityMenuOpen(false);
        setJobMenuOpen(false);
        setCustomizeOpen(false);
        setExportOpen(false);
        setActivePreview(null);
        setEditingAnchor(null);
        return;
      }
      const el = e.target as HTMLElement | null;
      const typing = el?.tagName === 'INPUT' || el?.tagName === 'TEXTAREA' || el?.isContentEditable;
      if (typing) return;
      if (e.key === ']') {
        e.preventDefault();
        setCoachCollapsed((v) => !v);
      } else if (e.altKey && e.key.toLowerCase() === 's') {
        e.preventDefault();
        setSwapSides((s) => !s);
      }
    };
    window.addEventListener('mousedown', onMouseDown);
    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('keydown', onKeyDown);
      if (appliedTimerRef.current) window.clearTimeout(appliedTimerRef.current);
      if (pulseTimerRef.current) window.clearTimeout(pulseTimerRef.current);
      if (texPulseTimerRef.current) window.clearTimeout(texPulseTimerRef.current);
    };
  }, []);

  const [versions, setVersions] = useState<VersionSnapshot[]>([
    { version: 1, label: 'Initial Tailor', summary: initialSummary, bullets: initialBullets },
  ]);
  const [versionIdx, setVersionIdx] = useState<number>(0);

  const fitEval = useMemo(
    () => evaluateAllPersonas(activeStudioJob, profile).best,
    [activeStudioJob, profile]
  );

  const targetCompany = cleanCompanyName(activeStudioJob.company_name);
  const targetRole = cleanTargetJobTitle(activeStudioJob.title);

  // Dynamically derived default AI Coach message synced strictly with activeStudioJob / Blank CV Canvas
  const defaultMessagesForJob = useMemo<AiChatMessage[]>(() => {
    if (isBlankCvMode) {
      return [
        {
          id: 'cv_blank_seed',
          role: 'assistant',
          text: 'Drop a PDF or .tex file, paste a job link/JD, or pick a saved role on the left to create a new CV in your workspace.',
        },
      ];
    }
    const openingText =
      fitEval.missingSkills.length > 0
        ? `Missing ${fitEval.missingSkills.slice(0, 2).join(', ')} for ${targetCompany}. Click any bullet on the CV or apply this opening polish:`
        : `Strong fit for ${targetCompany}. Click any bullet on the sheet to edit, or apply this tighter opening phrasing:`;
    const primaryExp = activePersona?.experience_highlights[0];
    const baseBullet = initialBullets[0] || '';
    return [
      {
        id: `m_init_${docKey}`,
        role: 'assistant',
        text: openingText,
        proposal: {
          id: `prop_init_${docKey}`,
          targetAnchorId: 'bullet-0',
          targetLabel: `${primaryExp?.company || 'Primary Role'} · Bullet 1`,
          oldText: baseBullet,
          newText: buildCleanLeadRewrite(baseBullet),
          status: 'pending',
        },
      },
    ];
  }, [isBlankCvMode, docKey, targetCompany, fitEval.missingSkills, activePersona, initialBullets]);

  const threadKey = isBlankCvMode
    ? 'cv_blank_new'
    : threadScope === 'workspace'
      ? 'workspace_global'
      : `job_${activeStudioJob.id}`;
  const messages = coachThreads[threadKey] ?? defaultMessagesForJob;
  const setMessagesForJob = (updater: (curr: AiChatMessage[]) => AiChatMessage[]) =>
    updateCoachThread(threadKey, defaultMessagesForJob, updater);

  const [coachMode, setCoachMode] = useState<string>('Surgical');
  const [isStreaming, setIsStreaming] = useState(false);

  const dispatchedJobIds = useMemo(
    () =>
      new Set(
        pipelineItems
          .filter((p) => p.status === 'applied' || p.status === 'interview')
          .map((p) => p.job.id)
      ),
    [pipelineItems]
  );

  const pushNewVersion = (label: string, nextSum: string, nextBullets: string[], nextLatex?: string) => {
    setVersions((prev) => {
      const sliced = prev.slice(0, versionIdx + 1);
      const nextVer = sliced.length + 1;
      return [...sliced, { version: nextVer, label, summary: nextSum, bullets: nextBullets, latex: nextLatex }];
    });
    setVersionIdx((idx) => idx + 1);
    if (activeStudioDoc) {
      const updatedDetail: CvFitDetail = {
        ...activeStudioDoc,
        ...(nextLatex ? { tailored_latex_content: nextLatex } : {}),
        bullet_diffs: activeStudioDoc.bullet_diffs.map((bd, i) => ({
          ...bd,
          tailored_bullet: nextBullets[i] ?? bd.tailored_bullet,
        })),
      };
      saveStudioDocUpdate(updatedDetail);
    }
  };

  const restoreVersion = (nextIdx: number) => {
    const snap = versions[nextIdx];
    if (!snap) return;
    setVersionIdx(nextIdx);
    setJobOverrides((prev) => ({
      ...prev,
      [docKey]: {
        summary: snap.summary,
        bullets: snap.bullets,
      },
    }));
    setLatexOverrides((prev) => {
      if (snap.latex) {
        return { ...prev, [docKey]: snap.latex };
      }
      if (!(docKey in prev)) return prev;
      const copy = { ...prev };
      delete copy[docKey];
      return copy;
    });
  };

  const openNewBlankCv = () => {
    setIsBlankCvMode(true);
    setActivePreview(null);
    setEditingAnchor(null);
    setCvDropInput('');
    if (cvAttachedFile?.previewUrl) URL.revokeObjectURL(cvAttachedFile.previewUrl);
    setCvAttachedFile(null);
    if (viewMode === 'tex') setViewMode('paper');
    scrollCvLibraryToTop();
    window.requestAnimationFrame(() => cvDropTextareaRef.current?.focus());
  };

  const openLibraryCv = (docId: string) => {
    setIsBlankCvMode(false);
    setActivePreview(null);
    setEditingAnchor(null);
    void openDocInStudio(docId);
  };

  const attachCvDropFile = async (file: File) => {
    const lower = file.name.toLowerCase();
    if (cvAttachedFile?.previewUrl) {
      URL.revokeObjectURL(cvAttachedFile.previewUrl);
    }
    if (lower.endsWith('.tex') || file.type.includes('tex')) {
      const rawText = await file.text();
      setCvAttachedFile({
        kind: 'tex',
        name: file.name,
        previewUrl: '',
        rawText,
      });
      pushToast(`Loaded ${file.name} — ready to import into CV Studio.`);
      return;
    }
    if (lower.endsWith('.pdf') || file.type === 'application/pdf') {
      const buf = await file.arrayBuffer();
      const extractedText = extractPdfPlainTextBestEffort(buf);
      setCvAttachedFile({
        kind: 'pdf',
        name: file.name,
        previewUrl: '',
        rawText: extractedText,
      });
      pushToast(`Loaded ${file.name} — ready to convert into editable LaTeX CV.`);
      return;
    }
    if (file.type.startsWith('image/')) {
      const previewUrl = URL.createObjectURL(file);
      setCvAttachedFile({
        kind: 'image',
        name: file.name || 'Job Screenshot',
        previewUrl,
        rawText: '',
      });
      pushToast(`Attached screenshot "${file.name || 'Clipboard Image'}".`);
      return;
    }
    const textContent = await file.text();
    setCvDropInput((prev) => (prev.trim() ? `${prev.trim()}\n${textContent}` : textContent));
  };

  const handleCvDropZonePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const items = Array.from(e.clipboardData?.items || []);
    const imgItem = items.find((item) => item.type.startsWith('image/'));
    if (imgItem) {
      const file = imgItem.getAsFile();
      if (file) {
        e.preventDefault();
        void attachCvDropFile(file);
      }
    }
  };

  const handleCvDropZoneDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setCvDraggingOver(false);
    const file = e.dataTransfer?.files?.[0];
    if (file) {
      await attachCvDropFile(file);
      return;
    }
    const droppedText = e.dataTransfer?.getData('text/plain') || e.dataTransfer?.getData('text/uri-list');
    if (droppedText) {
      setCvDropInput((prev) => (prev.trim() ? `${prev.trim()}\n${droppedText}` : droppedText));
    }
  };

  const handleCreateNewCvFromDrop = async () => {
    if (isCreatingCv) return;
    if (!cvDropInput.trim() && !cvAttachedFile) {
      pushToast('Drop a PDF / .tex CV, paste a job link or JD, or pick a saved role.', { variant: 'warn' });
      return;
    }

    setIsCreatingCv(true);
    try {
      if (cvAttachedFile?.kind === 'tex') {
        const imported = buildImportedTexCvDetail({
          fileName: cvAttachedFile.name,
          texContent: cvAttachedFile.rawText,
          profile,
          personaId: activePersona?.persona_id,
        });
        registerStudioDoc(imported);
        setActiveStudioJob(buildSyntheticJobFromDoc(imported));
        setIsBlankCvMode(false);
        setViewMode('paper');
        scrollCvLibraryToTop();
        setCvDropInput('');
        setCvAttachedFile(null);
        pushToast(`Imported ${cvAttachedFile.name} into Saved CVs.`, { variant: 'success' });
        return;
      }

      if (cvAttachedFile?.kind === 'pdf') {
        const pdfDoc = buildImportedPdfCvDetail({
          fileName: cvAttachedFile.name,
          extractedText: cvAttachedFile.rawText,
          profile,
          activePersona,
          phoneDisplay,
          locationLabel,
        });
        registerStudioDoc(pdfDoc);
        setActiveStudioJob(buildSyntheticJobFromDoc(pdfDoc));
        setIsBlankCvMode(false);
        setViewMode('paper');
        scrollCvLibraryToTop();
        setCvDropInput('');
        setCvAttachedFile(null);
        pushToast(`Imported ${cvAttachedFile.name} into CV Studio.`, { variant: 'success' });
        return;
      }

      const parsed = parseCoverLetterDropInput({
        rawText: cvDropInput,
        hasScreenshot: cvAttachedFile?.kind === 'image',
        screenshotName: cvAttachedFile?.name,
      });

      let targetJob: JobItem | null = null;
      if (parsed.sourceKind === 'link' || parsed.sourceKind === 'jd') {
        try {
          targetJob = await ingestJobUrlOrText(cvDropInput.trim(), { onlySaveInterest: true });
        } catch {
          targetJob = null;
        }
      }
      if (!targetJob) {
        targetJob = buildDroppedTargetJobRecord({
          company: parsed.company,
          role: parsed.role,
          location: parsed.location,
          url: parsed.url,
          skills: parsed.skills,
          summaryDescription: parsed.summaryDescription,
          recipientEmail: parsed.recipientEmail,
          sourceKind: parsed.sourceKind,
        });
        setRadarJobs((prev) => [targetJob!, ...prev]);
      }

      const res = await CvFitAPI.tailorCv(
        {
          profile_id: currentProfile?.id || 1,
          persona_id: activePersonaId,
          job_id: targetJob.id,
          job_title: cleanTargetJobTitle(targetJob.title),
          company_name: cleanCompanyName(targetJob.company_name),
          location: targetJob.location,
          location_type: targetJob.location_type,
          fit_score: targetJob.fit_score,
          parsed_skills: targetJob.parsed_skills || [],
          job_description_text: targetJob.raw_description,
        },
        profile
      );

      registerStudioDoc(res.data);
      setActiveStudioJob(targetJob);
      setIsBlankCvMode(false);
      setViewMode('paper');
      scrollCvLibraryToTop();

      if (cvAttachedFile?.previewUrl) URL.revokeObjectURL(cvAttachedFile.previewUrl);
      setCvAttachedFile(null);
      setCvDropInput('');
      setFitPulse(true);
      if (pulseTimerRef.current) window.clearTimeout(pulseTimerRef.current);
      pulseTimerRef.current = window.setTimeout(() => setFitPulse(false), 700);
      pushToast(`Created tailored CV for ${parsed.company} (${parsed.role}).`, { variant: 'success' });
    } finally {
      setIsCreatingCv(false);
    }
  };

  const handleCreateBlankLatexCv = () => {
    const blankDoc = buildBlankLatexCvDetail({
      profile,
      activePersona,
      phoneDisplay,
      locationLabel,
    });
    registerStudioDoc(blankDoc);
    setActiveStudioJob(buildSyntheticJobFromDoc(blankDoc));
    setIsBlankCvMode(false);
    setViewMode('paper');
    scrollCvLibraryToTop();
    setCvDropInput('');
    if (cvAttachedFile?.previewUrl) URL.revokeObjectURL(cvAttachedFile.previewUrl);
    setCvAttachedFile(null);
    pushToast('Created editable draft from your Master Profile.', { variant: 'info' });
  };

  const handleCreateCvFromSavedRole = (job: JobItem) => {
    setIsBlankCvMode(false);
    setCvDropInput('');
    if (cvAttachedFile?.previewUrl) URL.revokeObjectURL(cvAttachedFile.previewUrl);
    setCvAttachedFile(null);
    scrollCvLibraryToTop();
    void openJobInStudio(job);
  };

  const handleApplyProposal = (proposalId: string) => {
    const msg = messages.find((m) => m.proposal?.id === proposalId);
    const prop = msg?.proposal;
    if (!prop) return;

    if (prop.targetAnchorId === 'summary') {
      setSummaryForJob(prop.newText);
      pushNewVersion('AI Summary Refine', prop.newText, bullets);
    } else if (prop.targetAnchorId.startsWith('bullet-')) {
      const bIdx = Number(prop.targetAnchorId.replace('bullet-', '')) || 0;
      const updated = bullets.map((b, i) => (i === bIdx ? prop.newText : b));
      setBulletsForJob(updated);
      pushNewVersion(`AI Bullet ${bIdx + 1}`, summaryText, updated);
    }

    setMessagesForJob((prev) =>
      prev.map((m) =>
        m.proposal?.id === proposalId ? { ...m, proposal: { ...m.proposal, status: 'applied' } } : m
      )
    );
    setAppliedAnchorId(prop.targetAnchorId);
    setFitPulse(true);
    if (appliedTimerRef.current) window.clearTimeout(appliedTimerRef.current);
    if (pulseTimerRef.current) window.clearTimeout(pulseTimerRef.current);
    appliedTimerRef.current = window.setTimeout(() => setAppliedAnchorId(null), 1100);
    pulseTimerRef.current = window.setTimeout(() => setFitPulse(false), 700);
    if (getAccessToken()) {
      void AgentAPI.resolveProposal(proposalId, 'apply').catch(() => {});
    }
    TelemetrySDK.track('ui.proposal.resolved', 'ai.coach.proposal.resolve', {
      docId: activeStudioDoc?.doc_id,
      isMicroSignal: true,
      properties: { resolution: 'applied' },
    });
    pushToast('Applied edit to living document.', {
      variant: 'success',
      undoLabel: 'Undo',
      onUndo: () => handleUndoProposal(proposalId),
    });
  };

  const handleUndoProposal = (proposalId: string) => {
    const msg = messages.find((m) => m.proposal?.id === proposalId);
    const prop = msg?.proposal;
    if (!prop) return;

    if (prop.targetAnchorId === 'summary') {
      setSummaryForJob(prop.oldText);
    } else if (prop.targetAnchorId.startsWith('bullet-')) {
      const bIdx = Number(prop.targetAnchorId.replace('bullet-', '')) || 0;
      setBulletsForJob(bullets.map((b, i) => (i === bIdx ? prop.oldText : b)));
    }
    setMessagesForJob((prev) =>
      prev.map((m) =>
        m.proposal?.id === proposalId ? { ...m, proposal: { ...m.proposal, status: 'pending' } } : m
      )
    );
    pushToast('Reverted proposal change.');
  };

  const handleSkipProposal = (proposalId: string) => {
    setMessagesForJob((prev) =>
      prev.map((m) =>
        m.proposal?.id === proposalId ? { ...m, proposal: { ...m.proposal, status: 'skipped' } } : m
      )
    );
  };

  const handleRefineProposal = (proposalId: string, instruction: string) => {
    setMessagesForJob((prev) =>
      prev.map((m) => {
        if (m.proposal?.id !== proposalId) return m;
        const refinedText = instruction.toLowerCase().includes('short')
          ? `${m.proposal.newText.split(',')[0]}.`
          : `${m.proposal.newText.replace(/\.$/, '')} (${instruction.trim()}).`;
        return {
          ...m,
          proposal: {
            ...m.proposal,
            newText: refinedText,
            status: 'pending',
          },
        };
      })
    );
    pushToast('Refined proposal in-place.');
  };

  const handlePreviewResource = (res: AiResourceItem) => {
    if (res.kind === 'cv') {
      const doc = res.payloadId !== 'base' ? tailoredDocs.find((d) => d.doc_id === res.payloadId) || null : null;
      const matchedDetail = activeStudioDoc && doc && activeStudioDoc.doc_id === doc.doc_id ? activeStudioDoc : null;
      const cvSnapshot = buildParsedCvSnapshot({
        profile,
        personaId: doc?.persona_id || activePersona?.persona_id,
        activeRegionalPhone,
        docDetail: matchedDetail,
        docSummary: doc,
      });
      setActivePreview({
        kind: 'cv',
        id: res.id,
        title: res.title,
        subtitle: res.subtitle,
        fitScore: res.fitScore,
        cvDocument: cvSnapshot,
        matchedSkills: doc?.parsed_skills || fitEval.matchedSkills,
        primaryActionLabel: res.payloadId === 'base' ? 'Use Base CV' : 'Load Draft in Studio',
        onPrimaryAction: () => {
          if (doc) openLibraryCv(doc.doc_id);
          setActivePreview(null);
        },
      });
      return;
    }
    if (res.kind === 'letter') {
      const letter = coverLetters.find((c) => String(c.job_id) === res.payloadId);
      setActivePreview({
        kind: 'letter',
        id: res.id,
        title: res.title,
        subtitle: 'Saved Cover Letter',
        subjectLine: letter?.subject_line,
        bodyText: letter?.body_markdown,
        primaryActionLabel: 'Open in Cover Letters',
        onPrimaryAction: () => {
          const j = allTargetOptions.find((x) => String(x.id) === res.payloadId);
          setActivePreview(null);
          if (j) openJobInCoverLetters(j, { mode: 'pitch' });
        },
      });
      return;
    }
    if (res.kind === 'job') {
      const j = allTargetOptions.find((x) => String(x.id) === res.payloadId);
      if (!j) return;
      const je = evaluateAllPersonas(j, profile).best;
      setActivePreview({
        kind: 'job',
        id: res.id,
        title: cleanTargetJobTitle(j.title),
        subtitle: `${cleanCompanyName(j.company_name)} · ${j.location}`,
        fitScore: je.overallScore,
        summary: j.raw_description,
        bullets: j.responsibilities,
        matchedSkills: je.matchedSkills,
        missingSkills: je.missingSkills,
        primaryActionLabel: 'Switch Target Role',
        onPrimaryAction: () => {
          setActiveStudioJob(j);
          setActivePreview(null);
        },
      });
    }
  };

  const handleSelectResource = (res: AiResourceItem) => {
    if (res.kind === 'cv') {
      if (res.payloadId === 'base') {
        setBulletsForJob(activePersona?.experience_highlights.map((e) => e.achievements[0]).filter(Boolean) || bullets);
        pushToast('Loaded Master Profile baseline bullets.');
      } else {
        openDocInStudio(res.payloadId);
      }
      return;
    }
    if (res.kind === 'letter') {
      const j = allTargetOptions.find((x) => String(x.id) === res.payloadId) || activeStudioJob;
      openJobInCoverLetters(j, { mode: 'pitch' });
      return;
    }
    if (res.kind === 'job') {
      const j = allTargetOptions.find((x) => String(x.id) === res.payloadId);
      if (j) setActiveStudioJob(j);
    }
  };

  const handleConfirmAction = (actionId: string) => {
    const card = messages.find((m) => m.actionCard?.id === actionId)?.actionCard;
    if (!card) return;
    if (card.actionType === 'pipeline_stage') {
      const nextStatus = (card.payload?.status as 'applied' | 'interview' | 'saved') || 'applied';
      addToPipeline(activeStudioJob, nextStatus, activeStudioJob.recruiter_email || null, {
        tailoredCvDocId: activeStudioDoc?.doc_id || null,
        silent: true,
      });
      pushToast(`Pipeline updated: ${targetCompany} marked ${nextStatus}.`, { variant: 'success' });
    }
    setMessagesForJob((prev) =>
      prev.map((m) =>
        m.actionCard?.id === actionId ? { ...m, actionCard: { ...m.actionCard, status: 'confirmed' } } : m
      )
    );
    if (getAccessToken()) {
      void AgentAPI.confirmAction(actionId, true).catch(() => {});
    }
  };

  const handleAuditAction = (aud: AiAuditItem) => {
    if (aud.actionType === 'open_followup' || aud.actionType === 'open_letter') {
      const j =
        pipelineItems.find((p) => String(p.job.id) === aud.payloadId)?.job ||
        allTargetOptions.find((x) => String(x.id) === aud.payloadId);
      if (j) {
        openJobInCoverLetters(j, {
          mode: aud.actionType === 'open_followup' ? 'followup' : 'pitch',
        });
      }
      return;
    }
    if (aud.actionType === 'inject_text' && aud.payloadId) {
      setFocusedAnchor({ id: 'bullet-0', label: `Bullet 1 · Bridge ${aud.payloadId}` });
      const cur = bullets[0] || '';
      if (!cur.toLowerCase().includes(aud.payloadId.toLowerCase())) {
        const updated = bullets.map((b, i) =>
          i === 0 ? `${b.replace(/\.$/, '')} with production readiness for ${aud.payloadId}.` : b
        );
        setBulletsForJob(updated);
        pushNewVersion(`Bridged ${aud.payloadId}`, summaryText, updated);
        pushToast(`Inserted ${aud.payloadId} alignment into Bullet 1.`);
      }
    }
  };

  const agentThreadIdRef = useRef<Record<string, string>>({});

  const handleSendCoachMessage = async (prompt: string, mode: string) => {
    const userMsg: AiChatMessage = {
      id: `u_${Date.now()}`,
      role: 'user',
      text: prompt,
    };
    setMessagesForJob((prev) => [...prev, userMsg]);
    setIsStreaming(true);

    if (getAccessToken()) {
      const assistantId = `a_${Date.now()}`;
      try {
        const key = String(activeStudioJob.id);
        let threadId = agentThreadIdRef.current[key];
        if (!threadId) {
          const th = await AgentAPI.createThread({
            surface: 'cv',
            job_id: resolveServerJobId(activeStudioJob.id, activeStudioJob.server_id),
            doc_id: activeStudioDoc?.doc_id,
            title: `${targetCompany} — ${cleanTargetJobTitle(activeStudioJob.title)}`,
          });
          threadId = th.id;
          agentThreadIdRef.current[key] = threadId;
        }
        setMessagesForJob((prev) => [...prev, { id: assistantId, role: 'assistant', text: '' }]);
        await AgentAPI.streamMessage(
          threadId,
          {
            prompt,
            mode,
            focused_anchor: focusedAnchor,
            job_id: resolveServerJobId(activeStudioJob.id, activeStudioJob.server_id),
            doc_id: activeStudioDoc?.doc_id,
          },
          {
            onThinkingStep: (step) =>
              setMessagesForJob((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, thinkingSummary: step } : m))
              ),
            onTextDelta: (delta) =>
              setMessagesForJob((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, text: `${m.text}${delta}` } : m))
              ),
            onProposalCard: (proposal) =>
              setMessagesForJob((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, proposal } : m))
              ),
            onActionCard: (actionCard) =>
              setMessagesForJob((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, actionCard } : m))
              ),
            onResourceList: (resources) =>
              setMessagesForJob((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, resources } : m))
              ),
            onAuditSummary: (audit) =>
              setMessagesForJob((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, audit } : m))
              ),
          }
        );
        setIsStreaming(false);
        return;
      } catch {
        setMessagesForJob((prev) => prev.filter((m) => m.id !== assistantId));
      }
    }

    const workspaceReply = buildWorkspaceCoachReply({
      prompt,
      surface: 'cv',
      activeJob: activeStudioJob,
      profile,
      tailoredDocs,
      coverLetters,
      radarJobs,
      pipelineItems,
    });

    const targetId = focusedAnchor?.id || 'bullet-0';
    const targetLabel =
      focusedAnchor?.label ||
      `${activePersona?.experience_highlights[0]?.company || 'Experience'} · Bullet 1`;

    const currentOld =
      targetId === 'summary'
        ? summaryText
        : bullets[Number(targetId.replace('bullet-', '')) || 0] || bullets[0] || '';

    const nextCandidate =
      mode === 'Condense'
        ? `${currentOld.split(/[,—]/)[0].trim().replace(/\.$/, '')}.`
        : mode === 'Metrics+'
          ? `${currentOld.replace(/\.$/, '')}, sustaining sub-120ms p95 latency in production.`
          : buildCleanLeadRewrite(currentOld);

    setTimeout(() => {
      if (workspaceReply) {
        setMessagesForJob((prev) => [...prev, workspaceReply]);
        setIsStreaming(false);
        return;
      }
      const assistantMsg: AiChatMessage = {
        id: `a_${Date.now()}`,
        role: 'assistant',
        text: 'Updated based on your Master Profile:',
        thinkingSummary: `Audited ${targetLabel} against ${targetCompany} JD.`,
        proposal: {
          id: `prop_${Date.now()}`,
          targetAnchorId: targetId,
          targetLabel,
          oldText: currentOld,
          newText: nextCandidate,
          status: 'pending',
        },
      };
      setMessagesForJob((prev) => [...prev, assistantMsg]);
      setIsStreaming(false);
    }, 360);
  };

  const commitInlineEdit = () => {
    if (!editingAnchor) return;
    if (editingAnchor === 'summary') {
      setSummaryForJob(editBuffer);
      pushNewVersion('Manual Summary Edit', editBuffer, bullets);
    } else if (editingAnchor.startsWith('bullet-')) {
      const idx = Number(editingAnchor.replace('bullet-', ''));
      const next = bullets.map((b, i) => (i === idx ? editBuffer : b));
      setBulletsForJob(next);
      pushNewVersion(`Manual Bullet ${idx + 1}`, summaryText, next);
    }
    setEditingAnchor(null);
  };

  const handleShortenBullet = (idx: number) => {
    const shortened = `${bullets[idx].split(/[—;]/)[0].trim().replace(/\.$/, '')}.`;
    const next = bullets.map((b, i) => (i === idx ? shortened : b));
    setBulletsForJob(next);
    pushNewVersion(`Shortened Bullet ${idx + 1}`, summaryText, next);
    pushToast('Condensed bullet to 1 sharp line.');
  };

  const targetSeen = new Set<number>();
  const allTargetOptions = [activeStudioJob, ...interestList, ...radarJobs].filter((j) => {
    if (targetSeen.has(j.id)) return false;
    targetSeen.add(j.id);
    return true;
  });

  const exps = useMemo(() => activePersona?.experience_highlights || [], [activePersona]);
  const projects = useMemo(() => activePersona?.featured_projects || [], [activePersona]);
  const certs = useMemo(() => activePersona?.certifications || [], [activePersona]);
  const langs = useMemo(() => profile.languages || [], [profile.languages]);
  const skillBuckets = activePersona?.skills_and_tools;

  const fallbackParsedCv = useMemo<ParsedLatexCv>(() => {
    const skillRows = skillBuckets
      ? [
        { label: 'Core Disciplines', value: skillBuckets.core_skills.join(' · ') },
        ...(skillBuckets.programming_languages.length > 0
          ? [{ label: 'Languages & Data', value: skillBuckets.programming_languages.join(' · ') }]
          : []),
        ...(skillBuckets.frameworks_and_libraries.length > 0
          ? [{ label: 'Frameworks & AI', value: skillBuckets.frameworks_and_libraries.join(' · ') }]
          : []),
        ...(skillBuckets.tools_and_platforms.length > 0
          ? [{ label: 'Cloud & MLOps', value: skillBuckets.tools_and_platforms.join(' · ') }]
          : []),
      ]
      : [];
    const mappedExps = exps.map((exp, expIdx) => {
      const roleBullets =
        exps.length === 1
          ? bullets.length >= exp.achievements.length
            ? bullets
            : [...bullets, ...exp.achievements.slice(bullets.length)]
          : [bullets[expIdx] ?? exp.achievements[0], ...exp.achievements.slice(1)].filter(Boolean);
      return {
        role: exp.role,
        company: exp.company,
        dates: `${exp.start_date} – ${exp.end_date}`,
        location: exp.location || locationLabel,
        bullets: roleBullets,
      };
    });
    return {
      fullName: profile.personal_info.full_name,
      headlineLine: `${activePersona?.target_title || 'Candidate'} · ${locationLabel}`,
      contactLine: `${phoneDisplay} · ${profile.personal_info.primary_email} · ${(profile.personal_info.links.linkedin || 'linkedin.com/in/candidate').replace('https://', '')} · ${(profile.personal_info.links.github || 'github.com/candidate').replace('https://', '')}`,
      summary: summaryText,
      skillRows,
      experiences: mappedExps,
      flatBullets: bullets,
      projects: projects.map((pr) => ({ name: pr.name, summary: pr.summary })),
      education: profile.education.map((ed) => ({
        title: ed.degree,
        subtitle: `${ed.institution}${ed.graduation_year ? ` · ${ed.graduation_year}` : ''}`,
      })),
      certs: certs.slice(0, 2).map((c) => `${c.name} · ${c.issuer}`),
      languages: langs.map((l) => `${l.language} (${l.proficiency})`).join(', '),
      warnings: [],
    };
  }, [
    skillBuckets,
    exps,
    bullets,
    locationLabel,
    profile.personal_info,
    profile.education,
    activePersona,
    phoneDisplay,
    summaryText,
    projects,
    certs,
    langs,
  ]);

  const baseLatexForJob = useMemo(
    () =>
      buildCanonicalCvLatex({
        profile,
        activePersona,
        phoneDisplay,
        locationLabel,
        summaryText: initialSummary,
        bullets: initialBullets,
      }),
    [profile, activePersona, phoneDisplay, locationLabel, initialSummary, initialBullets]
  );

  const syncedLatexFromStructured = useMemo(
    () =>
      buildCanonicalCvLatex({
        profile,
        activePersona,
        phoneDisplay,
        locationLabel,
        summaryText,
        bullets,
      }),
    [profile, activePersona, phoneDisplay, locationLabel, summaryText, bullets]
  );

  const activeLatex =
    latexOverrides[docKey] ??
    (!(docKey in jobOverrides) && activeStudioDoc?.tailored_latex_content
      ? activeStudioDoc.tailored_latex_content
      : syncedLatexFromStructured);

  const parsedLiveCv = useMemo(
    () => parseLatexToCv(activeLatex, fallbackParsedCv),
    [activeLatex, fallbackParsedCv]
  );

  const latexAudit = useMemo(
    () => computeLatexLineDiff(baseLatexForJob, activeLatex),
    [baseLatexForJob, activeLatex]
  );

  const latexLines = useMemo(() => activeLatex.split('\n'), [activeLatex]);
  const warningLinesSet = useMemo(
    () => new Set(parsedLiveCv.warnings.map((w) => w.line)),
    [parsedLiveCv.warnings]
  );

  const switchStudioViewMode = (nextMode: 'paper' | 'diff' | 'tex') => {
    if (nextMode === viewMode) return;
    if (nextMode === 'tex') {
      wasCoachOpenBeforeTexRef.current = !coachCollapsed;
      wasLibraryOpenBeforeTexRef.current = cvLibraryOpen;
      setCoachCollapsed(true);
      setCvLibraryOpen(false);
    } else if (viewMode === 'tex') {
      if (wasCoachOpenBeforeTexRef.current) setCoachCollapsed(false);
      if (wasLibraryOpenBeforeTexRef.current) setCvLibraryOpen(true);
    }
    setViewMode(nextMode);
  };

  const handleLatexChange = (nextTex: string) => {
    setLatexOverrides((prev) => ({ ...prev, [docKey]: nextTex }));
    const nextParsed = parseLatexToCv(nextTex, fallbackParsedCv);
    setJobOverrides((prev) => ({
      ...prev,
      [docKey]: {
        summary: nextParsed.summary || summaryText,
        bullets: nextParsed.flatBullets.length > 0 ? nextParsed.flatBullets : bullets,
      },
    }));
    setTexSyncPulse(true);
    if (texPulseTimerRef.current) window.clearTimeout(texPulseTimerRef.current);
    texPulseTimerRef.current = window.setTimeout(() => setTexSyncPulse(false), 600);
  };

  const syncTexCursor = (el: HTMLTextAreaElement) => {
    const pos = el.selectionStart || 0;
    const before = el.value.slice(0, pos);
    const lines = before.split('\n');
    setTexCursorPos({
      line: lines.length,
      col: (lines[lines.length - 1]?.length || 0) + 1,
    });
  };

  const handleTexKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const el = e.currentTarget;
      const start = el.selectionStart;
      const end = el.selectionEnd;
      const next = `${el.value.slice(0, start)}  ${el.value.slice(end)}`;
      handleLatexChange(next);
      window.requestAnimationFrame(() => {
        if (texEditorRef.current) {
          texEditorRef.current.selectionStart = start + 2;
          texEditorRef.current.selectionEnd = start + 2;
        }
      });
    }
  };

  const renderCvPaperSheet = (opts: { interactive: boolean; data: ParsedLatexCv; compactPreview?: boolean }) => {
    const { interactive, data, compactPreview } = opts;
    const displayedSummary = interactive ? summaryText : data.summary;

    return (
      <div
        className={`t-atelier-sheet ${compactPreview ? 't-tex-preview-sheet' : ''}`}
        style={{
          transform: `scale(${zoomPct / 100})`,
          padding: paperDensity === 'compact' || compactPreview ? '20px 28px' : '26px 34px',
        }}
      >
        {/* ATS Contact Header */}
        <div style={{ textAlign: 'center', borderBottom: '1.5px solid var(--ink)', paddingBottom: 10, marginBottom: 12 }}>
          <div style={{ fontFamily: 'var(--font-voice)', fontSize: 24, fontWeight: 600, letterSpacing: '-0.02em', lineHeight: 1.15 }}>
            {data.fullName}
          </div>
          <div className="t-mono" style={{ fontSize: 10.5, color: 'var(--n700)', marginTop: 3 }}>
            {data.headlineLine}
          </div>
          <div className="t-mono" style={{ fontSize: 10.5, color: 'var(--n500)', marginTop: 2 }}>
            {data.contactLine}
          </div>
        </div>

        {/* Summary Section */}
        <div style={{ marginBottom: 12 }}>
          <div className="t-mono" style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', borderBottom: '1px solid var(--n300)', paddingBottom: 2, marginBottom: 6 }}>
            PROFESSIONAL SUMMARY
          </div>
          {interactive ? (
            <div
              ref={(el) => {
                anchorRefs.current['summary'] = el;
              }}
              className={`t-atelier-bullet ${focusedAnchor?.id === 'summary' ? 't-atelier-bullet--focused' : ''} ${highlightedAnchor === 'summary' ? 't-atelier-bullet--highlighted' : ''
                } ${appliedAnchorId === 'summary' ? 't-atelier-bullet--applied' : ''}`}
            >
              <div className="t-atelier-microbar">
                <button
                  type="button"
                  className="t-microbar-btn"
                  onClick={() => {
                    setCoachCollapsed(false);
                    setFocusedAnchor({ id: 'summary', label: 'Professional Summary' });
                  }}
                >
                  Ask AI
                </button>
                <button
                  type="button"
                  className="t-microbar-btn"
                  onClick={() => {
                    const concise = `${summaryText.split('.')[0].trim()}.`;
                    setSummaryForJob(concise);
                    pushNewVersion('Shortened Summary', concise, bullets);
                  }}
                >
                  Shorten
                </button>
                <button
                  type="button"
                  className="t-microbar-btn"
                  onClick={() => {
                    setEditingAnchor('summary');
                    setEditBuffer(summaryText);
                  }}
                >
                  Edit
                </button>
              </div>

              {editingAnchor === 'summary' ? (
                <div>
                  <textarea
                    className="t-textarea"
                    rows={3}
                    value={editBuffer}
                    onChange={(e) => setEditBuffer(e.target.value)}
                  />
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6, marginTop: 6 }}>
                    <button type="button" className="t-btn t-btn--ghost t-btn--sm" onClick={() => setEditingAnchor(null)}>
                      Cancel
                    </button>
                    <button type="button" className="t-btn t-btn--ink t-btn--sm" onClick={commitInlineEdit}>
                      Save
                    </button>
                  </div>
                </div>
              ) : (
                <p
                  style={{ margin: 0, fontSize: 13, lineHeight: 1.46, cursor: 'text' }}
                  onClick={() => {
                    setEditingAnchor('summary');
                    setEditBuffer(summaryText);
                  }}
                >
                  {displayedSummary}
                </p>
              )}
            </div>
          ) : (
            <p style={{ margin: 0, fontSize: 13, lineHeight: 1.46 }}>{displayedSummary}</p>
          )}
        </div>

        {/* Technical Skills Matrix */}
        {data.skillRows.length > 0 && (
          <div style={{ marginBottom: 12 }}>
            <div className="t-mono" style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', borderBottom: '1px solid var(--n300)', paddingBottom: 2, marginBottom: 6 }}>
              CORE TECHNICAL COMPETENCIES
            </div>
            <div style={{ fontSize: 12.2, lineHeight: 1.48, color: 'var(--n700)', display: 'flex', flexDirection: 'column', gap: 2 }}>
              {data.skillRows.map((row, idx) => (
                <div key={idx}>
                  <strong>{row.label}:</strong> {row.value}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Work Experience */}
        <div style={{ marginBottom: 12 }}>
          <div className="t-mono" style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', borderBottom: '1px solid var(--n300)', paddingBottom: 2, marginBottom: 6 }}>
            WORK EXPERIENCE
          </div>

          {interactive
            ? exps.map((exp, expIdx) => {
              const roleBulletIndices =
                exps.length === 1
                  ? bullets.map((_, idx) => idx)
                  : expIdx < bullets.length
                    ? [expIdx]
                    : [];
              const extraStatic =
                exps.length === 1 ? exp.achievements.slice(bullets.length) : exp.achievements.slice(1);

              return (
                <div key={expIdx} style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 3 }}>
                    <div style={{ fontWeight: 700, fontSize: 13 }}>
                      {exp.role} — {exp.company}
                    </div>
                    <div className="t-mono" style={{ fontSize: 10.5, color: 'var(--n500)' }}>
                      {exp.start_date} – {exp.end_date} · {exp.location || 'Egypt'}
                    </div>
                  </div>

                  {roleBulletIndices.map((bIdx) => {
                    const anchorId = `bullet-${bIdx}`;
                    const bText = bullets[bIdx] ?? exp.achievements[0] ?? '';
                    return (
                      <div
                        key={anchorId}
                        ref={(el) => {
                          anchorRefs.current[anchorId] = el;
                        }}
                        className={`t-atelier-bullet ${focusedAnchor?.id === anchorId ? 't-atelier-bullet--focused' : ''} ${highlightedAnchor === anchorId ? 't-atelier-bullet--highlighted' : ''
                          } ${appliedAnchorId === anchorId ? 't-atelier-bullet--applied' : ''}`}
                      >
                        <div className="t-atelier-microbar">
                          <button
                            type="button"
                            className="t-microbar-btn"
                            onClick={() => {
                              setCoachCollapsed(false);
                              setFocusedAnchor({ id: anchorId, label: `${exp.company} · Bullet ${bIdx + 1}` });
                            }}
                          >
                            Ask AI
                          </button>
                          <button
                            type="button"
                            className="t-microbar-btn"
                            onClick={() => handleShortenBullet(bIdx)}
                          >
                            Shorten
                          </button>
                          <button
                            type="button"
                            className="t-microbar-btn"
                            onClick={() => {
                              setEditingAnchor(anchorId);
                              setEditBuffer(bText);
                            }}
                          >
                            Edit
                          </button>
                        </div>

                        {editingAnchor === anchorId ? (
                          <div>
                            <textarea
                              className="t-textarea"
                              rows={2}
                              value={editBuffer}
                              onChange={(e) => setEditBuffer(e.target.value)}
                            />
                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6, marginTop: 6 }}>
                              <button type="button" className="t-btn t-btn--ghost t-btn--sm" onClick={() => setEditingAnchor(null)}>
                                Cancel
                              </button>
                              <button type="button" className="t-btn t-btn--ink t-btn--sm" onClick={commitInlineEdit}>
                                Save
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div
                            style={{ display: 'flex', gap: 8, fontSize: 12.6, lineHeight: 1.44, cursor: 'text' }}
                            onClick={() => {
                              setEditingAnchor(anchorId);
                              setEditBuffer(bText);
                            }}
                          >
                            <span style={{ color: 'var(--thread)', fontWeight: 700 }}>•</span>
                            <span>{bText}</span>
                          </div>
                        )}
                      </div>
                    );
                  })}

                  {extraStatic.map((eb, eIdx) => (
                    <div key={eIdx} style={{ display: 'flex', gap: 8, fontSize: 12.6, lineHeight: 1.44, padding: '2px 0' }}>
                      <span style={{ color: 'var(--n500)', fontWeight: 700 }}>•</span>
                      <span>{eb}</span>
                    </div>
                  ))}
                </div>
              );
            })
            : data.experiences.map((exp, expIdx) => (
              <div key={expIdx} style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 3 }}>
                  <div style={{ fontWeight: 700, fontSize: 13 }}>
                    {exp.role} {exp.company ? `— ${exp.company}` : ''}
                  </div>
                  <div className="t-mono" style={{ fontSize: 10.5, color: 'var(--n500)' }}>
                    {[exp.dates, exp.location].filter(Boolean).join(' · ')}
                  </div>
                </div>
                {exp.bullets.map((b, bi) => (
                  <div key={bi} style={{ display: 'flex', gap: 8, fontSize: 12.6, lineHeight: 1.44, padding: '2px 0' }}>
                    <span style={{ color: 'var(--thread)', fontWeight: 700 }}>•</span>
                    <span>{b}</span>
                  </div>
                ))}
              </div>
            ))}
        </div>

        {/* Projects & Education / Certifications */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
          <div>
            <div className="t-mono" style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', borderBottom: '1px solid var(--n300)', paddingBottom: 2, marginBottom: 6 }}>
              FEATURED PROJECTS
            </div>
            {data.projects.map((pr, i) => (
              <div key={i} style={{ marginBottom: 6 }}>
                <div style={{ fontWeight: 600, fontSize: 12.2 }}>{pr.name}</div>
                <div style={{ fontSize: 11.8, color: 'var(--n700)', lineHeight: 1.4 }}>{pr.summary}</div>
              </div>
            ))}
          </div>

          <div>
            <div className="t-mono" style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', borderBottom: '1px solid var(--n300)', paddingBottom: 2, marginBottom: 6 }}>
              EDUCATION, CERTS &amp; LANGUAGES
            </div>
            {data.education.map((ed, i) => (
              <div key={i} style={{ marginBottom: 5 }}>
                <div style={{ fontWeight: 600, fontSize: 12.2 }}>{ed.title}</div>
                <div className="t-mono" style={{ fontSize: 10.5, color: 'var(--n500)' }}>
                  {ed.subtitle}
                </div>
              </div>
            ))}
            {data.certs.map((c, i) => (
              <div key={i} className="t-mono" style={{ fontSize: 10.5, color: 'var(--n700)', marginTop: 3 }}>
                {c}
              </div>
            ))}
            {data.languages && (
              <div className="t-mono" style={{ fontSize: 10.5, color: 'var(--n500)', marginTop: 4 }}>
                Languages: {data.languages}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const paperPane = (
    <div className="t-atelier-workbench">
      <AtelierPreviewDrawer preview={activePreview} onClose={() => setActivePreview(null)} />
      {isBlankCvMode ? (
        <div className="t-atelier-desk-scroll">
          <div className="t-cl-blank-dropcard">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
              <div>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, marginBottom: 6 }}>
                  <TailoredIcon name="cv" size={14} color="var(--kraft)" />
                  <span className="t-mono" style={{ fontSize: 10.5, fontWeight: 600, letterSpacing: '0.09em', color: 'var(--kraft)' }}>
                    NEW CV · 1-PAGE ATS BUILD
                  </span>
                </div>
                <h2 style={{ fontFamily: 'var(--font-voice)', fontSize: 23, fontWeight: 540, color: 'var(--chalk)', margin: 0, letterSpacing: '-0.02em' }}>
                  Drop a CV or target job to start
                </h2>
              </div>

              <div style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className="t-mono" style={{ fontSize: 10.5, color: 'rgba(229, 224, 218, 0.56)' }}>
                  Master Profile → .tex + PDF
                </span>
                <button
                  type="button"
                  className={`t-atelier-pair-btn ${blankPersonaMenuOpen ? 't-atelier-pair-btn--open' : ''}`}
                  style={{ fontSize: 12, padding: '5px 10px' }}
                  onClick={() => setBlankPersonaMenuOpen((v) => !v)}
                  title="Choose which Master Profile persona to tailor from"
                >
                  <span style={{ color: 'var(--kraft)' }}>Using:</span>
                  <span>{activePersona?.target_title || 'Primary Persona'}</span>
                  <TailoredIcon name="chevronDown" size={11} color="var(--chalk)" />
                </button>

                {blankPersonaMenuOpen && (
                  <div className="t-popover" style={{ top: 'calc(100% + 6px)', right: 0, width: 260, zIndex: 45 }}>
                    <div className="t-atelier-popover-label">Starting Persona (0 cr)</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {profile.career_personas.map((p) => (
                        <button
                          key={p.persona_id}
                          type="button"
                          className={`t-atelier-menu-row ${p.persona_id === activePersona?.persona_id ? 't-atelier-menu-row--active' : ''}`}
                          onClick={() => {
                            setActivePersonaId(p.persona_id);
                            setBlankPersonaMenuOpen(false);
                          }}
                        >
                          <span>{p.target_title}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div
              className={`t-cl-drop-well ${cvDraggingOver ? 't-cl-drop-well--dragging' : ''}`}
              onDragOver={(e) => {
                e.preventDefault();
                setCvDraggingOver(true);
              }}
              onDragLeave={() => setCvDraggingOver(false)}
              onDrop={(e) => void handleCvDropZoneDrop(e)}
            >
              <div className="t-cl-drop-input-wrap">
                <TypewriterDropPlaceholder
                  items={CV_DROP_PROMPTS}
                  visible={!cvDropInput && !cvAttachedFile}
                />
                <textarea
                  ref={cvDropTextareaRef}
                  id="cv-blank-drop-input"
                  aria-label="Drop a PDF or .tex resume, job link, job description, or screenshot"
                  rows={6}
                  className="t-cl-drop-textarea"
                  placeholder=""
                  value={cvDropInput}
                  onChange={(e) => setCvDropInput(e.target.value)}
                  onPaste={handleCvDropZonePaste}
                  onKeyDown={(e) => {
                    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                      e.preventDefault();
                      void handleCreateNewCvFromDrop();
                    }
                  }}
                />
              </div>

              {cvAttachedFile && (
                <div className="t-cl-drop-thumb">
                  {cvAttachedFile.previewUrl ? (
                    <img src={cvAttachedFile.previewUrl} alt="Attached job screenshot" />
                  ) : (
                    <TailoredIcon name="cv" size={18} color="var(--kraft)" />
                  )}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <span style={{ fontWeight: 600 }}>{cvAttachedFile.name}</span>
                    <span className="t-mono" style={{ fontSize: 10.5, color: 'var(--kraft)' }}>
                      {cvAttachedFile.kind === 'tex'
                        ? 'LaTeX .tex ready to import'
                        : cvAttachedFile.kind === 'pdf'
                          ? 'PDF resume ready to import'
                          : 'Job screenshot ready (OCR)'}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="t-atelier-icon-btn"
                    style={{ width: 24, height: 24, color: 'var(--chalk)' }}
                    aria-label="Remove attached file"
                    onClick={() => {
                      if (cvAttachedFile.previewUrl) URL.revokeObjectURL(cvAttachedFile.previewUrl);
                      setCvAttachedFile(null);
                    }}
                  >
                    <TailoredIcon name="close" size={12} color="var(--chalk)" />
                  </button>
                </div>
              )}

              <input
                ref={cvFileInputRef}
                type="file"
                accept=".pdf,.tex,image/*,.txt,.md"
                style={{ display: 'none' }}
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (file) await attachCvDropFile(file);
                  e.target.value = '';
                }}
              />

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', paddingTop: 6, borderTop: '1px solid rgba(229, 224, 218, 0.08)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    className="t-cl-drop-iconbtn"
                    onClick={() => cvFileInputRef.current?.click()}
                  >
                    <TailoredIcon name="upload" size={13} color="var(--chalk)" />
                    <span>Attach PDF / .tex / Image</span>
                  </button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <button
                    type="button"
                    className="t-atelier-topbar-ghost"
                    style={{ fontSize: 12.5 }}
                    title="Create an editable LaTeX CV pre-filled from your Master Profile (0 cr)"
                    onClick={handleCreateBlankLatexCv}
                  >
                    <span>Start from Master Profile</span>
                  </button>
                  <button
                    type="button"
                    className="t-atelier-btn-primary"
                    disabled={isCreatingCv || (!cvDropInput.trim() && !cvAttachedFile)}
                    onClick={() => void handleCreateNewCvFromDrop()}
                  >
                    <TailoredIcon name="scissors" size={13} color="var(--ink)" />
                    <span>
                      {isCreatingCv
                        ? 'Processing...'
                        : cvAttachedFile?.kind === 'tex' || cvAttachedFile?.kind === 'pdf'
                          ? 'Import into Studio'
                          : 'Create Tailored CV'}
                    </span>
                  </button>
                </div>
              </div>
            </div>

            <SavedRoleDropdown
              jobs={[...interestList, ...radarJobs]}
              profile={profile}
              onSelectRole={handleCreateCvFromSavedRole}
            />
          </div>
        </div>
      ) : viewMode === 'tex' ? (
        <div className="t-tex-split-wrap">
          <ResizableSplitPane
            storageKey="cv_studio_tex_split"
            defaultLeftPct={48}
            minLeftPx={360}
            minRightPx={400}
            left={
              <div className="t-tex-editor-card">
                <div className="t-tex-editor-head">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span className="t-mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--kraft)' }}>
                      tailored_cv.tex
                    </span>
                    {parsedLiveCv.warnings.length > 0 ? (
                      <span
                        className="t-mono"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 5,
                          fontSize: 11,
                          color: 'var(--thread)',
                          background: 'rgba(233, 69, 63, 0.14)',
                          padding: '2px 8px',
                          borderRadius: '3px 8px 3px 3px',
                        }}
                      >
                        <span className="t-signal-down" aria-hidden="true" />
                        <span>{parsedLiveCv.warnings.length} syntax issue</span>
                      </span>
                    ) : (
                      <span
                        className="t-mono"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 5,
                          fontSize: 11,
                          color: 'var(--green)',
                          background: 'rgba(30, 138, 90, 0.15)',
                          padding: '2px 8px',
                          borderRadius: '3px 8px 3px 3px',
                        }}
                      >
                        <span className="t-signal-up" aria-hidden="true" />
                        <span>{texSyncPulse ? 'Syncing Preview...' : 'Live Synced'}</span>
                      </span>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    {latexAudit.changedCount > 0 && (
                      <button
                        type="button"
                        className="t-atelier-pair-btn"
                        style={{ padding: '4px 10px', fontSize: 11.5 }}
                        onClick={() => switchStudioViewMode('diff')}
                      >
                        <span className="t-signal-up" aria-hidden="true" />
                        <span>Audit Diff ({latexAudit.changedCount})</span>
                      </button>
                    )}
                    <button
                      type="button"
                      className="t-atelier-pair-btn"
                      style={{ padding: '4px 10px', fontSize: 11.5 }}
                      onClick={() => {
                        pushNewVersion(
                          'LaTeX Edit',
                          parsedLiveCv.summary,
                          parsedLiveCv.flatBullets,
                          activeLatex
                        );
                        pushToast(`Saved version v${versions.length + 1} snapshot.`, { variant: 'success' });
                      }}
                    >
                      Save v{versions.length + 1}
                    </button>
                    {latexOverrides[docKey] && (
                      <button
                        type="button"
                        className="t-atelier-topbar-ghost"
                        style={{ padding: '4px 8px', fontSize: 11.5 }}
                        onClick={() => {
                          setLatexOverrides((prev) => {
                            const copy = { ...prev };
                            delete copy[docKey];
                            return copy;
                          });
                          setJobOverrides((prev) => {
                            const copy = { ...prev };
                            delete copy[docKey];
                            return copy;
                          });
                          pushToast('Reset LaTeX source to baseline.');
                        }}
                      >
                        Reset
                      </button>
                    )}
                    <button
                      type="button"
                      className="t-atelier-pair-btn"
                      style={{ padding: '4px 10px', fontSize: 11.5 }}
                      onClick={() => {
                        navigator.clipboard?.writeText(activeLatex);
                        pushToast('Copied .tex source to clipboard.');
                      }}
                    >
                      Copy .tex
                    </button>
                  </div>
                </div>

                <div className="t-tex-editor-body">
                  <div ref={texGutterRef} className="t-tex-gutter" aria-hidden="true">
                    {latexLines.map((_, i) => {
                      const lineNo = i + 1;
                      const isWarn = warningLinesSet.has(lineNo);
                      const isChanged = latexAudit.modifiedLineNumbers.has(lineNo);
                      return (
                        <div
                          key={lineNo}
                          className={`t-tex-gutter-line ${isWarn
                            ? 't-tex-gutter-line--warn'
                            : isChanged
                              ? 't-tex-gutter-line--changed'
                              : ''
                            }`}
                        >
                          {lineNo}
                        </div>
                      );
                    })}
                  </div>
                  <textarea
                    ref={texEditorRef}
                    id="cv-latex-editor"
                    aria-label="Editable XeLaTeX resume source"
                    spellCheck={false}
                    className="t-tex-textarea"
                    value={activeLatex}
                    onChange={(e) => {
                      handleLatexChange(e.target.value);
                      syncTexCursor(e.currentTarget);
                    }}
                    onKeyDown={handleTexKeyDown}
                    onClick={(e) => syncTexCursor(e.currentTarget)}
                    onKeyUp={(e) => syncTexCursor(e.currentTarget)}
                    onScroll={(e) => {
                      if (texGutterRef.current) {
                        texGutterRef.current.scrollTop = e.currentTarget.scrollTop;
                      }
                    }}
                  />
                </div>

                <div className="t-tex-editor-foot">
                  <span>
                    Ln {texCursorPos.line}, Col {texCursorPos.col} · {latexLines.length} lines
                  </span>
                  <span style={{ color: parsedLiveCv.warnings[0] ? 'var(--thread)' : 'var(--kraft)' }}>
                    {parsedLiveCv.warnings[0]
                      ? `Line ${parsedLiveCv.warnings[0].line}: ${parsedLiveCv.warnings[0].message}`
                      : 'Overleaf live preview synced on keystroke'}
                  </span>
                </div>
              </div>
            }
            right={
              <div className="t-tex-preview-scroll">
                {renderCvPaperSheet({ interactive: false, data: parsedLiveCv, compactPreview: true })}
              </div>
            }
          />
        </div>
      ) : (
        <div className="t-atelier-desk-scroll">
          {viewMode === 'diff' && (
            <div className="t-atelier-sheet" style={{ padding: '26px 34px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
                <div>
                  <span className="t-eyebrow">Semantic &amp; LaTeX Audit vs Base</span>
                  <h2 style={{ fontSize: 21, marginTop: 4 }}>Tracked Tailoring Deltas</h2>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <button type="button" className="t-atelier-btn-tonal" onClick={() => switchStudioViewMode('tex')}>
                    Edit in .tex Split
                  </button>
                  <button type="button" className="t-atelier-btn-tonal" onClick={() => switchStudioViewMode('paper')}>
                    Return to Paper
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {summaryText !== initialSummary && (
                  <div
                    style={{
                      border: 'none',
                      borderRadius: '4px 14px 4px 4px',
                      padding: 14,
                      background: 'white',
                      boxShadow: '0 6px 18px -8px rgba(26, 20, 18, 0.10)',
                    }}
                  >
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--n500)', marginBottom: 6 }}>
                      Professional Summary
                    </div>
                    <div className="t-diff-old" style={{ marginBottom: 6 }}>
                      <span className="t-signal-down" style={{ marginTop: 6 }} aria-hidden="true" />
                      <span style={{ textDecoration: 'line-through' }}>{initialSummary}</span>
                    </div>
                    <div className="t-diff-new">
                      <span className="t-signal-up" style={{ marginTop: 6 }} aria-hidden="true" />
                      <span>{summaryText}</span>
                    </div>
                  </div>
                )}

                {bullets.map((b, idx) => {
                  const base =
                    activeStudioDoc?.bullet_diffs?.[idx]?.original_bullet ||
                    exps[idx]?.achievements[0] ||
                    initialBullets[idx] ||
                    b;
                  return (
                    <div
                      key={idx}
                      style={{
                        border: 'none',
                        borderRadius: '4px 14px 4px 4px',
                        padding: 14,
                        background: 'white',
                        boxShadow: '0 6px 18px -8px rgba(26, 20, 18, 0.10)',
                      }}
                    >
                      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--n500)', marginBottom: 6 }}>
                        Experience Bullet {idx + 1}
                      </div>
                      <div className="t-diff-old" style={{ marginBottom: 6 }}>
                        <span className="t-signal-down" style={{ marginTop: 6 }} aria-hidden="true" />
                        <span style={{ textDecoration: 'line-through' }}>{base}</span>
                      </div>
                      <div className="t-diff-new">
                        <span className="t-signal-up" style={{ marginTop: 6 }} aria-hidden="true" />
                        <span>{b}</span>
                      </div>
                    </div>
                  );
                })}

                {latexAudit.changedCount > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <div className="t-mono" style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '0.1em', color: 'var(--n500)', marginBottom: 8 }}>
                      .TEX SOURCE LINE AUDIT ({latexAudit.changedCount} LINE{latexAudit.changedCount === 1 ? '' : 'S'} CHANGED)
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {latexAudit.diffs.slice(0, 12).map((d) => (
                        <div
                          key={`${d.lineNumber}_${d.kind}`}
                          style={{
                            borderRadius: '4px 14px 4px 4px',
                            padding: 12,
                            background: 'white',
                            boxShadow: '0 6px 18px -8px rgba(26, 20, 18, 0.10)',
                          }}
                        >
                          <div className="t-mono" style={{ fontSize: 11, fontWeight: 600, color: 'var(--n500)', marginBottom: 5 }}>
                            Line {d.lineNumber} · {d.kind}
                          </div>
                          {d.oldLine !== undefined && (
                            <div className="t-diff-old t-mono" style={{ fontSize: 12, marginBottom: d.newLine !== undefined ? 5 : 0 }}>
                              <span className="t-signal-down" style={{ marginTop: 5 }} aria-hidden="true" />
                              <span>{d.oldLine || '(blank line)'}</span>
                            </div>
                          )}
                          {d.newLine !== undefined && (
                            <div className="t-diff-new t-mono" style={{ fontSize: 12 }}>
                              <span className="t-signal-up" style={{ marginTop: 5 }} aria-hidden="true" />
                              <span>{d.newLine || '(blank line)'}</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {viewMode === 'paper' &&
            renderCvPaperSheet({
              interactive: activeStudioDoc?.generation_mode !== 'imported_tex',
              data: parsedLiveCv,
            })}
        </div>
      )}

      {/* Subtle Floating Bottom Status Pill (Zero Document Height Added) */}
      {!isBlankCvMode && (
        <div className="t-atelier-status-pill">
          <button
            type="button"
            className="t-atelier-zoom-btn"
            aria-label="Previous version"
            disabled={versionIdx <= 0}
            onClick={() => restoreVersion(versionIdx - 1)}
          >
            ‹
          </button>
          <span>v{versions[versionIdx]?.version || 1}</span>
          <button
            type="button"
            className="t-atelier-zoom-btn"
            aria-label="Next version"
            disabled={versionIdx >= versions.length - 1}
            onClick={() => restoreVersion(versionIdx + 1)}
          >
            ›
          </button>
          <span style={{ opacity: 0.35 }}>|</span>
          <span>Page 1/1</span>
          <span style={{ opacity: 0.35 }}>|</span>
          <button
            type="button"
            className="t-atelier-zoom-btn"
            aria-label="Zoom out"
            onClick={() => setZoomPct((z) => Math.max(80, z - 5))}
          >
            -
          </button>
          <span>{zoomPct}%</span>
          <button
            type="button"
            className="t-atelier-zoom-btn"
            aria-label="Zoom in"
            onClick={() => setZoomPct((z) => Math.min(115, z + 5))}
          >
            +
          </button>
        </div>
      )}

      {coachCollapsed && (
        <div className="t-atelier-coach-reopen">
          <button
            type="button"
            className="t-atelier-export-btn"
            onClick={() => setCoachCollapsed(false)}
          >
            <TailoredIcon name="chat" size={14} color="var(--ink)" />
            <span>Open Coach</span>
          </button>
        </div>
      )}
    </div>
  );

  const coachPane = (
    <div className={`t-atelier-coach-float-wrap ${swapSides ? 't-atelier-coach-float-wrap--left' : ''}`}>
      <CalmAiCoachSidecar
        variant="atelier"
        title="Atelier Coach"
        groundedContextLabel={
          isBlankCvMode ? 'New CV' : threadScope === 'workspace' ? 'All Workspace' : targetCompany
        }
        threadScope={threadScope}
        onChangeThreadScope={setThreadScope}
        enableWorkspaceMentions
        messages={messages}
        isStreaming={isStreaming}
        focusedAnchor={focusedAnchor}
        onClearFocusedAnchor={() => setFocusedAnchor(null)}
        onSendMessage={handleSendCoachMessage}
        onStopStreaming={() => setIsStreaming(false)}
        onApplyProposal={handleApplyProposal}
        onSkipProposal={handleSkipProposal}
        onUndoProposal={handleUndoProposal}
        onRefineProposal={handleRefineProposal}
        onHoverProposal={setHighlightedAnchor}
        onLocateAnchor={(id) => {
          switchStudioViewMode('paper');
          setHighlightedAnchor(id);
          setTimeout(() => {
            anchorRefs.current[id]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }, 40);
          setTimeout(() => setHighlightedAnchor(null), 1600);
        }}
        onPreviewResource={handlePreviewResource}
        onSelectResource={handleSelectResource}
        onConfirmAction={handleConfirmAction}
        onCancelAction={(actionId) =>
          setMessagesForJob((prev) =>
            prev.map((m) =>
              m.actionCard?.id === actionId
                ? { ...m, actionCard: { ...m.actionCard, status: 'cancelled' } }
                : m
            )
          )
        }
        onAuditAction={handleAuditAction}
        onSwapSide={() => setSwapSides((s) => !s)}
        onCollapse={() => setCoachCollapsed(true)}
        onNewThread={() =>
          resetCoachThread(threadKey, [
            {
              id: `m_reset_${Date.now()}`,
              role: 'assistant',
              text: `Clean thread ready for ${targetCompany}. Click any bullet, ask about @Saved CVs, or check @Pipeline.`,
            },
          ])
        }
        starterPrompts={[
          'Quantify Bullet 1',
          'Show my available CVs',
          'Check pipeline follow-ups',
        ]}
        mode={coachMode}
        onChangeMode={setCoachMode}
      />
    </div>
  );

  const cvLibraryPanel = (
    <aside
      className={`t-cl-history-rail ${!cvLibraryOpen ? 't-cl-history-rail--collapsed' : ''}`}
      aria-label="Saved CVs"
    >
      <div className="t-cl-history-head">
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: cvLibraryOpen ? 'space-between' : 'center',
            gap: 8,
          }}
        >
          {cvLibraryOpen && (
            <span
              style={{
                fontFamily: 'var(--font-voice)',
                fontSize: 16,
                fontWeight: 540,
                color: 'var(--chalk)',
                letterSpacing: '-0.02em',
                whiteSpace: 'nowrap',
              }}
            >
              Saved CVs
            </span>
          )}
          <button
            type="button"
            className="t-atelier-icon-btn"
            style={{ width: 26, height: 26, color: 'rgba(229, 224, 218, 0.78)' }}
            title={cvLibraryOpen ? 'Collapse Saved CVs rail' : 'Expand Saved CVs rail'}
            aria-label={cvLibraryOpen ? 'Collapse Saved CVs rail' : 'Expand Saved CVs rail'}
            aria-expanded={cvLibraryOpen}
            onClick={() => setCvLibraryOpen((v) => !v)}
          >
            <TailoredIcon name={cvLibraryOpen ? 'collapse' : 'expand'} size={14} color="var(--chalk)" />
          </button>
        </div>

        {cvLibraryOpen ? (
          <button
            type="button"
            className="t-atelier-btn-primary"
            style={{ width: '100%', justifyContent: 'center', padding: '8px 12px', whiteSpace: 'nowrap' }}
            onClick={openNewBlankCv}
          >
            <TailoredIcon name="plus" size={13} color="var(--ink)" />
            <span>New CV</span>
          </button>
        ) : (
          <button
            type="button"
            className="t-cl-history-mini-btn"
            title="New CV"
            aria-label="New CV"
            onClick={openNewBlankCv}
          >
            <TailoredIcon name="plus" size={14} color="var(--ink)" />
          </button>
        )}
      </div>

      {cvLibraryOpen ? (
        <>
          <div className="t-cl-history-sub">SAVED CVS · {tailoredDocs.length}</div>

          <div ref={cvListRef} className="t-cl-history-list">
            {isBlankCvMode && (
              <div className="t-cl-history-item t-cl-history-item--active">
                <div style={{ fontWeight: 600, fontSize: 12.5, color: 'var(--kraft)' }}>
                  Untitled New CV
                </div>
                <div style={{ fontSize: 11.5, color: 'rgba(229, 224, 218, 0.65)' }}>
                  Drop CV or job target…
                </div>
              </div>
            )}

            {tailoredDocs.map((doc) => {
              const isCurrent = !isBlankCvMode && activeStudioDoc?.doc_id === doc.doc_id;
              const docCo = cleanCompanyName(doc.company_name || 'Saved CV');
              const docRole = cleanTargetJobTitle(doc.job_title || 'Tailored CV');
              const fitPct = Math.round(doc.fit_score ?? 90);
              const isSent = doc.job_id !== undefined && dispatchedJobIds.has(doc.job_id);
              const statusLabel = isSent
                ? 'Dispatched'
                : doc.doc_id.startsWith('local-tex-')
                  ? '.tex Import'
                  : doc.doc_id.startsWith('local-pdf-')
                    ? 'PDF Import'
                    : formatShortCvDate(doc.updated_at || doc.created_at);

              return (
                <div
                  key={doc.doc_id}
                  role="button"
                  tabIndex={0}
                  className={`t-cl-history-item ${isCurrent ? 't-cl-history-item--active' : ''}`}
                  onClick={() => openLibraryCv(doc.doc_id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      openLibraryCv(doc.doc_id);
                    }
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
                    <span
                      style={{
                        fontWeight: 600,
                        fontSize: 12.5,
                        color: 'var(--chalk)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {docCo}
                    </span>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 2, flexShrink: 0 }}>
                      {isSent && (
                        <button
                          type="button"
                          className="t-cl-history-del"
                          title="Fork editable copy (0 cr)"
                          aria-label={`Fork ${docCo} CV`}
                          onClick={(e) => {
                            e.stopPropagation();
                            setIsBlankCvMode(false);
                            void forkSavedDoc(doc.doc_id);
                          }}
                        >
                          <TailoredIcon name="copy" size={11} />
                        </button>
                      )}
                      <button
                        type="button"
                        className="t-cl-history-del"
                        title="Delete saved CV"
                        aria-label={`Delete ${docCo} CV`}
                        onClick={(e) => {
                          e.stopPropagation();
                          const remaining = tailoredDocs.filter((x) => x.doc_id !== doc.doc_id);
                          deleteStudioDoc(doc.doc_id);
                          if (isCurrent) {
                            if (remaining[0]) {
                              openLibraryCv(remaining[0].doc_id);
                            } else {
                              openNewBlankCv();
                            }
                          }
                        }}
                      >
                        <TailoredIcon name="trash" size={11} />
                      </button>
                    </div>
                  </div>
                  <div
                    style={{
                      fontSize: 11.5,
                      color: 'rgba(229, 224, 218, 0.72)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {docRole}
                  </div>
                  <div
                    className="t-mono"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: 6,
                      fontSize: 10.2,
                      color: 'rgba(229, 224, 218, 0.5)',
                      marginTop: 2,
                    }}
                  >
                    <span style={{ color: fitPct >= 75 ? 'var(--green)' : 'var(--kraft)', fontWeight: 600 }}>
                      {fitPct}% Fit
                    </span>
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: isSent ? 'var(--thread)' : 'var(--kraft)' }}>
                      {statusLabel}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <div
          className="t-cl-history-collapsed-body"
          onClick={() => setCvLibraryOpen(true)}
          title="Expand Saved CVs rail"
        >
          <span className="t-cl-history-collapsed-count">{tailoredDocs.length}</span>
          <span className="t-cl-history-collapsed-label">Saved CVs</span>
        </div>
      )}
    </aside>
  );

  return (
    <div className="t-studio-shell t-cv-studio-v2">
      {/* FOCUSED FLOATING TOP BAR */}
      <header ref={headerRef} className="t-studio-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0, position: 'relative' }}>
          <button
            type="button"
            className="t-atelier-topbar-ghost"
            style={{ paddingLeft: 6 }}
            onClick={goBack}
          >
            <TailoredIcon name="back" size={14} color="var(--chalk)" />
            <span>Back</span>
          </button>

          <button
            type="button"
            className={`t-atelier-pair-btn ${identityMenuOpen ? 't-atelier-pair-btn--open' : ''}`}
            onClick={() => {
              setIdentityMenuOpen((v) => !v);
              setJobMenuOpen(false);
              setCustomizeOpen(false);
              setExportOpen(false);
            }}
          >
            <span>{activePersona?.target_title.split(' ')[0] || 'Persona'}</span>
            <span className="t-mono" style={{ fontSize: 11.5, color: 'var(--kraft)' }}>{activeRegionalPhone}</span>
            <TailoredIcon name="chevronDown" size={12} color="var(--chalk)" />
          </button>

          <span style={{ color: 'var(--n500)', fontSize: 13 }}>/</span>

          {isBlankCvMode ? (
            <span
              style={{
                fontSize: 13,
                fontWeight: 500,
                color: 'var(--kraft)',
                maxWidth: 'clamp(120px, 16vw, 220px)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              New Blank CV
            </span>
          ) : (
            <button
              type="button"
              className={`t-atelier-pair-btn ${jobMenuOpen ? 't-atelier-pair-btn--open' : ''}`}
              onClick={() => {
                setJobMenuOpen((v) => !v);
                setIdentityMenuOpen(false);
                setCustomizeOpen(false);
                setExportOpen(false);
              }}
            >
              <span style={{ maxWidth: 'clamp(100px, 10vw, 155px)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {targetCompany} · {targetRole}
              </span>
              <TailoredIcon name="chevronDown" size={12} color="var(--chalk)" />
            </button>
          )}

          {identityMenuOpen && (
            <div className="t-popover" style={{ top: 44, left: 68, width: 310 }}>
              <div className="t-atelier-popover-label">Switch Career Persona (0 cr)</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 14 }}>
                {profile.career_personas.map((p) => (
                  <button
                    key={p.persona_id}
                    type="button"
                    className={`t-atelier-menu-row ${p.persona_id === activePersona?.persona_id ? 't-atelier-menu-row--active' : ''
                      }`}
                    onClick={() => {
                      setActivePersonaId(p.persona_id);
                      setIdentityMenuOpen(false);
                    }}
                  >
                    <span>{p.target_title}</span>
                  </button>
                ))}
              </div>
              <div className="t-atelier-popover-label">Dual-SIM Regional Header Phone</div>
              <div style={{ display: 'flex', gap: 6 }}>
                {(['+20', '+966', '+971'] as const).map((code) => (
                  <button
                    key={code}
                    type="button"
                    className={`t-atelier-popover-chip ${activeRegionalPhone === code ? 't-atelier-popover-chip--active' : ''
                      }`}
                    onClick={() => setActiveRegionalPhone(code)}
                  >
                    <span className="t-mono" style={{ fontSize: 12 }}>{code}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {jobMenuOpen && (
            <div className="t-popover" style={{ top: 44, left: 210, width: 380 }}>
              <div className="t-atelier-popover-label">Switch Target Role</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 200, overflowY: 'auto', marginBottom: 14 }}>
                {allTargetOptions.map((j) => (
                  <button
                    key={j.id}
                    type="button"
                    className={`t-atelier-menu-row ${j.id === activeStudioJob.id ? 't-atelier-menu-row--active' : ''
                      }`}
                    onClick={() => {
                      setActiveStudioJob(j);
                      setJobMenuOpen(false);
                    }}
                  >
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {cleanCompanyName(j.company_name)} · {cleanTargetJobTitle(j.title)}
                    </span>
                    <span className="t-mono" style={{ fontSize: 11.5, opacity: 0.75, flexShrink: 0 }}>
                      {isJobUnlocked(j.id, 'cv') ? '0 cr' : '1 cr'}
                    </span>
                  </button>
                ))}
              </div>
              <div className="t-atelier-popover-label">Or Paste New JD / URL</div>
              <div style={{ display: 'flex', gap: 6 }}>
                <input
                  className="t-atelier-inline-input"
                  placeholder="Paste URL or JD text..."
                  value={quickJdPaste}
                  onChange={(e) => setQuickJdPaste(e.target.value)}
                />
                <button
                  type="button"
                  className="t-atelier-btn-primary"
                  disabled={!quickJdPaste.trim()}
                  onClick={async () => {
                    await ingestJobUrlOrText(quickJdPaste, { openInStudio: true });
                    setQuickJdPaste('');
                    setJobMenuOpen(false);
                  }}
                >
                  Load
                </button>
              </div>
              {fitEval.missingSkills.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div className="t-atelier-popover-label" style={{ marginBottom: 6 }}>
                    Missing Stack Tokens
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                    {fitEval.missingSkills.map((sk) => (
                      <span
                        key={sk}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 6,
                          padding: '4px 9px',
                          borderRadius: '4px 9px 4px 9px',
                          background: 'var(--paper)',
                          color: 'var(--n700)',
                          fontSize: 12,
                          fontWeight: 500,
                        }}
                      >
                        <span className="t-signal-down" aria-hidden="true" />
                        <span>{sk}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Center Mode Switcher (Paper | Diff | .tex Split Overleaf View) */}
        {!isBlankCvMode ? (
          <div className="t-atelier-seg t-atelier-seg--studio" role="tablist" aria-label="Studio document view">
            <span
              aria-hidden="true"
              className="t-atelier-seg-thumb"
              style={{
                transform: `translateX(${viewMode === 'paper' ? 0 : viewMode === 'diff' ? 100 : 200}%)`,
              }}
            />
            {(['paper', 'diff', 'tex'] as const).map((m) => (
              <button
                key={m}
                type="button"
                role="tab"
                aria-selected={viewMode === m}
                className={`t-atelier-seg-btn ${viewMode === m ? 't-atelier-seg-btn--active' : ''}`}
                onClick={() => switchStudioViewMode(m)}
              >
                {m === 'tex' ? '.tex Split' : m === 'diff' ? 'Diff' : 'Paper'}
              </button>
            ))}
          </div>
        ) : (
          <div />
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, position: 'relative' }}>
          {!isBlankCvMode && (
            <>
              <span className={`t-atelier-fit-pill ${fitPulse ? 't-atelier-fit-pill--pulse' : ''}`}>
                {fitEval.overallScore >= 75 ? (
                  <span className="t-signal-up" aria-hidden="true" />
                ) : fitEval.overallScore < 50 ? (
                  <span className="t-signal-down" aria-hidden="true" />
                ) : (
                  <span className="t-atelier-fit-dot" style={{ background: 'var(--amber)' }} />
                )}
                <span className="t-mono" style={{ fontSize: 12, fontWeight: 600 }}>
                  {Math.round(fitEval.overallScore)}%
                </span>
                <span>Fit</span>
              </span>

              <button
                type="button"
                className="t-atelier-pair-btn"
                title="Use the current CV in Cover Letters"
                onClick={() => {
                  setSelectedCvForJob(activeStudioJob.id, activeStudioDoc?.doc_id || 'base');
                  openJobInCoverLetters(activeStudioJob, { mode: 'pitch' });
                  pushToast('Opened Cover Letters with this CV paired.', { variant: 'success' });
                }}
              >
                <TailoredIcon name="coverLetter" size={13} color="var(--chalk)" />
                <span>Cover Letter</span>
              </button>

              <button
                type="button"
                className="t-atelier-topbar-ghost"
                onClick={() => {
                  setCustomizeOpen((v) => !v);
                  setExportOpen(false);
                  setIdentityMenuOpen(false);
                  setJobMenuOpen(false);
                }}
              >
                <TailoredIcon name="sliders" size={13} color="var(--chalk)" />
                <span>Customize</span>
              </button>

              <button
                type="button"
                className="t-atelier-export-btn"
                onClick={() => {
                  setExportOpen((v) => !v);
                  setCustomizeOpen(false);
                }}
              >
                <span>Export PDF</span>
                <TailoredIcon name="chevronDown" size={11} color="var(--ink)" />
              </button>
            </>
          )}

          {customizeOpen && !isBlankCvMode && (
            <div className="t-popover" style={{ top: 44, right: 112, width: 290 }}>
              <div className="t-atelier-popover-label">Paper Density</div>
              <div style={{ display: 'flex', gap: 6, marginBottom: 14 }}>
                {(['cozy', 'compact'] as const).map((d) => (
                  <button
                    key={d}
                    type="button"
                    className={`t-atelier-popover-chip ${paperDensity === d ? 't-atelier-popover-chip--active' : ''
                      }`}
                    onClick={() => setPaperDensity(d)}
                  >
                    {d === 'cozy' ? 'Cozy Paper' : 'Compact 1-Page'}
                  </button>
                ))}
              </div>
              <div className="t-atelier-popover-label">Tailor Intensity</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
                {(['Surgical', 'Metrics+', 'Executive'] as const).map((i) => (
                  <button
                    key={i}
                    type="button"
                    className={`t-atelier-popover-chip ${tailorIntensity === i ? 't-atelier-popover-chip--active' : ''
                      }`}
                    onClick={() => setTailorIntensity(i)}
                  >
                    {i}
                  </button>
                ))}
              </div>
              <button
                type="button"
                className="t-atelier-menu-row"
                style={{ background: 'var(--paper)' }}
                onClick={() => {
                  setCustomizeOpen(false);
                  if (activeStudioDoc) setSelectedCvForJob(activeStudioJob.id, activeStudioDoc.doc_id);
                  openJobInCoverLetters(activeStudioJob, { mode: 'pitch' });
                }}
              >
                <span>Open Matching Cover Letter</span>
                <span>→</span>
              </button>
            </div>
          )}

          {exportOpen && !isBlankCvMode && (
            <div className="t-popover" style={{ top: 44, right: 0, width: 256 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <button
                  type="button"
                  className="t-atelier-menu-row"
                  style={{ background: 'var(--ink)', color: 'var(--chalk)' }}
                  onClick={() => {
                    if (activeStudioDoc) CvFitAPI.downloadArtifact(activeStudioDoc, 'pdf');
                    setExportOpen(false);
                    pushToast('Compiled clean 1-page ATS PDF.');
                  }}
                >
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <TailoredIcon name="download" size={13} color="var(--chalk)" />
                    <span>Download ATS PDF</span>
                  </span>
                  <span className="t-mono" style={{ fontSize: 11, opacity: 0.75 }}>0 cr</span>
                </button>
                <button
                  type="button"
                  className="t-atelier-menu-row"
                  style={{ background: 'var(--paper)' }}
                  onClick={() => {
                    if (latexOverrides[docKey] || isImportedCustomDoc || !activeStudioDoc) {
                      const blob = new Blob([activeLatex], { type: 'application/x-tex;charset=utf-8' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `${(profile.personal_info.full_name || 'tailored').replace(/\s+/g, '_')}_${targetCompany.replace(/\s+/g, '_')}.tex`;
                      a.click();
                      URL.revokeObjectURL(url);
                    } else {
                      CvFitAPI.downloadArtifact(activeStudioDoc, 'tex');
                    }
                    setExportOpen(false);
                    pushToast('Downloaded .tex source.');
                  }}
                >
                  <span>Download .tex Source</span>
                </button>
                <button
                  type="button"
                  className="t-atelier-menu-row"
                  style={{ background: 'var(--paper)' }}
                  onClick={() => {
                    addToPipeline(activeStudioJob, 'applied', activeStudioJob.recruiter_email || null, {
                      tailoredCvDocId: activeStudioDoc?.doc_id || null,
                      silent: true,
                    });
                    setExportOpen(false);
                    pushToast(`Marked ${targetCompany} as Applied in Pipeline.`, { variant: 'success' });
                  }}
                >
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <span className="t-signal-up" aria-hidden="true" />
                    <span>Mark Applied in Pipeline</span>
                  </span>
                </button>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* ATELIER WORKSPACE STAGE WITH FRENCH-CURVE BACKDROP + SAVED CVS RAIL */}
      <div className="t-atelier-stage" style={{ flexDirection: 'row' }}>
        <AtelierFrenchCurveBackdrop />
        {cvLibraryPanel}
        <div style={{ position: 'relative', zIndex: 1, flex: 1, minWidth: 0, minHeight: 0, display: 'flex' }}>
          {coachCollapsed ? (
            <div style={{ position: 'relative', zIndex: 1, flex: 1, minHeight: 0, overflow: 'hidden', display: 'flex' }}>
              {paperPane}
            </div>
          ) : (
            <ResizableSplitPane
              storageKey={swapSides ? 'cv_studio_v2_swapped' : 'cv_studio_v2_main'}
              defaultLeftPct={swapSides ? 36 : 64}
              minLeftPx={swapSides ? 336 : 420}
              minRightPx={swapSides ? 420 : 336}
              left={swapSides ? coachPane : paperPane}
              right={swapSides ? paperPane : coachPane}
            />
          )}
        </div>
      </div>
    </div>
  );
};
