import {
  cleanCompanyName,
  cleanTargetJobTitle,
  stripLeadingRoleFromBioClient,
  type CvFitDetail,
  type CvFitSummary,
} from '../services/cvFitApi';
import type { UserProfilePayload } from '../services/profileApi';
import { parseLatexToCv, type ParsedLatexCv } from './latexLiveSync';

export interface BuildCvSnapshotParams {
  profile: UserProfilePayload;
  personaId?: string;
  activeRegionalPhone: '+20' | '+966' | '+971';
  docDetail?: CvFitDetail | null;
  docSummary?: CvFitSummary | null;
}

/**
 * Resolves a complete, preview-ready ParsedLatexCv document from a saved CV summary/detail or base persona.
 */
export function buildParsedCvSnapshot(params: BuildCvSnapshotParams): ParsedLatexCv {
  const { profile, personaId, activeRegionalPhone, docDetail, docSummary } = params;
  const resolvedPersonaId = docDetail?.persona_id || docSummary?.persona_id || personaId;
  const persona =
    profile.career_personas.find((p) => p.persona_id === resolvedPersonaId) ||
    profile.career_personas.find((p) => p.is_primary) ||
    profile.career_personas[0];

  const phoneDisplay =
    activeRegionalPhone === '+966'
      ? '+966 54 391 8820'
      : activeRegionalPhone === '+971'
        ? '+971 50 987 6543'
        : '+20 100 482 9102';

  const locationLabel =
    docDetail?.location ||
    docSummary?.location ||
    (activeRegionalPhone === '+966'
      ? 'Riyadh, KSA'
      : activeRegionalPhone === '+971'
        ? 'Dubai, UAE'
        : 'Cairo, Egypt');

  const stripped = stripLeadingRoleFromBioClient(persona?.summary_bio || '');
  const summaryText =
    (stripped ? stripped.charAt(0).toUpperCase() + stripped.slice(1) : '') ||
    'Senior Data Scientist & AI Systems Engineer delivering production regression engines, FastAPI inference pipelines, and scalable analytics.';

  const diffBullets = docDetail?.bullet_diffs?.map((b) => b.tailored_bullet).filter(Boolean) || [];
  const baseBullets =
    persona?.experience_highlights.map((e) => e.achievements[0]).filter(Boolean) || [];
  const bullets = diffBullets.length > 0 ? diffBullets : baseBullets;

  const skillBuckets = persona?.skills_and_tools;
  const parsedSkills = docDetail?.parsed_skills || docSummary?.parsed_skills || [];
  const mergedCore = Array.from(
    new Set([...(skillBuckets?.core_skills || []), ...parsedSkills].filter(Boolean))
  );

  const skillRows = skillBuckets
    ? [
        ...(mergedCore.length > 0
          ? [{ label: 'Core Disciplines', value: mergedCore.slice(0, 8).join(' · ') }]
          : []),
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

  const exps = persona?.experience_highlights || [];
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

  const targetTitle =
    docDetail?.job_title || docSummary?.job_title
      ? cleanTargetJobTitle(docDetail?.job_title || docSummary?.job_title)
      : persona?.target_title || 'Candidate';
  const targetCo =
    docDetail?.company_name || docSummary?.company_name
      ? ` · Targeted for ${cleanCompanyName(docDetail?.company_name || docSummary?.company_name)}`
      : '';

  const fallback: ParsedLatexCv = {
    fullName: profile.personal_info.full_name,
    headlineLine: `${targetTitle}${targetCo} · ${locationLabel}`,
    contactLine: `${phoneDisplay} · ${profile.personal_info.primary_email} · ${(profile.personal_info.links.linkedin || 'linkedin.com/in/candidate').replace('https://', '')} · ${(profile.personal_info.links.github || 'github.com/candidate').replace('https://', '')}`,
    summary: summaryText,
    skillRows,
    experiences: mappedExps,
    flatBullets: bullets,
    projects: (persona?.featured_projects || []).map((pr) => ({
      name: pr.name,
      tech: pr.tech_stack.join(', '),
      summary: pr.summary,
    })),
    education: (profile.education || []).map((ed) => ({
      title: ed.degree,
      subtitle: `${ed.institution}${ed.graduation_year ? ` · ${ed.graduation_year}` : ''}`,
    })),
    certs: (persona?.certifications || [])
      .slice(0, 2)
      .map((c) => `${c.name} · ${c.issuer}`),
    languages: (profile.languages || [])
      .map((l) => `${l.language} (${l.proficiency})`)
      .join(', '),
    warnings: [],
  };

  const latexSource = docDetail?.tailored_latex_content || docDetail?.base_latex_content;
  if (latexSource && latexSource.includes('\\section')) {
    return parseLatexToCv(latexSource, fallback);
  }
  return fallback;
}
