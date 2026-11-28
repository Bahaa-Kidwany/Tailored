import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { ResizableSplitPane } from '../components/common/ResizableSplitPane';
import { TailoredIcon } from '../brand/TailoredIcons';
import { AtelierFrenchCurveBackdrop } from '../brand/BrandElements';
import {
  AtelierPreviewDrawer,
  type AtelierPreviewData,
} from '../components/studio/AtelierPreviewDrawer';
import { buildParsedCvSnapshot } from '../utils/cvSnapshotBuilder';
import { SavedRoleDropdown } from '../components/common/SavedRoleDropdown';
import {
  TypewriterDropPlaceholder,
  type TypewriterPromptItem,
} from '../components/common/TypewriterDropPlaceholder';
import {
  CalmAiCoachSidecar,
  type AiChatMessage,
  type AiResourceItem,
  type AiAuditItem,
} from '../components/common/CalmAiCoachSidecar';
import { SAMPLE_PROFILE } from '../services/profileApi';
import { cleanCompanyName, cleanTargetJobTitle, CvFitAPI } from '../services/cvFitApi';
import { CoverLetterAPI, type CoverLetterItem } from '../services/coverLetterApi';
import { extractEmail, resolveServerJobId, type JobItem } from '../services/jobsApi';
import { AgentAPI } from '../services/agentApi';
import { getAccessToken } from '../services/apiClient';
import { evaluateAllPersonas } from '../utils/fitEngine';
import { buildWorkspaceCoachReply } from '../utils/workspaceCoachEngine';
import {
  composeTailoredOutreachDraft,
  parseCoverLetterDropInput,
} from '../utils/coverLetterTargetParser';

type CoverLetterTone = 'Executive' | 'Technical' | 'Impact-Driven' | 'Founder-Direct';

const COVER_LETTER_DROP_PROMPTS: TypewriterPromptItem[] = [
  { icon: 'link', text: 'Paste a job link...' },
  { icon: 'cv', text: 'Paste a full job description...' },
  { icon: 'image', text: 'Drop or Ctrl+V a job post screenshot...' },
  { icon: 'coverLetter', text: 'Describe a role & recruiter email...' },
];

function buildCoverLetterRewrite(
  original: string,
  mode: string,
  tone: CoverLetterTone,
  company: string,
  role: string,
  skills: string[]
): string {
  const clean = original.trim();
  if (!clean) return '';
  const leadStack = skills.slice(0, 3).join(', ') || 'Python, FastAPI, Docker';

  if (mode === 'Condense') {
    const firstSentence = clean.split('.')[0]?.trim();
    if (firstSentence && firstSentence.length + 12 < clean.length) {
      return `${firstSentence}. Ready to contribute measurable impact from day one at ${company}.`;
    }
    return clean.replace(/\s+/g, ' ').replace(/\bstrong interest in\b/i, 'focus on');
  }

  if (mode === 'Hook Swap') {
    return `Shipping production ${leadStack} architectures maps directly to ${company}'s ${role} priorities—I bring verified end-to-end delivery ready for immediate impact.`;
  }

  if (mode === 'Check Claim') {
    if (clean.includes('Master Profile')) return clean;
    return `${clean.replace(/\.$/, '')}—backed by verified production delivery in my Master Profile.`;
  }

  if (/^I am writing to express|^Having architected/i.test(clean)) {
    return tone === 'Founder-Direct'
      ? `Your ${role} roadmap at ${company} maps directly to the production ${leadStack} systems I have built and shipped.`
      : tone === 'Executive'
        ? `I bring hands-on technical leadership across ${leadStack} systems aligned directly with ${company}'s ${role} charter.`
        : `Building low-latency ${leadStack} services aligns directly with ${company}'s ${role} priorities, and I can contribute from week one.`;
  }
  if (/^In my recent work/i.test(clean)) {
    return clean.replace(/^In my recent work at\b/i, 'Most recently at');
  }
  return `${clean.replace(/\.$/, '')}—refined for ${tone.toLowerCase()} clarity.`;
}

function buildQuickRoleCoverLetterRecord(params: {
  job: JobItem;
  fullName: string;
  phoneDisplay: string;
  primaryCompany: string;
}): { doc: CoverLetterItem; paragraphs: string[] } {
  const cleanCo = cleanCompanyName(params.job.company_name);
  const cleanRole = cleanTargetJobTitle(params.job.title);
  const paragraphs = [
    `Dear ${cleanCo} Hiring Team,`,
    `Having architected production services in ${params.job.parsed_skills.slice(0, 3).join(', ') || 'Python, FastAPI, Docker'
    }, I can contribute immediately to ${cleanCo}'s ${cleanRole} roadmap.`,
    `Most recently at ${params.primaryCompany}, I delivered end-to-end modeling and low-latency API orchestration with measurable reliability gains.`,
    `My tailored CV is attached for review—I'd welcome the chance to connect.`,
    `Best,\n${params.fullName} · ${params.phoneDisplay}`,
  ];
  const doc: CoverLetterItem = {
    doc_id: `cl_${Date.now()}`,
    job_id: params.job.id,
    company_name: cleanCo,
    job_title: cleanRole,
    recipient_email: params.job.recruiter_email || extractEmail(params.job.raw_description || '') || null,
    source_label: 'Saved Role',
    subject_line: `Application: ${cleanRole} (${cleanCo}) — ${params.fullName}`,
    body_markdown: paragraphs.join('\n\n'),
    created_at: new Date().toISOString(),
  };
  return { doc, paragraphs };
}

function buildBlankManualCoverLetterRecord(params: {
  fullName: string;
  phoneDisplay: string;
}): { doc: CoverLetterItem; paragraphs: string[] } {
  const stamp = Date.now();
  const paragraphs = [
    'Dear Hiring Team,',
    'I am writing to express my strong interest in joining your engineering team and contributing immediate production impact.',
    'My tailored CV is attached for reference—I look forward to connecting.',
    `Best,\n${params.fullName} · ${params.phoneDisplay}`,
  ];
  const doc: CoverLetterItem = {
    doc_id: `cl_manual_${stamp}`,
    job_id: null,
    company_name: 'Custom Recipient',
    job_title: 'Blank Outreach Draft',
    recipient_email: '',
    source_label: 'Blank Canvas',
    subject_line: `Application — ${params.fullName}`,
    body_markdown: paragraphs.join('\n\n'),
    created_at: new Date().toISOString(),
  };
  return { doc, paragraphs };
}

function formatShortHistoryDate(iso?: string): string {
  if (!iso) return 'Draft';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return 'Draft';
  const diffDays = Math.floor((Date.now() - d.getTime()) / 86400000);
  if (diffDays <= 0) return 'Today';
  if (diffDays === 1) return '1d ago';
  if (diffDays < 14) return `${diffDays}d ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export const CoverLetterStudioPage: React.FC = () => {
  const {
    goBack,
    currentSearch,
    currentProfile,
    activePersonaId,
    setActivePersonaId,
    activeRegionalPhone,
    setActiveRegionalPhone,
    activeStudioJob,
    setActiveStudioJob,
    activeStudioDoc,
    tailoredDocs,
    radarJobs,
    setRadarJobs,
    interestList,
    addToInterest,
    pipelineItems,
    ingestJobUrlOrText,
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
    addToPipeline,
    openJobInStudio,
    openDocInStudio,
    openJobInCoverLetters,
    requestCreditAction,
    isJobUnlocked,
    navigateTo,
    pushToast,
  } = useWorkspace();

  const profile = currentProfile?.profile || SAMPLE_PROFILE;
  const activePersona =
    profile.career_personas.find((p) => p.persona_id === activePersonaId) ||
    profile.career_personas[0];
  const fullName = profile.personal_info.full_name || 'Candidate';
  const myEmail = profile.personal_info.primary_email || '';

  const historyLetters = useMemo(() => {
    const seen = new Set<string>();
    return coverLetters.filter((c) => {
      if (seen.has(c.doc_id)) return false;
      seen.add(c.doc_id);
      return true;
    });
  }, [coverLetters]);

  const urlJobId = useMemo(() => {
    const raw = new URLSearchParams(currentSearch).get('job_id');
    return raw ? Number(raw) : null;
  }, [currentSearch]);

  const [historyOpen, setHistoryOpen] = useState(true);
  const [isBlankMode, setIsBlankMode] = useState(false);
  const [selectedLetterDocId, setSelectedLetterDocId] = useState<string | null>(null);

  const activeLetter = useMemo<CoverLetterItem | null>(() => {
    if (isBlankMode) return null;
    if (selectedLetterDocId) {
      const hit = historyLetters.find((c) => c.doc_id === selectedLetterDocId);
      if (hit) return hit;
    }
    if (urlJobId) {
      return historyLetters.find((c) => c.job_id === urlJobId) || null;
    }
    return historyLetters[0] || null;
  }, [isBlankMode, selectedLetterDocId, historyLetters, urlJobId]);

  const showBlankDropCanvas = isBlankMode || (!activeLetter && !urlJobId);

  const allTargetOptions = useMemo(() => {
    const seen = new Set<number>();
    return [activeStudioJob, ...interestList, ...radarJobs].filter((j) => {
      if (seen.has(j.id)) return false;
      seen.add(j.id);
      return true;
    });
  }, [activeStudioJob, interestList, radarJobs]);

  const displayJob = useMemo<JobItem>(() => {
    if (activeLetter?.job_id) {
      const matched =
        allTargetOptions.find((j) => j.id === activeLetter.job_id) ||
        pipelineItems.find((p) => p.job.id === activeLetter.job_id)?.job;
      if (matched) return matched;
    }
    if (activeLetter) {
      return {
        id: activeLetter.job_id || -1,
        source_id: activeLetter.doc_id,
        title: activeLetter.job_title || 'Tailored Outreach',
        company_name: activeLetter.company_name || 'Target Organization',
        location: 'MENA / Remote',
        url: '',
        raw_description: activeLetter.body_markdown,
        fit_score: 88,
        is_high_match: true,
        source_type: 'custom_drop',
        parsed_skills: ['Python', 'FastAPI', 'Docker', 'PostgreSQL'],
        responsibilities: [],
        location_type: 'Hybrid',
        created_at: activeLetter.created_at,
        recruiter_email: activeLetter.recipient_email || null,
      };
    }
    return activeStudioJob;
  }, [activeLetter, allTargetOptions, pipelineItems, activeStudioJob]);

  const company = cleanCompanyName(activeLetter?.company_name || displayJob.company_name);
  const role = cleanTargetJobTitle(activeLetter?.job_title || displayJob.title);
  const existingPipelineItem = pipelineItems.find((p) => p.job.id === displayJob.id);

  const fitEval = useMemo(
    () => evaluateAllPersonas(displayJob, profile).best,
    [displayJob, profile]
  );

  const phoneDisplay =
    activeRegionalPhone === '+20'
      ? '+20 100 482 9102'
      : activeRegionalPhone === '+966'
        ? '+966 54 391 8820'
        : '+971 50 987 6543';

  const detectedRecipientEmail =
    activeLetter?.recipient_email ||
    existingPipelineItem?.recruiter_email ||
    displayJob.recruiter_email ||
    extractEmail(displayJob.raw_description || '') ||
    '';

  const defaultParagraphs = useMemo(() => {
    if (coverLetterEntryMode === 'followup') {
      return [
        `Hi ${company} Hiring Team,`,
        `Following up briefly on my ${role} application and attached tailored CV sent earlier this week. I'd welcome a short technical chat to share recent ${displayJob.parsed_skills.slice(0, 2).join(' & ') || 'production architecture'
        } results from ${activePersona?.experience_highlights[0]?.company || 'Swvl'}.`,
        `Best,\n${fullName} · ${phoneDisplay}`,
      ];
    }
    const fallbackBody =
      `Dear ${company} Hiring Team,\n\nHaving architected production ML inference pipelines and backend APIs in ${displayJob.parsed_skills.slice(0, 3).join(', ') || 'Python, FastAPI, Docker'
      }, I can contribute immediately to ${company}'s ${role} roadmap.\n\nMost recently at ${activePersona?.experience_highlights[0]?.company || 'Swvl'
      }, I delivered end-to-end modeling and low-latency API orchestration with measurable throughput gains.\n\nMy tailored 1-page CV is attached for review—I'd welcome the chance to connect.\n\nBest,\n${fullName} · ${phoneDisplay}`;
    const raw = (activeLetter?.body_markdown || fallbackBody)
      .replace(/\r\n/g, '\n')
      .replace(/^(?:\s*Subject\s*:[^\n]*\n+)+/i, '')
      .replace(/\[(?:Candidate|Your)\s+Name\]/gi, fullName)
      .trim();
    const parts = raw
      .split(/\n{2,}/)
      .map((p) => p.trim())
      .filter(Boolean);
    return parts.length > 0 ? parts : fallbackBody.split('\n\n');
  }, [
    coverLetterEntryMode,
    activeLetter,
    company,
    role,
    displayJob.parsed_skills,
    activePersona,
    fullName,
    phoneDisplay,
  ]);

  const [tone, setTone] = useState<CoverLetterTone>('Technical');
  const [hookFocus, setHookFocus] = useState('Measured throughput & clean production engineering');
  const [lengthMode, setLengthMode] = useState<'compact' | 'balanced'>('balanced');
  const [viewMode, setViewMode] = useState<'clean' | 'keywords'>('clean');
  const [swapSides, setSwapSides] = useState(false);
  const [coachCollapsed, setCoachCollapsed] = useState(false);

  const [toOverrides, setToOverrides] = useState<Record<string, string>>({});
  const [ccSelf, setCcSelf] = useState(true);
  const [markAppliedOnSend, setMarkAppliedOnSend] = useState(true);
  const [subjectOverrides, setSubjectOverrides] = useState<Record<string, string>>({});
  const [paraOverrides, setParaOverrides] = useState<Record<string, string[]>>({});
  const [toWarnPulse, setToWarnPulse] = useState(false);

  // Big Blank Canvas Drop Zone state (only active when starting a new blank letter)
  const [dropInput, setDropInput] = useState('');
  const [blankToEmail, setBlankToEmail] = useState('');
  const [blankCvId, setBlankCvId] = useState<string>('auto');
  const [blankCvMenuOpen, setBlankCvMenuOpen] = useState(false);
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [attachedScreenshot, setAttachedScreenshot] = useState<{ name: string; previewUrl: string } | null>(null);
  const [isCreatingLetter, setIsCreatingLetter] = useState(false);

  const letterKey = activeLetter?.doc_id || `draft_${displayJob.id}`;
  const toEmail = toOverrides[letterKey] ?? detectedRecipientEmail;

  const subjectKey = `${letterKey}_${coverLetterEntryMode}`;
  const subjectLine =
    subjectOverrides[letterKey] ??
    (coverLetterEntryMode === 'followup'
      ? `Following up: ${role} — ${fullName}`
      : activeLetter?.subject_line ?? `Application: ${role} — ${fullName}`);

  const paragraphs = paraOverrides[letterKey] ?? defaultParagraphs;

  const persistActiveLetterPatch = (
    patch: Partial<Pick<CoverLetterItem, 'subject_line' | 'body_markdown' | 'recipient_email'>>
  ) => {
    if (!activeLetter) return;
    saveCoverLetter({
      ...activeLetter,
      ...patch,
    });
  };

  const setToForLetter = (nextTo: string) => {
    setToOverrides((prev) => ({ ...prev, [letterKey]: nextTo }));
    persistActiveLetterPatch({ recipient_email: nextTo });
  };

  const setSubjectLine = (s: string) => {
    setSubjectOverrides((prev) => ({ ...prev, [letterKey]: s }));
    persistActiveLetterPatch({ subject_line: s });
  };

  const setParagraphs = (updater: (curr: string[]) => string[]) => {
    const currentList = paraOverrides[letterKey] ?? defaultParagraphs;
    const updatedList = updater(currentList);
    setParaOverrides((prev) => ({
      ...prev,
      [letterKey]: updatedList,
    }));
    persistActiveLetterPatch({ body_markdown: updatedList.join('\n\n') });
  };

  // Menus & Drawers
  const [identityMenuOpen, setIdentityMenuOpen] = useState(false);
  const [briefPopoverOpen, setBriefPopoverOpen] = useState(false);
  const [attachMenuOpen, setAttachMenuOpen] = useState(false);
  const [sendMenuOpen, setSendMenuOpen] = useState(false);
  const [activePreview, setActivePreview] = useState<AtelierPreviewData | null>(null);

  const [editingIdx, setEditingIdx] = useState<number | null>(null);
  const [editBuffer, setEditBuffer] = useState('');
  const [focusedAnchor, setFocusedAnchor] = useState<{ id: string; label: string } | null>(null);
  const [highlightedAnchor, setHighlightedAnchor] = useState<string | null>(null);
  const [appliedAnchorId, setAppliedAnchorId] = useState<string | null>(null);
  const [fitPulse, setFitPulse] = useState(false);
  const [threadScope, setThreadScope] = useState<'role' | 'workspace'>('role');

  const headerRef = useRef<HTMLElement>(null);
  const attachWrapRef = useRef<HTMLDivElement>(null);
  const sendWrapRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const blankTextareaRef = useRef<HTMLTextAreaElement>(null);
  const historyListRef = useRef<HTMLDivElement>(null);
  const toInputRef = useRef<HTMLInputElement>(null);
  const previewReqIdRef = useRef(0);

  const scrollHistoryToTop = () => {
    window.requestAnimationFrame(() => {
      if (historyListRef.current) {
        historyListRef.current.scrollTop = 0;
      }
    });
  };
  const anchorRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const appliedTimerRef = useRef<number | null>(null);
  const pulseTimerRef = useRef<number | null>(null);
  const warnTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const onMouseDown = (e: MouseEvent) => {
      if (headerRef.current && !headerRef.current.contains(e.target as Node)) {
        setIdentityMenuOpen(false);
        setBriefPopoverOpen(false);
      }
      if (attachWrapRef.current && !attachWrapRef.current.contains(e.target as Node)) {
        setAttachMenuOpen(false);
      }
      if (sendWrapRef.current && !sendWrapRef.current.contains(e.target as Node)) {
        setSendMenuOpen(false);
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIdentityMenuOpen(false);
        setBriefPopoverOpen(false);
        setAttachMenuOpen(false);
        setSendMenuOpen(false);
        setActivePreview(null);
        setEditingIdx(null);
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
      if (warnTimerRef.current) window.clearTimeout(warnTimerRef.current);
    };
  }, []);

  const matchingJobCv = useMemo(
    () => tailoredDocs.find((d) => d.job_id === displayJob.id) || null,
    [tailoredDocs, displayJob.id]
  );
  const selectedCvId =
    selectedCvByJob[displayJob.id] ?? (matchingJobCv ? matchingJobCv.doc_id : 'base');
  const selectedTailoredDoc =
    selectedCvId !== 'base' && selectedCvId !== 'none'
      ? tailoredDocs.find((d) => d.doc_id === selectedCvId) || matchingJobCv
      : null;

  const attachedCvLabel =
    selectedCvId === 'none'
      ? 'No CV attached (text pitch only)'
      : selectedTailoredDoc
        ? `${fullName.replace(/\s+/g, '_')}_CV_${cleanCompanyName(selectedTailoredDoc.company_name || company).replace(/\s+/g, '_')}.pdf`
        : `${fullName.replace(/\s+/g, '_')}_Base_CV.pdf`;

  const attachedCvScore =
    selectedCvId === 'none'
      ? null
      : selectedTailoredDoc?.fit_score ?? Math.round(fitEval.overallScore);

  const wordCount = useMemo(
    () => paragraphs.join(' ').trim().split(/\s+/).filter(Boolean).length,
    [paragraphs]
  );

  const threadKey = showBlankDropCanvas
    ? 'cl_blank_new'
    : threadScope === 'workspace'
      ? 'workspace_global'
      : `job_${displayJob.id}`;

  const defaultMessagesForJob = useMemo<AiChatMessage[]>(() => {
    if (showBlankDropCanvas) {
      return [
        {
          id: 'cl_blank_seed',
          role: 'assistant',
          text: 'Drop any job link, raw JD, screenshot, or freeform note on the left canvas to generate a brand-new tailored cover letter — your saved history stays untouched.',
        },
      ];
    }
    const leadSkill = displayJob.parsed_skills[0] || 'Python';
    return [
      {
        id: `cl_m1_${subjectKey}`,
        role: 'assistant',
        text:
          coverLetterEntryMode === 'followup'
            ? `Drafted a concise follow-up for ${company} referencing your submitted package.`
            : fitEval.missingSkills.length > 0
              ? `Ready to pitch ${company} (${tone} voice). Ask about @Saved CVs to attach, or apply this tighter opening hook:`
              : `Strong fit for ${company} (${tone} voice). Ask about @Saved CVs to pick your attachment, or apply this opening polish:`,
        proposal: {
          id: `cl_prop_1_${letterKey}`,
          targetAnchorId: 'para-1',
          targetLabel: `Opening Hook · ${company}`,
          oldText: defaultParagraphs[1] || defaultParagraphs[0],
          newText: `Building low-latency ${leadSkill} and production backend systems aligns directly with ${company}'s ${role} charter — and my recent architecture work delivered verified operational gains.`,
          status: 'pending',
        },
      },
    ];
  }, [
    showBlankDropCanvas,
    subjectKey,
    coverLetterEntryMode,
    company,
    role,
    tone,
    letterKey,
    displayJob.parsed_skills,
    fitEval.missingSkills,
    defaultParagraphs,
  ]);

  const messages = coachThreads[threadKey] ?? defaultMessagesForJob;
  const setMessages = (updater: (curr: AiChatMessage[]) => AiChatMessage[]) =>
    updateCoachThread(threadKey, defaultMessagesForJob, updater);

  const [coachMode, setCoachMode] = useState('Tone Refine');
  const [isStreaming, setIsStreaming] = useState(false);

  const openCvPreview = async (cvId: string) => {
    const reqId = ++previewReqIdRef.current;
    const doc = cvId !== 'base' ? tailoredDocs.find((d) => d.doc_id === cvId) || null : null;
    const matchedActiveDetail =
      activeStudioDoc && doc && activeStudioDoc.doc_id === doc.doc_id ? activeStudioDoc : null;

    const previewTitle = doc
      ? `${cleanCompanyName(doc.company_name || company)} · ${cleanTargetJobTitle(doc.job_title || role)}`
      : `${activePersona?.target_title || 'Master Profile'} · Base CV`;

    const initialSnapshot = buildParsedCvSnapshot({
      profile,
      personaId: doc?.persona_id || activePersona?.persona_id,
      activeRegionalPhone,
      docDetail: matchedActiveDetail,
      docSummary: doc,
    });

    const handleEditInStudio = () => {
      setActivePreview(null);
      if (doc) {
        void openDocInStudio(doc.doc_id);
      } else {
        setActiveStudioJob(displayJob);
        navigateTo(`/studio?job_id=${displayJob.id}`);
      }
    };

    const needsFetch = Boolean(doc && !matchedActiveDetail);

    setActivePreview({
      kind: 'cv',
      id: cvId,
      title: previewTitle,
      subtitle: doc ? `${doc.bullet_diffs_count} tailored bullets · ATS PDF Ready` : 'Master Profile Baseline · 0 cr',
      fitScore: doc?.fit_score ?? Math.round(fitEval.overallScore),
      cvDocument: initialSnapshot,
      loading: needsFetch,
      matchedSkills: doc?.parsed_skills || fitEval.matchedSkills,
      primaryActionLabel: selectedCvId === cvId ? 'Attached ✓' : 'Use This CV',
      onPrimaryAction: () => {
        setSelectedCvForJob(displayJob.id, cvId);
        setActivePreview(null);
        pushToast(`Attached ${doc ? cleanCompanyName(doc.company_name || company) : 'Base'} CV to outreach.`, {
          variant: 'success',
        });
      },
      secondaryActionLabel: 'Edit in CV Studio',
      onSecondaryAction: handleEditInStudio,
    });

    if (doc && needsFetch) {
      const fullDetail = await CvFitAPI.getCvFit(doc.doc_id);
      if (previewReqIdRef.current !== reqId) return;
      const hydratedSnapshot = fullDetail
        ? buildParsedCvSnapshot({
          profile,
          personaId: fullDetail.persona_id || doc.persona_id || activePersona?.persona_id,
          activeRegionalPhone,
          docDetail: fullDetail,
          docSummary: doc,
        })
        : initialSnapshot;
      setActivePreview((prev) =>
        prev && prev.kind === 'cv' && prev.id === cvId
          ? {
            ...prev,
            loading: false,
            cvDocument: hydratedSnapshot,
            subtitle:
              fullDetail?.bullet_diffs?.length
                ? `${fullDetail.bullet_diffs.length} tailored bullets · ATS PDF Ready`
                : prev.subtitle,
            matchedSkills:
              fullDetail?.parsed_skills?.length ? fullDetail.parsed_skills : prev.matchedSkills,
          }
          : prev
      );
    }
  };

  const openNewBlankLetter = () => {
    setIsBlankMode(true);
    setSelectedLetterDocId(null);
    setActivePreview(null);
    setDropInput('');
    setBlankToEmail('');
    setBlankCvMenuOpen(false);
    if (attachedScreenshot?.previewUrl) URL.revokeObjectURL(attachedScreenshot.previewUrl);
    setAttachedScreenshot(null);
    setEditingIdx(null);
    scrollHistoryToTop();
    window.requestAnimationFrame(() => blankTextareaRef.current?.focus());
  };

  const openHistoryLetter = (item: CoverLetterItem) => {
    setIsBlankMode(false);
    setSelectedLetterDocId(item.doc_id);
    setActivePreview(null);
    setEditingIdx(null);
    if (item.job_id) {
      const matched =
        allTargetOptions.find((j) => j.id === item.job_id) ||
        pipelineItems.find((p) => p.job.id === item.job_id)?.job;
      if (matched) setActiveStudioJob(matched);
    }
  };

  const handlePreviewResource = (res: AiResourceItem) => {
    if (res.kind === 'cv') {
      void openCvPreview(res.payloadId);
      return;
    }
    if (res.kind === 'letter') {
      const letter = historyLetters.find((c) => String(c.job_id) === res.payloadId);
      setActivePreview({
        kind: 'letter',
        id: res.id,
        title: res.title,
        subtitle: 'Saved Cover Letter',
        subjectLine: letter?.subject_line || subjectLine,
        bodyText: letter?.body_markdown || paragraphs.join('\n\n'),
        primaryActionLabel: 'Open Letter',
        onPrimaryAction: () => {
          if (letter) {
            openHistoryLetter(letter);
          } else {
            const targetJob = allTargetOptions.find((j) => String(j.id) === res.payloadId);
            if (targetJob) {
              setIsBlankMode(false);
              setSelectedLetterDocId(null);
              setActiveStudioJob(targetJob);
            }
          }
          setActivePreview(null);
        },
      });
      return;
    }
    if (res.kind === 'job') {
      const targetJob = allTargetOptions.find((j) => String(j.id) === res.payloadId);
      if (!targetJob) return;
      const je = evaluateAllPersonas(targetJob, profile).best;
      setActivePreview({
        kind: 'job',
        id: res.id,
        title: cleanTargetJobTitle(targetJob.title),
        subtitle: `${cleanCompanyName(targetJob.company_name)} · ${targetJob.location}`,
        fitScore: je.overallScore,
        summary: targetJob.raw_description,
        bullets: targetJob.responsibilities,
        matchedSkills: je.matchedSkills,
        missingSkills: je.missingSkills,
        primaryActionLabel: 'Draft New Letter for Role',
        onPrimaryAction: () => {
          void handleCreateFromQuickRole(targetJob);
          setActivePreview(null);
        },
      });
    }
  };

  const handleSelectResource = (res: AiResourceItem) => {
    if (res.kind === 'cv') {
      setSelectedCvForJob(displayJob.id, res.payloadId);
      pushToast(`Attached ${res.title} to your outreach card.`, { variant: 'success' });
      return;
    }
    if (res.kind === 'letter') {
      const letter = historyLetters.find((c) => String(c.job_id) === res.payloadId);
      if (letter) {
        openHistoryLetter(letter);
        pushToast(`Opened letter for ${cleanCompanyName(letter.company_name || 'Target')}.`);
        return;
      }
    }
    if (res.kind === 'letter' || res.kind === 'job') {
      const targetJob = allTargetOptions.find((j) => String(j.id) === res.payloadId);
      if (targetJob) {
        setIsBlankMode(false);
        const existingMatch = historyLetters.find((c) => c.job_id === targetJob.id);
        setSelectedLetterDocId(existingMatch?.doc_id || null);
        setActiveStudioJob(targetJob);
        pushToast(`Switched target role to ${cleanCompanyName(targetJob.company_name)}.`);
      }
    }
  };

  const handleConfirmAction = (actionId: string) => {
    const msg = messages.find((m) => m.actionCard?.id === actionId);
    const card = msg?.actionCard;
    if (!card) return;
    if (card.actionType === 'pipeline_stage') {
      const nextStatus = (card.payload?.status as 'applied' | 'interview' | 'saved') || 'applied';
      const letterPayload: CoverLetterItem = {
        doc_id: activeLetter?.doc_id || `cl_${Date.now()}`,
        job_id: displayJob.id > 0 ? displayJob.id : null,
        company_name: company,
        job_title: role,
        recipient_email: toEmail || null,
        source_label: activeLetter?.source_label || 'Outreach Composer',
        subject_line: subjectLine,
        body_markdown: paragraphs.join('\n\n'),
        created_at: activeLetter?.created_at || new Date().toISOString(),
      };
      addToPipeline(displayJob, nextStatus, toEmail || null, {
        tailoredCvDocId: selectedCvId !== 'none' && selectedCvId !== 'base' ? selectedCvId : null,
        coverLetter: letterPayload,
        silent: true,
      });
      pushToast(`Pipeline updated: ${company} marked ${nextStatus}.`, { variant: 'success' });
    }
    setMessages((prev) =>
      prev.map((m) =>
        m.actionCard?.id === actionId ? { ...m, actionCard: { ...m.actionCard, status: 'confirmed' } } : m
      )
    );
  };

  const handleAuditAction = (aud: AiAuditItem) => {
    if (aud.actionType === 'open_followup' || aud.actionType === 'open_letter') {
      const targetJob =
        pipelineItems.find((p) => String(p.job.id) === aud.payloadId)?.job ||
        allTargetOptions.find((j) => String(j.id) === aud.payloadId);
      if (targetJob) {
        const match = historyLetters.find((c) => c.job_id === targetJob.id);
        setIsBlankMode(false);
        setSelectedLetterDocId(match?.doc_id || null);
        openJobInCoverLetters(targetJob, {
          mode: aud.actionType === 'open_followup' ? 'followup' : 'pitch',
        });
      }
      return;
    }
    if (aud.actionType === 'inject_text' && aud.payloadId) {
      setFocusedAnchor({ id: 'para-1', label: `Paragraph 2 · Bridge ${aud.payloadId}` });
      setParagraphs((prev) =>
        prev.map((p, i) =>
          i === 1 && !p.toLowerCase().includes(aud.payloadId!.toLowerCase())
            ? `${p.replace(/\.$/, '')}, building adjacent strength toward ${aud.payloadId}.`
            : p
        )
      );
      pushToast(`Inserted ${aud.payloadId} bridge into opening paragraph.`);
    }
  };

  const handleGenerateFromBrief = () => {
    const unlocked = isJobUnlocked(displayJob.id, 'cl');
    requestCreditAction({
      cost: unlocked ? 0 : 1,
      unlockKey: `cl_${displayJob.id}`,
      actionLabel: 'Generate Cover Letter',
      jobTarget: `${company} — ${role}`,
      onAuthorized: async () => {
        const res = await CoverLetterAPI.generateCoverLetter({
          base_cv_text: `${activePersona?.summary_bio || ''}\nFocus: ${hookFocus}`,
          job_id: displayJob.id > 0 ? displayJob.id : undefined,
          company_name: company,
          job_title: role,
          job_description_text: displayJob.raw_description,
          tone,
        });
        const chunks = res.coverLetter.body_markdown.split('\n\n');
        const finalChunks = lengthMode === 'compact' ? chunks.slice(0, 3) : chunks;
        const nextDoc: CoverLetterItem = {
          ...res.coverLetter,
          doc_id: activeLetter?.doc_id || res.coverLetter.doc_id,
          recipient_email: toEmail || activeLetter?.recipient_email || null,
          source_label: activeLetter?.source_label || 'Regenerated Brief',
          body_markdown: finalChunks.join('\n\n'),
        };
        setSubjectOverrides((prev) => ({ ...prev, [nextDoc.doc_id]: nextDoc.subject_line }));
        setParaOverrides((prev) => ({ ...prev, [nextDoc.doc_id]: finalChunks }));
        saveCoverLetter(nextDoc);
        setSelectedLetterDocId(nextDoc.doc_id);
        setIsBlankMode(false);
        setBriefPopoverOpen(false);
        pushToast('Generated tailored cover letter.', { variant: 'success' });
      },
    });
  };

  const agentThreadRef = useRef<Record<string, string>>({});

  const handleSendCoachMessage = async (prompt: string, mode: string) => {
    setMessages((prev) => [...prev, { id: `clu_${Date.now()}`, role: 'user', text: prompt }]);
    setIsStreaming(true);

    if (getAccessToken()) {
      const assistantId = `cla_${Date.now()}`;
      try {
        const key = String(displayJob.id);
        let threadId = agentThreadRef.current[key];
        if (!threadId) {
          const th = await AgentAPI.createThread({
            surface: 'cover_letter',
            job_id: resolveServerJobId(displayJob.id, displayJob.server_id),
            doc_id: activeLetter?.doc_id,
            title: `${company} — Cover Letter`,
          });
          threadId = th.id;
          agentThreadRef.current[key] = threadId;
        }
        setMessages((prev) => [...prev, { id: assistantId, role: 'assistant', text: '' }]);
        await AgentAPI.streamMessage(
          threadId,
          {
            prompt,
            mode,
            focused_anchor: focusedAnchor,
            job_id: resolveServerJobId(displayJob.id, displayJob.server_id),
            doc_id: activeLetter?.doc_id,
          },
          {
            onThinkingStep: (step) =>
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, thinkingSummary: step } : m))
              ),
            onTextDelta: (delta) =>
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, text: `${m.text}${delta}` } : m))
              ),
            onProposalCard: (proposal) =>
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, proposal } : m))
              ),
            onActionCard: (actionCard) =>
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, actionCard } : m))
              ),
            onResourceList: (resources) =>
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, resources } : m))
              ),
            onAuditSummary: (audit) =>
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, audit } : m))
              ),
          }
        );
        setIsStreaming(false);
        return;
      } catch {
        setMessages((prev) => prev.filter((m) => m.id !== assistantId));
      }
    }

    const workspaceReply = buildWorkspaceCoachReply({
      prompt,
      surface: 'cover-letter',
      activeJob: displayJob,
      profile,
      tailoredDocs,
      coverLetters: historyLetters,
      radarJobs,
      pipelineItems,
    });

    const anchorId = focusedAnchor?.id || 'para-1';
    const pIdx = Number(anchorId.replace('para-', '')) || 1;
    const oldTxt = paragraphs[pIdx] || paragraphs[0];

    setTimeout(() => {
      if (workspaceReply) {
        setMessages((prev) => [...prev, workspaceReply]);
        setIsStreaming(false);
        return;
      }
      const nextTxt = buildCoverLetterRewrite(
        oldTxt,
        mode,
        tone,
        company,
        role,
        displayJob.parsed_skills
      );
      setMessages((prev) => [
        ...prev,
        {
          id: `cla_${Date.now()}`,
          role: 'assistant',
          text: `Updated paragraph ${pIdx + 1} from your Master Profile:`,
          proposal: {
            id: `clp_${Date.now()}`,
            targetAnchorId: anchorId,
            targetLabel: focusedAnchor?.label || `Paragraph ${pIdx + 1}`,
            oldText: oldTxt,
            newText: nextTxt,
            status: 'pending',
          },
        },
      ]);
      setIsStreaming(false);
    }, 360);
  };

  const handleUndoProposal = (propId: string) => {
    const prop = messages.find((m) => m.proposal?.id === propId)?.proposal;
    if (!prop) return;
    const pIdx = Number(prop.targetAnchorId.replace('para-', '')) || 1;
    setParagraphs((prev) => prev.map((x, i) => (i === pIdx ? prop.oldText : x)));
    setMessages((prev) =>
      prev.map((m) => (m.proposal?.id === propId ? { ...m, proposal: { ...m.proposal, status: 'pending' } } : m))
    );
    pushToast('Reverted proposal change.');
  };

  const applyProposal = (propId: string) => {
    const prop = messages.find((m) => m.proposal?.id === propId)?.proposal;
    if (!prop) return;
    const pIdx = Number(prop.targetAnchorId.replace('para-', '')) || 1;
    setParagraphs((prev) => prev.map((p, i) => (i === pIdx ? prop.newText : p)));
    setMessages((prev) =>
      prev.map((m) =>
        m.proposal?.id === propId ? { ...m, proposal: { ...m.proposal, status: 'applied' } } : m
      )
    );
    setAppliedAnchorId(prop.targetAnchorId);
    setFitPulse(true);
    if (appliedTimerRef.current) window.clearTimeout(appliedTimerRef.current);
    if (pulseTimerRef.current) window.clearTimeout(pulseTimerRef.current);
    appliedTimerRef.current = window.setTimeout(() => setAppliedAnchorId(null), 1100);
    pulseTimerRef.current = window.setTimeout(() => setFitPulse(false), 700);
    if (getAccessToken()) {
      void AgentAPI.resolveProposal(propId, 'apply').catch(() => {});
    }
    pushToast('Applied edit to outreach pitch.', {
      variant: 'success',
      undoLabel: 'Undo',
      onUndo: () => handleUndoProposal(propId),
    });
  };

  const downloadAttachedCv = async () => {
    if (selectedCvId === 'none') return;
    if (selectedTailoredDoc) {
      const detail = await CvFitAPI.getCvFit(selectedTailoredDoc.doc_id);
      if (detail) {
        await CvFitAPI.downloadArtifact(detail, 'pdf');
        return;
      }
    }
    const blob = new Blob(
      [`Tailored ATS Resume — ${fullName}\nRole: ${role} @ ${company}\n${activePersona?.summary_bio || ''}`],
      { type: 'text/plain' }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = attachedCvLabel.replace(/\.pdf$/, '.txt');
    a.click();
    URL.revokeObjectURL(url);
  };

  const commitOutreachToWorkspace = () => {
    const bodyMd = paragraphs.join('\n\n');
    const saved: CoverLetterItem = {
      doc_id: activeLetter?.doc_id || `cl_${Date.now()}`,
      job_id: displayJob.id > 0 ? displayJob.id : null,
      company_name: company,
      job_title: role,
      recipient_email: toEmail || null,
      source_label: activeLetter?.source_label || 'Outreach Composer',
      subject_line: subjectLine,
      body_markdown: bodyMd,
      created_at: activeLetter?.created_at || new Date().toISOString(),
    };
    saveCoverLetter(saved);
    setSelectedLetterDocId(saved.doc_id);
    setIsBlankMode(false);
    if (markAppliedOnSend) {
      addToPipeline(displayJob, 'applied', toEmail || null, {
        tailoredCvDocId: selectedCvId !== 'none' && selectedCvId !== 'base' ? selectedCvId : null,
        coverLetter: saved,
        silent: true,
      });
    }
  };

  const attachImageFile = (file: File) => {
    if (attachedScreenshot?.previewUrl) {
      URL.revokeObjectURL(attachedScreenshot.previewUrl);
    }
    const previewUrl = URL.createObjectURL(file);
    setAttachedScreenshot({ name: file.name || 'screenshot.png', previewUrl });
    pushToast('Screenshot attached — click Create Tailored Letter.', { variant: 'info' });
  };

  const handleDropZonePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of Array.from(items)) {
      if (item.type.startsWith('image/')) {
        e.preventDefault();
        const file = item.getAsFile();
        if (file) {
          attachImageFile(file);
        } else {
          setAttachedScreenshot({ name: 'pasted-screenshot.png', previewUrl: '' });
          pushToast('Screenshot captured — click Create Tailored Letter.', { variant: 'info' });
        }
        return;
      }
    }
  };

  const handleDropZoneDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(false);

    const files = Array.from(e.dataTransfer?.files || []);
    const imgFile = files.find((f) => f.type.startsWith('image/'));
    if (imgFile) {
      attachImageFile(imgFile);
      return;
    }
    const txtFile = files.find((f) => /\.(txt|md)$/i.test(f.name) || f.type.startsWith('text/'));
    if (txtFile) {
      const content = await txtFile.text();
      setDropInput((prev) => (prev.trim() ? `${prev.trim()}\n${content}` : content));
      return;
    }
    const droppedText = e.dataTransfer?.getData('text/uri-list') || e.dataTransfer?.getData('text/plain');
    if (droppedText?.trim()) {
      setDropInput((prev) => (prev.trim() ? `${prev.trim()}\n${droppedText.trim()}` : droppedText.trim()));
    }
  };

  const handleCreateNewLetterFromDrop = async () => {
    if (!dropInput.trim() && !attachedScreenshot) return;
    setIsCreatingLetter(true);
    try {
      const parsed = parseCoverLetterDropInput({
        rawText: dropInput,
        hasScreenshot: Boolean(attachedScreenshot),
        screenshotName: attachedScreenshot?.name,
      });

      let targetJob: JobItem;
      if (parsed.sourceKind === 'link' || parsed.sourceKind === 'jd') {
        const ingested = await ingestJobUrlOrText(dropInput.trim(), { onlySaveInterest: true });
        if (ingested) {
          const fallbackComp = ingested.company_name === 'Target Organization';
          targetJob = {
            ...ingested,
            company_name: fallbackComp && parsed.company !== 'Target Team' ? parsed.company : ingested.company_name,
            title:
              parsed.role && parsed.role !== 'Senior AI & Data Engineer' && ingested.title === 'Custom Target Role'
                ? parsed.role
                : ingested.title,
            recruiter_email: ingested.recruiter_email || parsed.recipientEmail || null,
            parsed_skills: ingested.parsed_skills.length > 0 ? ingested.parsed_skills : parsed.skills,
          };
          setRadarJobs((prev) => prev.map((j) => (j.id === targetJob.id ? targetJob : j)));
        } else {
          targetJob = {
            id: Date.now(),
            source_id: `drop_${Date.now()}`,
            title: parsed.role,
            company_name: parsed.company,
            location: parsed.location,
            url: parsed.url,
            raw_description: parsed.summaryDescription,
            fit_score: 89,
            is_high_match: true,
            source_type: parsed.sourceKind === 'link' ? 'url_ingest' : 'custom_drop',
            parsed_skills: parsed.skills,
            responsibilities: [`Deliver production impact as ${parsed.role} at ${parsed.company}`],
            location_type: parsed.location.toLowerCase().includes('remote') ? 'Remote' : 'Hybrid',
            created_at: new Date().toISOString(),
            recruiter_email: parsed.recipientEmail || null,
          };
          setRadarJobs((prev) => [targetJob, ...prev]);
          addToInterest(targetJob);
        }
      } else {
        targetJob = {
          id: Date.now(),
          source_id: `drop_${Date.now()}`,
          title: parsed.role,
          company_name: parsed.company,
          location: parsed.location,
          url: parsed.url,
          raw_description: parsed.summaryDescription,
          fit_score: 91,
          is_high_match: true,
          source_type: parsed.sourceKind === 'screenshot' ? 'screenshot_ocr' : 'custom_brief',
          parsed_skills: parsed.skills,
          responsibilities: [
            `Drive ${parsed.role} delivery with ${parsed.skills.slice(0, 3).join(', ')}`,
          ],
          location_type: parsed.location.toLowerCase().includes('remote') ? 'Remote' : 'Hybrid',
          created_at: new Date().toISOString(),
          recruiter_email: parsed.recipientEmail || null,
        };
        setRadarJobs((prev) => [targetJob, ...prev]);
        addToInterest(targetJob);
      }

      const drafted = composeTailoredOutreachDraft({
        target: parsed,
        fullName,
        phoneDisplay,
        primaryCompany: activePersona?.experience_highlights[0]?.company || 'Swvl',
        primarySummary:
          activePersona?.summary_bio ||
          'Data Scientist with 3+ years building predictive ML models and FastAPI systems.',
        tone,
        entryMode: coverLetterEntryMode,
      });

      const finalRecipient = blankToEmail.trim() || parsed.recipientEmail || targetJob.recruiter_email || '';
      const newDoc: CoverLetterItem = {
        doc_id: `cl_${Date.now()}`,
        job_id: targetJob.id,
        company_name: cleanCompanyName(targetJob.company_name),
        job_title: cleanTargetJobTitle(targetJob.title),
        recipient_email: finalRecipient || null,
        source_label: parsed.sourceLabel,
        subject_line: drafted.subjectLine,
        body_markdown: drafted.paragraphs.join('\n\n'),
        created_at: new Date().toISOString(),
      };

      saveCoverLetter(newDoc);
      setActiveStudioJob(targetJob);
      setSelectedLetterDocId(newDoc.doc_id);
      if (blankCvId !== 'auto') {
        setSelectedCvForJob(targetJob.id, blankCvId);
      }
      setIsBlankMode(false);
      scrollHistoryToTop();
      setSubjectOverrides((prev) => ({ ...prev, [newDoc.doc_id]: drafted.subjectLine }));
      setParaOverrides((prev) => ({ ...prev, [newDoc.doc_id]: drafted.paragraphs }));
      if (finalRecipient) {
        setToOverrides((prev) => ({ ...prev, [newDoc.doc_id]: finalRecipient }));
      }

      const targetThreadKey = threadScope === 'workspace' ? 'workspace_global' : `job_${targetJob.id}`;
      updateCoachThread(targetThreadKey, [], (curr) => [
        ...curr,
        {
          id: `drop_sync_${Date.now()}`,
          role: 'assistant',
          text: `Tailored a fresh cover letter for ${parsed.company} (${parsed.role}) from ${parsed.sourceLabel}${finalRecipient ? ` · To: ${finalRecipient}` : ''
            }${parsed.emphasis ? ` · Emphasizing ${parsed.emphasis}` : ''}. Ask me to sharpen any paragraph or pick a CV.`,
        },
      ]);

      setDropInput('');
      setBlankToEmail('');
      setBlankCvMenuOpen(false);
      if (attachedScreenshot?.previewUrl) URL.revokeObjectURL(attachedScreenshot.previewUrl);
      setAttachedScreenshot(null);
      setFitPulse(true);
      if (pulseTimerRef.current) window.clearTimeout(pulseTimerRef.current);
      pulseTimerRef.current = window.setTimeout(() => setFitPulse(false), 700);
      pushToast(`Created new tailored letter for ${newDoc.company_name}.`, {
        variant: 'success',
      });
    } finally {
      setIsCreatingLetter(false);
    }
  };

  const handleCreateBlankManualLetter = () => {
    const { doc, paragraphs: blankParagraphs } = buildBlankManualCoverLetterRecord({
      fullName,
      phoneDisplay,
    });
    const manualRecipient = blankToEmail.trim();
    const docWithRecipient = manualRecipient ? { ...doc, recipient_email: manualRecipient } : doc;
    saveCoverLetter(docWithRecipient);
    setSelectedLetterDocId(docWithRecipient.doc_id);
    setIsBlankMode(false);
    scrollHistoryToTop();
    setSubjectOverrides((prev) => ({ ...prev, [docWithRecipient.doc_id]: docWithRecipient.subject_line }));
    setParaOverrides((prev) => ({ ...prev, [docWithRecipient.doc_id]: blankParagraphs }));
    if (manualRecipient) {
      setToOverrides((prev) => ({ ...prev, [docWithRecipient.doc_id]: manualRecipient }));
    }
    setDropInput('');
    setBlankToEmail('');
    setBlankCvMenuOpen(false);
    if (attachedScreenshot?.previewUrl) URL.revokeObjectURL(attachedScreenshot.previewUrl);
    setAttachedScreenshot(null);
    pushToast('Opened a clean manual cover letter draft.', { variant: 'info' });
  };

  const handleCreateFromQuickRole = (job: JobItem) => {
    const { doc: newDoc, paragraphs: bodyParagraphs } = buildQuickRoleCoverLetterRecord({
      job,
      fullName,
      phoneDisplay,
      primaryCompany: activePersona?.experience_highlights[0]?.company || 'Swvl',
    });
    const manualRecipient = blankToEmail.trim() || newDoc.recipient_email || '';
    const finalDoc = manualRecipient ? { ...newDoc, recipient_email: manualRecipient } : newDoc;
    saveCoverLetter(finalDoc);
    setActiveStudioJob(job);
    setSelectedLetterDocId(finalDoc.doc_id);
    if (blankCvId !== 'auto') {
      setSelectedCvForJob(job.id, blankCvId);
    }
    setIsBlankMode(false);
    scrollHistoryToTop();
    setSubjectOverrides((prev) => ({ ...prev, [finalDoc.doc_id]: finalDoc.subject_line }));
    setParaOverrides((prev) => ({ ...prev, [finalDoc.doc_id]: bodyParagraphs }));
    if (manualRecipient) {
      setToOverrides((prev) => ({ ...prev, [finalDoc.doc_id]: manualRecipient }));
    }
    setBlankToEmail('');
    setBlankCvMenuOpen(false);
    pushToast(`Created new tailored letter for ${cleanCompanyName(job.company_name)}.`, { variant: 'success' });
  };

  const handleSendViaGmail = async () => {
    if (!toEmail.trim()) {
      setToWarnPulse(true);
      if (warnTimerRef.current) window.clearTimeout(warnTimerRef.current);
      warnTimerRef.current = window.setTimeout(() => setToWarnPulse(false), 1800);
      toInputRef.current?.focus();
      pushToast('Add a recipient email in the To field to send directly.', { variant: 'warn' });
      return;
    }
    const bodyText = paragraphs.join('\n\n');
    await downloadAttachedCv();
    try {
      await navigator.clipboard.writeText(bodyText);
    } catch {
      // ignore clipboard permissions
    }
    const url = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(toEmail)}&su=${encodeURIComponent(
      subjectLine
    )}&body=${encodeURIComponent(bodyText)}${ccSelf && myEmail ? `&cc=${encodeURIComponent(myEmail)}` : ''}`;
    window.open(url, '_blank');
    commitOutreachToWorkspace();
    pushToast(
      selectedCvId === 'none'
        ? 'Opened email compose (no CV attached) & logged Applied.'
        : `Opened email compose & downloaded ${attachedCvLabel} to attach.`,
      { variant: 'success' }
    );
  };

  const handleCopyAll = async () => {
    const bundle = `${toEmail.trim() ? `To: ${toEmail}\n` : ''}Subject: ${subjectLine}\n\n${paragraphs.join('\n\n')}`;
    await navigator.clipboard.writeText(bundle);
    pushToast('Copied outreach pitch to clipboard.', { variant: 'success' });
  };

  const renderHighlighted = (text: string) => {
    if (viewMode === 'clean') return text;
    const keywords = displayJob.parsed_skills.slice(0, 6);
    if (keywords.length === 0) return text;
    const parts = text.split(
      new RegExp(`(${keywords.map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi')
    );
    return parts.map((part, idx) =>
      keywords.some((k) => k.toLowerCase() === part.toLowerCase()) ? (
        <mark
          key={idx}
          style={{
            background: 'var(--mist)',
            color: 'var(--ink)',
            padding: '1px 4px',
            borderRadius: 3,
            fontWeight: 600,
          }}
        >
          {part}
        </mark>
      ) : (
        <React.Fragment key={idx}>{part}</React.Fragment>
      )
    );
  };

  const letterPane = (
    <div className="t-atelier-workbench t-cl-workbench">
      <AtelierPreviewDrawer preview={activePreview} onClose={() => setActivePreview(null)} />

      <div className="t-atelier-desk-scroll">
        {showBlankDropCanvas ? (
          <div className="t-cl-stationery-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
              <div>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, marginBottom: 5 }}>
                  <TailoredIcon name="coverLetter" size={14} color="var(--dye)" />
                  <span className="t-mono" style={{ fontSize: 10.5, fontWeight: 600, letterSpacing: '0.09em', color: 'var(--dye)' }}>
                    NEW OUTREACH LETTER
                  </span>
                </div>
                <h2 style={{ fontFamily: 'var(--font-voice)', fontSize: 23, fontWeight: 540, color: 'var(--ink)', margin: 0, letterSpacing: '-0.02em' }}>
                  Drop anything to start a fresh letter
                </h2>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', position: 'relative' }}>
                {(['pitch', 'letter', 'followup'] as const).map((m) => (
                  <button
                    key={m}
                    type="button"
                    className={`t-atelier-stage-pill ${coverLetterEntryMode === m ? 't-atelier-stage-pill--active' : ''}`}
                    onClick={() => setCoverLetterEntryMode(m)}
                  >
                    {m === 'pitch' ? 'Email Pitch' : m === 'letter' ? 'Formal Letter' : 'Follow-Up'}
                  </button>
                ))}

                <button
                  type="button"
                  className="t-cl-stationery-pill"
                  onClick={() => setBlankCvMenuOpen((v) => !v)}
                  title="Choose which CV to pair with this letter"
                >
                  <TailoredIcon name="cv" size={12} color="var(--dye)" />
                  <span>
                    {blankCvId === 'auto'
                      ? 'Pair CV: Auto'
                      : blankCvId === 'base'
                        ? 'Pair CV: Base'
                        : blankCvId === 'none'
                          ? 'Email Only'
                          : `Pair: ${cleanCompanyName(tailoredDocs.find((d) => d.doc_id === blankCvId)?.company_name || 'CV')}`}
                  </span>
                  <TailoredIcon name="chevronDown" size={10} color="var(--n700)" />
                </button>

                {blankCvMenuOpen && (
                  <div className="t-popover" style={{ top: 'calc(100% + 6px)', right: 0, width: 256, zIndex: 45 }}>
                    <div className="t-atelier-popover-label">CV Pairing for New Letter</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 200, overflowY: 'auto' }}>
                      <button
                        type="button"
                        className={`t-atelier-menu-row ${blankCvId === 'auto' ? 't-atelier-menu-row--active' : ''}`}
                        onClick={() => {
                          setBlankCvId('auto');
                          setBlankCvMenuOpen(false);
                        }}
                      >
                        <span>Auto-match best CV</span>
                      </button>
                      <button
                        type="button"
                        className={`t-atelier-menu-row ${blankCvId === 'base' ? 't-atelier-menu-row--active' : ''}`}
                        onClick={() => {
                          setBlankCvId('base');
                          setBlankCvMenuOpen(false);
                        }}
                      >
                        <span>{activePersona?.target_title || 'Master'} · Base CV (0 cr)</span>
                      </button>
                      {tailoredDocs.slice(0, 5).map((doc) => (
                        <button
                          key={doc.doc_id}
                          type="button"
                          className={`t-atelier-menu-row ${blankCvId === doc.doc_id ? 't-atelier-menu-row--active' : ''}`}
                          onClick={() => {
                            setBlankCvId(doc.doc_id);
                            setBlankCvMenuOpen(false);
                          }}
                        >
                          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {cleanCompanyName(doc.company_name || 'CV')} · {cleanTargetJobTitle(doc.job_title)}
                          </span>
                        </button>
                      ))}
                      <button
                        type="button"
                        className={`t-atelier-menu-row ${blankCvId === 'none' ? 't-atelier-menu-row--active' : ''}`}
                        onClick={() => {
                          setBlankCvId('none');
                          setBlankCvMenuOpen(false);
                        }}
                      >
                        <span>No CV (email pitch only)</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div
              className={`t-cl-stationery-well ${isDraggingOver ? 't-cl-drop-well--dragging' : ''}`}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDraggingOver(true);
              }}
              onDragLeave={() => setIsDraggingOver(false)}
              onDrop={handleDropZoneDrop}
            >
              <div className="t-cl-stationery-to-row">
                <label
                  htmlFor="cl-blank-to-input"
                  className="t-mono"
                  style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--n500)', flexShrink: 0 }}
                >
                  To
                </label>
                <input
                  id="cl-blank-to-input"
                  type="email"
                  className="t-cl-stationery-to-input"
                  placeholder="recruiter@company.com (optional — auto-detected from paste)"
                  value={blankToEmail}
                  onChange={(e) => setBlankToEmail(e.target.value)}
                />
              </div>

              <div className="t-cl-drop-input-wrap" style={{ minHeight: 112 }}>
                <TypewriterDropPlaceholder
                  tone="light"
                  items={COVER_LETTER_DROP_PROMPTS}
                  visible={!dropInput && !attachedScreenshot}
                />
                <textarea
                  ref={blankTextareaRef}
                  id="cl-blank-drop-input"
                  aria-label="Drop a job link, job description, screenshot, or freeform brief"
                  rows={5}
                  className="t-cl-stationery-textarea"
                  placeholder=""
                  value={dropInput}
                  onChange={(e) => setDropInput(e.target.value)}
                  onPaste={handleDropZonePaste}
                  onKeyDown={(e) => {
                    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                      e.preventDefault();
                      void handleCreateNewLetterFromDrop();
                    }
                  }}
                />
              </div>

              {attachedScreenshot && (
                <div className="t-cl-drop-thumb">
                  {attachedScreenshot.previewUrl ? (
                    <img src={attachedScreenshot.previewUrl} alt="Attached target screenshot" />
                  ) : (
                    <TailoredIcon name="cv" size={16} color="var(--kraft)" />
                  )}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <span style={{ fontWeight: 600 }}>{attachedScreenshot.name}</span>
                    <span className="t-mono" style={{ fontSize: 10.5, color: 'var(--kraft)' }}>
                      Screenshot OCR ready
                    </span>
                  </div>
                  <button
                    type="button"
                    className="t-atelier-icon-btn"
                    style={{ width: 24, height: 24, color: 'var(--chalk)' }}
                    aria-label="Remove screenshot"
                    onClick={() => {
                      if (attachedScreenshot.previewUrl) URL.revokeObjectURL(attachedScreenshot.previewUrl);
                      setAttachedScreenshot(null);
                    }}
                  >
                    <TailoredIcon name="close" size={12} color="var(--chalk)" />
                  </button>
                </div>
              )}

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,.txt,.md"
                style={{ display: 'none' }}
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  if (file.type.startsWith('image/')) {
                    attachImageFile(file);
                  } else {
                    const txt = await file.text();
                    setDropInput((prev) => (prev.trim() ? `${prev.trim()}\n${txt}` : txt));
                  }
                  e.target.value = '';
                }}
              />

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', paddingTop: 8, borderTop: '1px solid rgba(26, 20, 18, 0.08)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    className="t-cl-stationery-iconbtn"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <TailoredIcon name="upload" size={13} color="var(--ink)" />
                    <span>Attach Screenshot / File</span>
                  </button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <button
                    type="button"
                    className="t-atelier-btn-tonal"
                    onClick={handleCreateBlankManualLetter}
                  >
                    <span>Start Blank Email</span>
                  </button>
                  <button
                    type="button"
                    className="t-atelier-btn-primary"
                    disabled={isCreatingLetter || (!dropInput.trim() && !attachedScreenshot)}
                    onClick={() => void handleCreateNewLetterFromDrop()}
                  >
                    <TailoredIcon name="coverLetter" size={13} color="var(--ink)" />
                    <span>{isCreatingLetter ? 'Creating...' : 'Create Tailored Letter'}</span>
                  </button>
                </div>
              </div>
            </div>

            <SavedRoleDropdown
              tone="light"
              jobs={[...interestList, ...radarJobs]}
              profile={profile}
              onSelectRole={handleCreateFromQuickRole}
            />
          </div>
        ) : (
          <div className="t-outreach-card">
            {/* 1. Envelope Header: Channel Mode + Always-Editable To / Subject */}
            <div className="t-outreach-head">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  {(['pitch', 'letter', 'followup'] as const).map((m) => (
                    <button
                      key={m}
                      type="button"
                      className={`t-atelier-stage-pill ${coverLetterEntryMode === m ? 't-atelier-stage-pill--active' : ''
                        }`}
                      onClick={() => setCoverLetterEntryMode(m)}
                    >
                      {m === 'pitch' ? 'Email Pitch' : m === 'letter' ? 'Formal Letter' : '7-Day Follow-Up'}
                    </button>
                  ))}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  {(['clean', 'keywords'] as const).map((vm) => (
                    <button
                      key={vm}
                      type="button"
                      className={`t-atelier-stage-pill ${viewMode === vm ? 't-atelier-stage-pill--active' : ''}`}
                      onClick={() => setViewMode(vm)}
                    >
                      {vm === 'clean' ? 'Clean' : 'Keywords'}
                    </button>
                  ))}
                </div>
              </div>

              <div className={`t-outreach-field-row ${toWarnPulse ? 't-outreach-field-row--warn' : ''}`}>
                <label htmlFor="cl-to-input" className="t-outreach-field-label">
                  To
                </label>
                <input
                  ref={toInputRef}
                  id="cl-to-input"
                  name="recipientEmail"
                  className="t-outreach-field-input"
                  placeholder="recruiter@company.com (required to send directly)"
                  value={toEmail}
                  onChange={(e) => {
                    setToForLetter(e.target.value);
                    if (toWarnPulse) setToWarnPulse(false);
                  }}
                />
                {displayJob.url && (
                  <button
                    type="button"
                    className="t-atelier-btn-ghost"
                    style={{ padding: '2px 7px', fontSize: 11.5, color: 'var(--dye)' }}
                    title="Open source job listing"
                    onClick={() => window.open(displayJob.url, '_blank')}
                  >
                    <span>Listing</span>
                    <TailoredIcon name="external" size={11} color="var(--dye)" />
                  </button>
                )}
                <label
                  htmlFor="cl-cc-me"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 5,
                    fontSize: 12,
                    color: 'var(--n500)',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                  }}
                >
                  <input
                    id="cl-cc-me"
                    type="checkbox"
                    checked={ccSelf}
                    onChange={(e) => setCcSelf(e.target.checked)}
                  />
                  <span>CC me</span>
                </label>
              </div>

              <div className="t-outreach-field-row">
                <label htmlFor="cl-subject-input" className="t-outreach-field-label">
                  Subject
                </label>
                <input
                  id="cl-subject-input"
                  name="subjectLine"
                  className="t-outreach-field-input t-outreach-field-input--bold"
                  value={subjectLine}
                  onChange={(e) => setSubjectLine(e.target.value)}
                />
              </div>
            </div>

            {/* 2. Calm Interactive Prose Body */}
            <div className="t-outreach-body">
              {paragraphs.map((p, idx) => {
                const anchorId = `para-${idx}`;
                return (
                  <div
                    key={idx}
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
                          setFocusedAnchor({ id: anchorId, label: `Paragraph ${idx + 1}` });
                        }}
                      >
                        Ask AI
                      </button>
                      <button
                        type="button"
                        className="t-microbar-btn"
                        onClick={() => {
                          setParagraphs((prev) =>
                            prev.map((x, i) => (i === idx ? `${x.split('.')[0].trim()}.` : x))
                          );
                          pushToast(`Condensed paragraph ${idx + 1}.`);
                        }}
                      >
                        Shorten
                      </button>
                      <button
                        type="button"
                        className="t-microbar-btn"
                        onClick={() => {
                          setEditingIdx(idx);
                          setEditBuffer(p);
                        }}
                      >
                        Edit
                      </button>
                    </div>

                    {editingIdx === idx ? (
                      <div>
                        <textarea
                          rows={4}
                          value={editBuffer}
                          onChange={(e) => setEditBuffer(e.target.value)}
                          style={{
                            width: '100%',
                            background: 'white',
                            border: 'none',
                            borderRadius: '4px 10px 4px 10px',
                            boxShadow: 'inset 0 0 0 1.5px var(--ink)',
                            padding: '10px 12px',
                            fontFamily: 'var(--font-ui)',
                            fontSize: 14.5,
                            lineHeight: 1.58,
                            color: 'var(--ink)',
                            outline: 'none',
                            resize: 'vertical',
                          }}
                        />
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6, marginTop: 6 }}>
                          <button type="button" className="t-atelier-btn-ghost" onClick={() => setEditingIdx(null)}>
                            Cancel
                          </button>
                          <button
                            type="button"
                            className="t-atelier-btn-primary"
                            onClick={() => {
                              setParagraphs((prev) => prev.map((x, i) => (i === idx ? editBuffer : x)));
                              setEditingIdx(null);
                            }}
                          >
                            Save
                          </button>
                        </div>
                      </div>
                    ) : (
                      <p
                        style={{
                          margin: 0,
                          fontSize: 14.5,
                          lineHeight: 1.58,
                          color: 'var(--ink)',
                          cursor: 'text',
                          whiteSpace: 'pre-line',
                        }}
                        onClick={() => {
                          setEditingIdx(idx);
                          setEditBuffer(p);
                        }}
                      >
                        {renderHighlighted(p)}
                      </p>
                    )}
                  </div>
                );
              })}

              <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: 2 }}>
                <span className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                  {wordCount} words · ~{Math.max(12, Math.round(wordCount / 4.2))}s skim
                </span>
              </div>
            </div>

            {/* 3. Docked Optional CV Attachment Tray (Choose, Preview, Edit in CV Studio, or Detach) */}
            <div className="t-outreach-attach-tray" ref={attachWrapRef}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
                <TailoredIcon name="cv" size={18} />
                <div style={{ minWidth: 0 }}>
                  <div
                    style={{
                      fontWeight: 600,
                      fontSize: 13.5,
                      color: 'var(--ink)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {attachedCvLabel}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 2, flexWrap: 'wrap' }}>
                    {attachedCvScore !== null && (
                      <span
                        className="t-mono"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 4,
                          fontSize: 11.5,
                          fontWeight: 600,
                          color: attachedCvScore >= 75 ? 'var(--green)' : 'var(--ink)',
                        }}
                      >
                        {attachedCvScore >= 75 && <span className="t-signal-up" aria-hidden="true" />}
                        <span>{Math.round(attachedCvScore)}% Fit</span>
                      </span>
                    )}
                    <span style={{ fontSize: 12, color: 'var(--n500)' }}>
                      {selectedTailoredDoc
                        ? 'Tailored CV · Attached'
                        : selectedCvId === 'base'
                          ? 'Baseline Profile PDF · 0 cr'
                          : 'Optional — send pitch without CV'}
                    </span>
                    {!matchingJobCv && selectedCvId !== 'none' && displayJob.id > 0 && (
                      <button
                        type="button"
                        className="t-atelier-btn-ghost"
                        style={{ padding: '1px 6px', fontSize: 12, color: 'var(--dye)', fontWeight: 600 }}
                        onClick={() => openJobInStudio(displayJob)}
                      >
                        Tailor New CV ({isJobUnlocked(displayJob.id, 'cv') ? '0 cr' : '1 cr'}) →
                      </button>
                    )}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                {selectedCvId !== 'none' && (
                  <>
                    <button
                      type="button"
                      className="t-atelier-icon-btn"
                      title="Quick preview CV"
                      aria-label="Preview CV"
                      onClick={() => openCvPreview(selectedCvId)}
                    >
                      <TailoredIcon name="eye" size={14} />
                    </button>
                    <button
                      type="button"
                      className="t-atelier-btn-tonal"
                      title="Open selected CV inside CV Studio to edit"
                      onClick={() => {
                        if (selectedTailoredDoc) {
                          openDocInStudio(selectedTailoredDoc.doc_id);
                        } else {
                          setActiveStudioJob(displayJob);
                          navigateTo(`/studio?job_id=${displayJob.id}`);
                        }
                      }}
                    >
                      <TailoredIcon name="edit" size={13} />
                      <span>Edit in CV Studio</span>
                    </button>
                    <button
                      type="button"
                      className="t-atelier-icon-btn"
                      title="Remove CV attachment (send email only)"
                      aria-label="Detach CV"
                      onClick={() => {
                        setSelectedCvForJob(displayJob.id, 'none');
                        pushToast('Removed CV attachment — email will send as text pitch only.');
                      }}
                    >
                      <TailoredIcon name="close" size={12} />
                    </button>
                  </>
                )}
                <button
                  type="button"
                  className="t-atelier-btn-tonal"
                  onClick={() => setAttachMenuOpen((v) => !v)}
                >
                  <span>Choose CV</span>
                  <TailoredIcon name="chevronDown" size={11} />
                </button>
              </div>

              {attachMenuOpen && (
                <div className="t-outreach-attach-menu" role="menu" aria-label="Select CV to attach">
                  <div className="t-atelier-popover-label">Select Optional CV Attachment</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 220, overflowY: 'auto' }}>
                    {(() => {
                      const seenKeys = new Set<string>();
                      const uniqueDocs = tailoredDocs.filter((d) => {
                        const key = `${cleanCompanyName(d.company_name || '')}::${cleanTargetJobTitle(d.job_title || '')}`;
                        if (seenKeys.has(key)) return false;
                        seenKeys.add(key);
                        return true;
                      });
                      return uniqueDocs.map((doc) => {
                        const active = selectedCvId === doc.doc_id;
                        return (
                          <div key={doc.doc_id} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                            <button
                              type="button"
                              className={`t-atelier-menu-row ${active ? 't-atelier-menu-row--active' : ''}`}
                              style={{ flex: 1 }}
                              onClick={() => {
                                setSelectedCvForJob(displayJob.id, doc.doc_id);
                                setAttachMenuOpen(false);
                              }}
                            >
                              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {cleanCompanyName(doc.company_name || company)} · {cleanTargetJobTitle(doc.job_title || role)}
                              </span>
                              <span className="t-mono" style={{ fontSize: 11, opacity: 0.8 }}>
                                {Math.round(doc.fit_score ?? 92)}%
                              </span>
                            </button>
                            <button
                              type="button"
                              className="t-atelier-icon-btn"
                              title="Preview CV"
                              onClick={() => {
                                setAttachMenuOpen(false);
                                openCvPreview(doc.doc_id);
                              }}
                            >
                              <TailoredIcon name="eye" size={13} />
                            </button>
                          </div>
                        );
                      });
                    })()}

                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <button
                        type="button"
                        className={`t-atelier-menu-row ${selectedCvId === 'base' ? 't-atelier-menu-row--active' : ''}`}
                        style={{ flex: 1 }}
                        onClick={() => {
                          setSelectedCvForJob(displayJob.id, 'base');
                          setAttachMenuOpen(false);
                        }}
                      >
                        <span>{activePersona?.target_title || 'Master'} · Base CV</span>
                        <span className="t-mono" style={{ fontSize: 11, opacity: 0.75 }}>0 cr</span>
                      </button>
                      <button
                        type="button"
                        className="t-atelier-icon-btn"
                        title="Preview Base CV"
                        onClick={() => {
                          setAttachMenuOpen(false);
                          openCvPreview('base');
                        }}
                      >
                        <TailoredIcon name="eye" size={13} />
                      </button>
                    </div>

                    <button
                      type="button"
                      className={`t-atelier-menu-row ${selectedCvId === 'none' ? 't-atelier-menu-row--active' : ''}`}
                      onClick={() => {
                        setSelectedCvForJob(displayJob.id, 'none');
                        setAttachMenuOpen(false);
                      }}
                    >
                      <span>No CV attachment (email only)</span>
                    </button>
                  </div>

                  <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(26, 20, 18, 0.08)' }}>
                    <button
                      type="button"
                      className="t-atelier-btn-primary"
                      style={{ width: '100%', justifyContent: 'center' }}
                      onClick={() => {
                        setAttachMenuOpen(false);
                        openJobInStudio(displayJob);
                      }}
                    >
                      <span>Tailor New CV for {company} ({isJobUnlocked(displayJob.id, 'cv') ? '0 cr' : '1 cr'})</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* 4. Bottom Action Bar — Primary Action = Send Email Directly (CV Optional) */}
            <div className="t-outreach-footer">
              <label
                htmlFor="cl-mark-applied"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 7,
                  fontSize: 12.5,
                  color: 'var(--n700)',
                  cursor: 'pointer',
                }}
              >
                <input
                  id="cl-mark-applied"
                  type="checkbox"
                  checked={markAppliedOnSend}
                  onChange={(e) => setMarkAppliedOnSend(e.target.checked)}
                />
                <span>Mark Applied in Pipeline</span>
              </label>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8, position: 'relative' }} ref={sendWrapRef}>
                <button type="button" className="t-atelier-btn-tonal" onClick={handleCopyAll}>
                  <TailoredIcon name="copy" size={13} />
                  <span>Copy All</span>
                </button>

                <button type="button" className="t-atelier-btn-primary" onClick={handleSendViaGmail}>
                  <TailoredIcon name="send" size={13} color="var(--ink)" />
                  <span>{selectedCvId !== 'none' ? 'Send Email + CV' : 'Send Email'}</span>
                </button>
                <button
                  type="button"
                  className="t-atelier-btn-tonal"
                  style={{ padding: '7px 9px' }}
                  aria-label="More send options"
                  onClick={() => setSendMenuOpen((v) => !v)}
                >
                  <TailoredIcon name="chevronDown" size={12} />
                </button>

                {sendMenuOpen && (
                  <div className="t-popover" style={{ bottom: 44, right: 0, top: 'auto', width: 224, padding: 8 }}>
                    <button
                      type="button"
                      className="t-atelier-menu-row"
                      onClick={async () => {
                        await downloadAttachedCv();
                        window.location.href = `mailto:${encodeURIComponent(toEmail)}?subject=${encodeURIComponent(
                          subjectLine
                        )}&body=${encodeURIComponent(paragraphs.join('\n\n'))}`;
                        commitOutreachToWorkspace();
                        setSendMenuOpen(false);
                      }}
                    >
                      Default Mail Client (mailto)
                    </button>
                    <button
                      type="button"
                      className="t-atelier-menu-row"
                      onClick={() => {
                        const blob = new Blob([`${subjectLine}\n\n${paragraphs.join('\n\n')}`], {
                          type: 'text/plain',
                        });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `Cover_Letter_${company.replace(/\s+/g, '_')}.txt`;
                        a.click();
                        URL.revokeObjectURL(url);
                        setSendMenuOpen(false);
                        pushToast('Downloaded cover letter text.');
                      }}
                    >
                      Download .txt Letter
                    </button>
                    {displayJob.url && (
                      <button
                        type="button"
                        className="t-atelier-menu-row"
                        onClick={() => {
                          window.open(displayJob.url, '_blank');
                          setSendMenuOpen(false);
                        }}
                      >
                        <span>Open Job Listing</span>
                        <TailoredIcon name="external" size={12} />
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

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
        groundedContextLabel={showBlankDropCanvas ? 'New Letter' : threadScope === 'workspace' ? 'All Workspace' : company}
        threadScope={threadScope}
        onChangeThreadScope={setThreadScope}
        enableWorkspaceMentions
        messages={messages}
        isStreaming={isStreaming}
        focusedAnchor={focusedAnchor}
        onClearFocusedAnchor={() => setFocusedAnchor(null)}
        onSendMessage={handleSendCoachMessage}
        onStopStreaming={() => setIsStreaming(false)}
        onApplyProposal={applyProposal}
        onSkipProposal={(id) =>
          setMessages((prev) =>
            prev.map((m) => (m.proposal?.id === id ? { ...m, proposal: { ...m.proposal, status: 'skipped' } } : m))
          )
        }
        onUndoProposal={handleUndoProposal}
        onRefineProposal={(id, instr) => {
          setMessages((prev) =>
            prev.map((m) => {
              if (m.proposal?.id !== id) return m;
              const refinedText = instr.toLowerCase().includes('short')
                ? `${m.proposal.newText.split(',')[0]}.`
                : `${m.proposal.newText.replace(/\.$/, '')} (${instr.trim()}).`;
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
        }}
        onHoverProposal={setHighlightedAnchor}
        onLocateAnchor={(id) => {
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
          setMessages((prev) =>
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
              id: `cl_rst_${Date.now()}`,
              role: 'assistant',
              text: showBlankDropCanvas
                ? 'Ready for a fresh tailored letter. Drop anything on the left or ask me about @Saved CVs.'
                : `Clean thread ready for ${company}. Ask to refine copy, list @Saved CVs, or check @Pipeline.`,
            },
          ])
        }
        starterPrompts={
          showBlankDropCanvas
            ? ['Show my available CVs', 'Check pipeline follow-ups', 'Show matching jobs']
            : ['Sharpen opening', 'Show my available CVs', 'Check pipeline follow-ups']
        }
        modes={['Tone Refine', 'Condense', 'Hook Swap', 'Check Claim']}
        mode={coachMode}
        onChangeMode={setCoachMode}
      />
    </div>
  );

  const historyPanel = (
    <aside
      className={`t-cl-history-rail ${!historyOpen ? 't-cl-history-rail--collapsed' : ''}`}
      aria-label="Tailored Cover Letters History"
    >
      <div className="t-cl-history-head">
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: historyOpen ? 'space-between' : 'center',
            gap: 8,
          }}
        >
          {historyOpen && (
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
              Cover Letters
            </span>
          )}
          <button
            type="button"
            className="t-atelier-icon-btn"
            style={{ width: 26, height: 26, color: 'var(--chalk)', opacity: 0.78 }}
            title={historyOpen ? 'Collapse Cover Letters rail' : 'Expand Cover Letters rail'}
            aria-label={historyOpen ? 'Collapse Cover Letters rail' : 'Expand Cover Letters rail'}
            aria-expanded={historyOpen}
            onClick={() => setHistoryOpen((v) => !v)}
          >
            <TailoredIcon name={historyOpen ? 'collapse' : 'expand'} size={14} color="var(--chalk)" />
          </button>
        </div>

        {historyOpen ? (
          <button
            type="button"
            className="t-atelier-btn-primary"
            style={{ width: '100%', justifyContent: 'center', padding: '7px 12px', whiteSpace: 'nowrap' }}
            onClick={openNewBlankLetter}
          >
            <TailoredIcon name="plus" size={13} color="var(--ink)" />
            <span>New Letter</span>
          </button>
        ) : (
          <button
            type="button"
            className="t-cl-history-mini-btn"
            title="New Letter"
            aria-label="New Letter"
            onClick={openNewBlankLetter}
          >
            <TailoredIcon name="plus" size={14} color="var(--ink)" />
          </button>
        )}
      </div>

      {historyOpen ? (
        <>
          <div className="t-cl-history-sub">HISTORY · {historyLetters.length}</div>

          <div ref={historyListRef} className="t-cl-history-list">
            {isBlankMode && (
              <div className="t-cl-history-item t-cl-history-item--active">
                <div style={{ fontWeight: 600, fontSize: 12.5, color: 'var(--kraft)' }}>
                  Untitled New Letter
                </div>
                <div style={{ fontSize: 11.5, color: 'rgba(229, 224, 218, 0.65)' }}>
                  Drop target on canvas…
                </div>
              </div>
            )}

            {historyLetters.map((item) => {
              const isCurrent = !isBlankMode && activeLetter?.doc_id === item.doc_id;
              const itemCo = cleanCompanyName(item.company_name || 'Target Organization');
              const itemRole = cleanTargetJobTitle(item.job_title || 'Tailored Outreach');
              return (
                <div
                  key={item.doc_id}
                  role="button"
                  tabIndex={0}
                  className={`t-cl-history-item ${isCurrent ? 't-cl-history-item--active' : ''}`}
                  onClick={() => openHistoryLetter(item)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      openHistoryLetter(item);
                    }
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
                    <span
                      style={{
                        fontWeight: 600,
                        fontSize: 12.8,
                        color: 'var(--chalk)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {itemCo}
                    </span>
                    <button
                      type="button"
                      className="t-cl-history-del"
                      title="Delete letter"
                      aria-label={`Delete ${itemCo} letter`}
                      onClick={(e) => {
                        e.stopPropagation();
                        const remaining = historyLetters.filter((x) => x.doc_id !== item.doc_id);
                        deleteCoverLetter(item.doc_id);
                        if (isCurrent) {
                          if (remaining[0]) {
                            openHistoryLetter(remaining[0]);
                          } else {
                            openNewBlankLetter();
                          }
                        }
                      }}
                    >
                      <TailoredIcon name="trash" size={11} />
                    </button>
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
                    {itemRole}
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
                    <span>{formatShortHistoryDate(item.created_at)}</span>
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--kraft)' }}>
                      {item.recipient_email ? item.recipient_email.split('@')[0] : item.source_label || 'Saved'}
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
          onClick={() => setHistoryOpen(true)}
          title="Expand Cover Letters history"
        >
          <span className="t-cl-history-collapsed-count">{historyLetters.length}</span>
          <span className="t-cl-history-collapsed-label">History</span>
        </div>
      )}
    </aside>
  );

  return (
    <div className="t-studio-shell t-cv-studio-v2">
      {/* FOCUSED SOLID TOP BAR */}
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
              setBriefPopoverOpen(false);
            }}
          >
            <span>{activePersona?.target_title.split(' ')[0] || 'Persona'}</span>
            <span className="t-mono" style={{ fontSize: 11.5, color: 'var(--kraft)' }}>{activeRegionalPhone}</span>
            <TailoredIcon name="chevronDown" size={12} color="var(--chalk)" />
          </button>

          <span style={{ color: 'var(--n500)', fontSize: 13 }}>/</span>

          <span
            style={{
              fontSize: 13,
              fontWeight: 500,
              color: showBlankDropCanvas ? 'var(--kraft)' : 'var(--chalk)',
              maxWidth: 'clamp(120px, 18vw, 260px)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {showBlankDropCanvas ? 'New Blank Letter' : `${company} · ${role}`}
          </span>

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
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, position: 'relative' }}>
          {!showBlankDropCanvas && (
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
          )}

          {!showBlankDropCanvas && (
            <button
              type="button"
              className="t-atelier-topbar-ghost"
              onClick={() => {
                setBriefPopoverOpen((v) => !v);
                setIdentityMenuOpen(false);
              }}
            >
              <TailoredIcon name="sliders" size={13} color="var(--chalk)" />
              <span>Brief &amp; Tone</span>
            </button>
          )}

          {briefPopoverOpen && !showBlankDropCanvas && (
            <div className="t-popover" style={{ top: 44, right: 0, width: 320 }}>
              <div className="t-atelier-popover-label">Voice &amp; Tone</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
                {(['Executive', 'Technical', 'Impact-Driven', 'Founder-Direct'] as CoverLetterTone[]).map((t) => (
                  <button
                    key={t}
                    type="button"
                    className={`t-atelier-popover-chip ${tone === t ? 't-atelier-popover-chip--active' : ''}`}
                    onClick={() => setTone(t)}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <div className="t-atelier-popover-label">Target Length</div>
              <div style={{ display: 'flex', gap: 6, marginBottom: 14 }}>
                {(['compact', 'balanced'] as const).map((len) => (
                  <button
                    key={len}
                    type="button"
                    className={`t-atelier-popover-chip ${lengthMode === len ? 't-atelier-popover-chip--active' : ''}`}
                    onClick={() => setLengthMode(len)}
                  >
                    {len === 'compact' ? '~180 words' : '~250 words'}
                  </button>
                ))}
              </div>
              <div className="t-atelier-popover-label">Opening Hook Emphasis</div>
              <input
                className="t-atelier-inline-input"
                style={{ marginBottom: 14 }}
                value={hookFocus}
                onChange={(e) => setHookFocus(e.target.value)}
              />
              <button
                type="button"
                className="t-atelier-btn-primary"
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={handleGenerateFromBrief}
              >
                <span>Re-Generate Draft</span>
                <span className="t-mono" style={{ fontSize: 11.5, opacity: 0.8 }}>
                  ({isJobUnlocked(displayJob.id, 'cl') ? '0 cr' : '1 cr'})
                </span>
              </button>
            </div>
          )}
        </div>
      </header>

      {/* ATELIER WORKSPACE STAGE WITH FRENCH-CURVE BACKDROP + HISTORY RAIL */}
      <div className="t-atelier-stage" style={{ flexDirection: 'row' }}>
        <AtelierFrenchCurveBackdrop />
        {historyPanel}
        <div style={{ position: 'relative', zIndex: 1, flex: 1, minWidth: 0, minHeight: 0, display: 'flex' }}>
          {coachCollapsed ? (
            <div style={{ position: 'relative', zIndex: 1, flex: 1, minHeight: 0, overflow: 'hidden', display: 'flex' }}>
              {letterPane}
            </div>
          ) : (
            <ResizableSplitPane
              storageKey={swapSides ? 'cl_studio_v4_swapped' : 'cl_studio_v4_main'}
              defaultLeftPct={swapSides ? 36 : 64}
              minLeftPx={swapSides ? 336 : 420}
              minRightPx={swapSides ? 420 : 336}
              left={swapSides ? coachPane : letterPane}
              right={swapSides ? letterPane : coachPane}
            />
          )}
        </div>
      </div>
    </div>
  );
};
