import type { JobItem } from '../services/jobsApi';
import type { CareerPersona, UserProfilePayload } from '../services/profileApi';

export interface FitPillarScore {
  key: string;
  label: string;
  weight: number; // Brand Book 9 pillars summing to 100
  score: number;
  detail: string;
}

export interface TailoringOpportunity {
  id: string;
  gapLabel: string;
  bridgeStrategy: string;
  recommendedBulletHint: string;
}

export interface JobFitAnalysis {
  overallScore: number;
  tier: 'strong' | 'partial' | 'low';
  tierLabel: string;
  personaId: string;
  personaTitle: string;
  whyMatched: string;
  matchedSkills: string[];
  missingSkills: string[];
  pillars: FitPillarScore[];
  tailoringOpportunities: TailoringOpportunity[];
}

const SKILL_ALIASES: Record<string, string[]> = {
  'deep learning': ['pytorch', 'tensorflow', 'neural', 'transformers'],
  pytorch: ['deep learning', 'ml', 'ai'],
  fastapi: ['python', 'api', 'rest', 'backend', 'microservices'],
  docker: ['aws', 'ecs', 'kubernetes', 'containers', 'devops'],
  kubernetes: ['docker', 'ecs', 'cloud'],
  aws: ['docker', 'cloud', 'ecs', 'gcp'],
  sql: ['postgresql', 'postgres', 'mysql', 'analytics'],
  postgresql: ['sql', 'postgres', 'databases'],
  mlops: ['docker', 'mlflow', 'ray', 'airflow', 'ci/cd'],
};

function collectPersonaSkills(persona: CareerPersona): string[] {
  const s = persona.skills_and_tools;
  return [
    ...(s.core_skills || []),
    ...(s.programming_languages || []),
    ...(s.frameworks_and_libraries || []),
    ...(s.tools_and_platforms || []),
  ];
}

function hasSkillMatch(req: string, candidateSkillsLower: string[]): boolean {
  const low = req.toLowerCase().trim();
  if (candidateSkillsLower.some((c) => c === low || c.includes(low) || low.includes(c))) {
    return true;
  }
  const aliases = SKILL_ALIASES[low] || [];
  return aliases.some((al) => candidateSkillsLower.some((c) => c.includes(al)));
}

export function computeNinePillarFit(
  job: JobItem,
  persona: CareerPersona,
  profile: UserProfilePayload
): JobFitAnalysis {
  const personaSkills = collectPersonaSkills(persona);
  const candidateLower = personaSkills.map((s) => s.toLowerCase());
  const required = job.parsed_skills?.length ? job.parsed_skills : ['Python', 'SQL'];

  const matchedSkills: string[] = [];
  const missingSkills: string[] = [];
  for (const sk of required) {
    if (hasSkillMatch(sk, candidateLower)) matchedSkills.push(sk);
    else missingSkills.push(sk);
  }

  // 1. Core Stack (30%)
  const stackScore = Math.round((matchedSkills.length / Math.max(1, required.length)) * 100);

  // 2. Projects / Proof of Work (20%)
  const projectText = [
    ...persona.featured_projects.flatMap((p) => [p.name, p.summary, ...(p.tech_stack || [])]),
    ...persona.experience_highlights.flatMap((e) => [e.role, e.company, ...e.achievements]),
  ]
    .join(' ')
    .toLowerCase();
  const projectHits = required.filter((s) => projectText.includes(s.toLowerCase())).length;
  const projectScore = Math.min(
    100,
    Math.round(55 + (projectHits / Math.max(1, required.length)) * 45)
  );

  // 3. Seniority (10%) & 4. Experience (10%) — continuous proximity (no zero cutoff)
  const jdLow = `${job.title} ${job.raw_description}`.toLowerCase();
  const reqYearsMatch = jdLow.match(/(\d+)\s*\+?\s*years?/);
  const reqYears = reqYearsMatch ? parseInt(reqYearsMatch[1], 10) : 3;
  const candYears = persona.years_of_experience || 4;
  const expDiff = Math.max(0, reqYears - candYears);
  const experienceScore = Math.max(45, Math.round(100 - expDiff * 14));

  const titleLow = job.title.toLowerCase();
  const seniorityExpected = titleLow.includes('lead') || titleLow.includes('staff')
    ? 'lead'
    : titleLow.includes('senior')
      ? 'senior'
      : 'mid';
  const candSenLow = persona.seniority_level.toLowerCase();
  const seniorityScore = candSenLow.includes(seniorityExpected)
    ? 95
    : candSenLow.includes('senior') || candSenLow.includes('lead')
      ? 84
      : 68;

  // 5. Domain & Title Alignment (10%)
  const candidateTitles = [persona.target_title, ...(persona.alternative_titles || [])].map((t) =>
    t.toLowerCase()
  );
  const titleWords = titleLow.split(/[^a-z0-9]+/).filter((w) => w.length > 2);
  const titleOverlap = candidateTitles.some((ct) =>
    titleWords.some((w) => ct.includes(w))
  );
  const domainScore = titleOverlap ? 92 : 66;

  // 6. Persona Track Fit (5%)
  const personaScore = persona.is_primary ? 95 : 85;

  // 7. Education (5%)
  const educationScore = (profile.education?.length || 0) > 0 ? 96 : 70;

  // 8. Work Mode & Geography (5%)
  const locLow = (job.location || '').toLowerCase();
  const modeLow = (job.location_type || '').toLowerCase();
  const locMatch = profile.residence_and_mobility.target_locations.some(
    (tl) =>
      locLow.includes(tl.city.toLowerCase()) ||
      locLow.includes(tl.country.toLowerCase()) ||
      tl.work_modes.some((m) => m.toLowerCase() === modeLow)
  );
  const workModeScore = locMatch || modeLow === 'remote' ? 96 : 62;

  // 9. Language (5%)
  const languageScore = (profile.languages?.length || 0) > 0 ? 95 : 80;

  const pillars: FitPillarScore[] = [
    {
      key: 'stack',
      label: 'Core stack',
      weight: 30,
      score: stackScore,
      detail: `${matchedSkills.length}/${required.length} required skills verified`,
    },
    {
      key: 'projects',
      label: 'Projects',
      weight: 20,
      score: projectScore,
      detail: `${persona.featured_projects.length} projects & work outcomes`,
    },
    {
      key: 'seniority',
      label: 'Seniority',
      weight: 10,
      score: seniorityScore,
      detail: `Your ${persona.seniority_level} profile vs. ${seniorityExpected}`,
    },
    {
      key: 'experience',
      label: 'Experience',
      weight: 10,
      score: experienceScore,
      detail: `${candYears} yrs verified vs. ${reqYears}+ yrs asked (continuous)`,
    },
    {
      key: 'domain',
      label: 'Domain',
      weight: 10,
      score: domainScore,
      detail: titleOverlap ? `Aligned with ${persona.target_title}` : 'Adjacent role focus',
    },
    {
      key: 'persona',
      label: 'Persona',
      weight: 5,
      score: personaScore,
      detail: persona.target_title,
    },
    {
      key: 'education',
      label: 'Education',
      weight: 5,
      score: educationScore,
      detail: profile.education[0]?.degree || 'Academic profile recorded',
    },
    {
      key: 'mode',
      label: 'Work mode',
      weight: 5,
      score: workModeScore,
      detail: `${job.location_type || 'Hybrid'} · ${job.location}`,
    },
    {
      key: 'language',
      label: 'Language',
      weight: 5,
      score: languageScore,
      detail: (profile.languages || []).map((l) => l.language).join(', ') || 'English & Arabic',
    },
  ];

  // Blend deterministic pillars gently with backend fit_score when available so Radar consistency holds
  const computedWeighted = pillars.reduce((acc, p) => acc + (p.score * p.weight) / 100, 0);
  const overallScore =
    persona.is_primary && job.fit_score > 0
      ? Math.round((computedWeighted * 0.45 + job.fit_score * 0.55) * 10) / 10
      : Math.round(computedWeighted * 10) / 10;

  const tier: 'strong' | 'partial' | 'low' =
    overallScore >= 75 ? 'strong' : overallScore >= 50 ? 'partial' : 'low';
  const tierLabel =
    tier === 'strong' ? 'Strong Fit' : tier === 'partial' ? 'Partial Fit' : 'Low Fit';

  const topMatched = matchedSkills.slice(0, 3).join(', ') || 'core stack';
  const gapSummary =
    missingSkills.length > 0
      ? `bridge ${missingSkills[0]} via existing ${persona.experience_highlights[0]?.company || 'production'} systems`
      : 'full required stack covered';

  const whyMatched = `${Math.round(overallScore)}% on ${persona.target_title}: matched ${topMatched} + ${job.location_type || 'Hybrid'} alignment; ${gapSummary}.`;

  const tailoringOpportunities: TailoringOpportunity[] = missingSkills.map((sk, i) => ({
    id: `gap_${i}_${sk}`,
    gapLabel: `Role highlights "${sk}"`,
    bridgeStrategy: `Connect your verified ${matchedSkills[0] || 'Python/Docker'} achievements to ${sk}-equivalent production workflows without inventing unverified claims.`,
    recommendedBulletHint: `Add real system context around ${sk} in your ${persona.experience_highlights[0]?.company || 'latest role'} bullets.`,
  }));

  if (candYears < reqYears) {
    tailoringOpportunities.push({
      id: 'gap_years',
      gapLabel: `Posting lists ${reqYears}+ years (you list ${candYears} yrs)`,
      bridgeStrategy:
        'Lead with high-throughput ownership and measurable production impact rather than tenure length.',
      recommendedBulletHint: 'Front-load quantified scale metrics in Summary and Bullet #1.',
    });
  }

  return {
    overallScore,
    tier,
    tierLabel,
    personaId: persona.persona_id,
    personaTitle: persona.target_title,
    whyMatched,
    matchedSkills,
    missingSkills,
    pillars,
    tailoringOpportunities,
  };
}

export function evaluateAllPersonas(
  job: JobItem,
  profile: UserProfilePayload
): { best: JobFitAnalysis; all: JobFitAnalysis[] } {
  const list = profile.career_personas.map((p) => computeNinePillarFit(job, p, profile));
  list.sort((a, b) => b.overallScore - a.overallScore);
  return {
    best: list[0],
    all: list,
  };
}
