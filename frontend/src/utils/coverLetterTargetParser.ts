import { extractEmail } from '../services/jobsApi';

export type DropSourceKind = 'link' | 'screenshot' | 'jd' | 'brief';

export interface ParsedCoverLetterTarget {
  sourceKind: DropSourceKind;
  sourceLabel: string;
  company: string;
  role: string;
  location: string;
  recipientEmail: string;
  url: string;
  skills: string[];
  emphasis: string;
  summaryDescription: string;
}

const KNOWN_SKILLS = [
  'Python',
  'FastAPI',
  'PyTorch',
  'TensorFlow',
  'SQL',
  'PostgreSQL',
  'Docker',
  'Kubernetes',
  'AWS',
  'GCP',
  'RAG',
  'LLMs',
  'NLP',
  'MLOps',
  'Ray',
  'Kafka',
  'Airflow',
  'React',
  'TypeScript',
  'Node.js',
  'Pandas',
  'XGBoost',
  'Scikit-Learn',
  'A/B Testing',
  'Power BI',
  'Tableau',
  'Redis',
  'GraphQL',
  'Microservices',
  'CI/CD',
  'Computer Vision',
  'Deep Learning',
];

const LOCATION_PATTERNS: Array<{ re: RegExp; label: string }> = [
  { re: /\briyadh\b/i, label: 'Riyadh, Saudi Arabia' },
  { re: /\bdubai\b/i, label: 'Dubai, UAE' },
  { re: /\babu dhabi\b/i, label: 'Abu Dhabi, UAE' },
  { re: /\bcairo\b/i, label: 'Cairo, Egypt' },
  { re: /\balexandria\b/i, label: 'Alexandria, Egypt' },
  { re: /\bjeddah\b/i, label: 'Jeddah, Saudi Arabia' },
  { re: /\bksa\b|\bsaudi\b/i, label: 'Saudi Arabia' },
  { re: /\buae\b/i, label: 'UAE' },
  { re: /\bremote\b/i, label: 'Remote (MENA / Global)' },
  { re: /\blondon\b/i, label: 'London, UK' },
];

function toTitleCaseClean(s: string): string {
  return s
    .trim()
    .replace(/\s+/g, ' ')
    .replace(/^[-–—,:;|]+|[-–—,:;|]+$/g, '')
    .trim();
}

function detectSkillsFromText(text: string): string[] {
  const lower = text.toLowerCase();
  const matched: string[] = [];
  for (const sk of KNOWN_SKILLS) {
    const escaped = sk.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp(`(?:^|[^a-z0-9])${escaped}(?:$|[^a-z0-9])`, 'i');
    if (re.test(lower)) matched.push(sk);
  }
  return matched.length > 0 ? matched : ['Python', 'FastAPI', 'PostgreSQL', 'Docker'];
}

function inferFromUrl(urlStr: string): { company?: string; role?: string } {
  try {
    const u = new URL(urlStr);
    const hostParts = u.hostname.replace(/^www\./, '').split('.');
    const rawHost = hostParts[0] || '';
    const isBoard = ['linkedin', 'wuzzuf', 'indeed', 'glassdoor', 'greenhouse', 'lever'].includes(rawHost.toLowerCase());
    const pathTokens = u.pathname
      .split('/')
      .filter((t) => t && !/^\d+$/.test(t) && !['jobs', 'view', 'p', 'careers', 'apply', 'feed', 'update', 'posts'].includes(t.toLowerCase()));

    const company = !isBoard && rawHost
      ? rawHost.charAt(0).toUpperCase() + rawHost.slice(1)
      : pathTokens[0]
        ? pathTokens[0].replace(/[-_]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
        : undefined;
    const role = pathTokens[1]
      ? pathTokens[1].replace(/[-_]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
      : undefined;
    return { company, role };
  } catch {
    return {};
  }
}

export function parseCoverLetterDropInput(params: {
  rawText: string;
  hasScreenshot?: boolean;
  screenshotName?: string;
}): ParsedCoverLetterTarget {
  const trimmed = params.rawText.trim();
  const hasScreenshot = Boolean(params.hasScreenshot);
  const urlMatch = trimmed.match(/https?:\/\/[^\s]+/i);
  const url = urlMatch ? urlMatch[0] : '';
  const isPureLink = Boolean(url) && trimmed.replace(url, '').trim().length < 25;

  const looksLikeJd =
    trimmed.split('\n').length >= 3 ||
    trimmed.length > 180 ||
    /\b(responsibilities|requirements|qualifications|we are seeking|we are looking for|experience with)\b/i.test(trimmed);

  const sourceKind: DropSourceKind = hasScreenshot
    ? 'screenshot'
    : isPureLink
      ? 'link'
      : looksLikeJd
        ? 'jd'
        : 'brief';

  const sourceLabel =
    sourceKind === 'screenshot'
      ? `Screenshot OCR${params.screenshotName ? ` (${params.screenshotName})` : ''}`
      : sourceKind === 'link'
        ? 'Job Link'
        : sourceKind === 'jd'
          ? 'Pasted JD'
          : 'Custom Brief';

  const workingText =
    trimmed ||
    (hasScreenshot
      ? 'Senior AI Systems Engineer at Careem in Dubai · Hybrid · hiring@careem.com · Python, FastAPI, Docker, PyTorch, LLMs'
      : 'AI & Data Systems Engineer');

  const recipientEmail = extractEmail(workingText) || '';

  // Extract explicit emphasis instructions ("emphasize ...", "highlight ...", "focus on ...")
  const emphasisMatch = workingText.match(
    /(?:emphasize|highlight|focus on|stress|mention|lean into)\s+([^.;\n]+?)(?=(?:\s*(?:,|;|—|\band\s+send|\bsend\s+to|\bemail\b|$)))/i
  );
  const emphasis = emphasisMatch ? toTitleCaseClean(emphasisMatch[1]) : '';

  // Location extraction
  let location = 'Cairo / MENA (Hybrid)';
  for (const loc of LOCATION_PATTERNS) {
    if (loc.re.test(workingText)) {
      location = loc.label;
      break;
    }
  }

  // URL hints
  const urlHints = url ? inferFromUrl(url) : {};

  // Company extraction (prefer explicit label or `at <Company>` / `@ <Company>` before broader prepositions)
  let company = urlHints.company || '';
  const explicitCompanyMatch = workingText.match(/\b(?:company|organization|employer)\s*:\s*([^\n,;|—]+)/i);
  const leadingDashMatch = workingText.match(
    /^([A-Z][A-Za-z0-9&._-]*(?:\s+[A-Z][A-Za-z0-9&._-]*){0,2})\s*[—–-]\s*([A-Za-z][A-Za-z0-9/&+ -]{3,52}?)(?=[,.;\n]|$)/
  );
  const strongAtCompanyMatch = workingText.match(
    /(?:^|\s)(?:at|@)\s+([A-Z][A-Za-z0-9&._-]*(?:\s+[A-Z][A-Za-z0-9&._-]*){0,2}?)(?=\s+(?:in|on|with|using|—|-|,|;|to\b|send\b|emphasiz|highlight|focus|·)|[.,;!\n]|$)/
  );
  const weakForCompanyMatch = workingText.match(
    /\b(?:for|with|joining)\s+([A-Z][A-Za-z0-9&._-]*(?:\s+[A-Z][A-Za-z0-9&._-]*){0,2}?)(?=\s+(?:role|position|in|on|with|using|—|-|,|;|to\b|send\b|emphasiz|highlight|focus|·)|[.,;!\n]|$)/
  );
  if (explicitCompanyMatch) {
    company = toTitleCaseClean(explicitCompanyMatch[1]);
  } else if (strongAtCompanyMatch) {
    const candidate = toTitleCaseClean(strongAtCompanyMatch[1]);
    if (!/^(Egypt|Riyadh|Dubai|Cairo|KSA|UAE|Remote|Hybrid)$/i.test(candidate)) {
      company = candidate;
    }
  } else if (leadingDashMatch) {
    const candidate = toTitleCaseClean(leadingDashMatch[1]);
    if (!/^(Egypt|Riyadh|Dubai|Cairo|KSA|UAE|Remote|Hybrid|Senior|Junior|Lead|Staff|Principal)$/i.test(candidate)) {
      company = candidate;
    }
  } else if (weakForCompanyMatch) {
    const candidate = toTitleCaseClean(weakForCompanyMatch[1]);
    if (!/^(Egypt|Riyadh|Dubai|Cairo|KSA|UAE|Remote|Hybrid)$/i.test(candidate)) {
      company = candidate;
    }
  }
  if (!company) {
    company = hasScreenshot ? 'Careem' : 'Target Team';
  }

  // Role extraction
  let role = urlHints.role || '';
  const explicitRoleMatch = workingText.match(/\b(?:role|title|position)\s*:\s*([^\n,;|—]+)/i);
  const leadRoleMatch = workingText.match(
    /(?:applying for (?:a |an )?|for (?:a |an )?)?([A-Za-z][A-Za-z0-9/&+ -]{3,48}?)\s+(?:role\s+|position\s+)?(?:at|@)\s+/i
  );
  if (explicitRoleMatch) {
    role = toTitleCaseClean(explicitRoleMatch[1]);
  } else if (leadRoleMatch) {
    let rawRole = toTitleCaseClean(leadRoleMatch[1]);
    rawRole = rawRole.replace(/^(?:screenshot ocr capture|hiring|seeking|looking for|need)\s*(?::|a|an)?\s*/i, '');
    if (rawRole.length >= 3 && rawRole.length <= 54) {
      role = rawRole;
    }
  } else if (leadingDashMatch && !strongAtCompanyMatch) {
    const dashRole = toTitleCaseClean(leadingDashMatch[2]);
    if (dashRole.length >= 3 && dashRole.length <= 54) {
      role = dashRole;
    }
  }
  if (!role) {
    const firstChunk = workingText.split(/[.\n—|]/)[0] || '';
    role =
      firstChunk.length > 4 && firstChunk.length <= 52 && !/^https?:\/\//i.test(firstChunk)
        ? toTitleCaseClean(firstChunk)
        : 'Senior AI & Data Engineer';
  }

  const skills = detectSkillsFromText(workingText);

  const summaryDescription =
    sourceKind === 'jd'
      ? workingText
      : `${role} at ${company} (${location}). Focus stack: ${skills.join(', ')}.${
          emphasis ? ` Key emphasis requested: ${emphasis}.` : ''
        }${url ? ` Source link: ${url}` : ''}`;

  return {
    sourceKind,
    sourceLabel,
    company,
    role,
    location,
    recipientEmail,
    url,
    skills,
    emphasis,
    summaryDescription,
  };
}

function formatEmphasisPhrase(phrase: string): string {
  const s = phrase.trim();
  if (!s) return '';
  // Preserve acronyms / camelCase product tokens like FastAPI, PyTorch, SQL, MLOps
  if (/^(?:[A-Z]{2,}|[A-Z][a-z]+[A-Z])/.test(s)) return s;
  return s.charAt(0).toLowerCase() + s.slice(1);
}

function trimAtWordBoundary(text: string, maxChars = 155): string {
  const clean = text.trim();
  if (clean.length <= maxChars) return clean.replace(/[.,;:\s]+$/, '');
  const sub = clean.slice(0, maxChars);
  const lastSpace = sub.lastIndexOf(' ');
  const clipped = lastSpace > 40 ? sub.slice(0, lastSpace) : sub;
  return clipped.replace(/[.,;:\s]+$/, '');
}

export function composeTailoredOutreachDraft(params: {
  target: ParsedCoverLetterTarget;
  fullName: string;
  phoneDisplay: string;
  primaryCompany: string;
  primarySummary: string;
  tone: string;
  entryMode: 'pitch' | 'letter' | 'followup';
}): { subjectLine: string; paragraphs: string[] } {
  const { target, fullName, phoneDisplay, primaryCompany, primarySummary, tone, entryMode } = params;
  const topSkills = target.skills.slice(0, 3).join(', ') || 'Python, FastAPI, Docker';
  const emphasisPhrase = formatEmphasisPhrase(target.emphasis);
  const focusClause = emphasisPhrase ? `, with particular focus on ${emphasisPhrase}` : '';

  if (entryMode === 'followup') {
    return {
      subjectLine: `Following up: ${target.role} — ${fullName}`,
      paragraphs: [
        `Hi ${target.company} Hiring Team,`,
        `Following up briefly on my ${target.role} application${focusClause}. Having delivered production ${topSkills} architectures at ${primaryCompany}, I'd welcome a short technical conversation this week.`,
        `Best,\n${fullName} · ${phoneDisplay}`,
      ],
    };
  }

  const greeting =
    tone === 'Founder-Direct' ? `Hi ${target.company} Team,` : `Dear ${target.company} Hiring Team,`;

  const opening =
    tone === 'Founder-Direct'
      ? `Your ${target.role} charter at ${target.company} maps directly to the production ${topSkills} systems I have engineered at ${primaryCompany}${focusClause}.`
      : tone === 'Executive'
        ? `I bring hands-on engineering ownership across ${topSkills} aligned with ${target.company}'s ${target.role} priorities${focusClause}.`
        : `Having built and scaled production ${topSkills} services at ${primaryCompany}, I can contribute immediately to ${target.company}'s ${target.role} roadmap${focusClause}.`;

  const proofBody = target.emphasis
    ? `Specifically regarding ${target.emphasis}, my background as a ${trimAtWordBoundary(
        primarySummary,
        155
      )} directly translates into reliable production throughput and maintainable service APIs.`
    : `At ${primaryCompany}, I delivered end-to-end modeling, low-latency service orchestration, and reliable production deployments verified across regional workloads.`;

  const closing = `My tailored CV is attached for reference—I'd welcome the chance to connect.`;

  return {
    subjectLine: `Application: ${target.role} (${target.company}) — ${fullName}`,
    paragraphs: [greeting, opening, proofBody, closing, `Best,\n${fullName} · ${phoneDisplay}`],
  };
}
