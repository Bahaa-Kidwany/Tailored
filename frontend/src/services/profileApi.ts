/**
 * Profile API Client for Tailored Master Identity & Multi-Persona System
 */

import { parseLatexCvClient } from '../utils/latexCvParser';

export interface ContactNumber {
  country_code: string;
  dial_code: string;
  phone_number: string;
  is_primary: boolean;
  label: string;
}

export interface PersonalInfo {
  full_name: string;
  primary_email: string;
  contact_numbers: ContactNumber[];
  links: Record<string, string>;
}

export interface TargetLocation {
  location_id: string;
  city: string;
  country: string;
  work_modes: string[];
  is_active_for_search: boolean;
}

export interface ResidenceAndMobility {
  current_residence: {
    city: string;
    country: string;
  };
  willing_to_relocate: boolean;
  target_locations: TargetLocation[];
}

export interface Education {
  institution: string;
  degree: string;
  field_of_study?: string;
  graduation_year?: number;
  grade_or_gpa?: string;
}

export interface LanguageProficiency {
  language: string;
  proficiency: string; // "Native" | "Fluent" | "Professional" | "Intermediate"
}

export interface SkillsAndTools {
  core_skills: string[];
  programming_languages: string[];
  frameworks_and_libraries: string[];
  tools_and_platforms: string[];
}

export interface ExperienceHighlight {
  company: string;
  role: string;
  start_date: string;
  end_date: string;
  location: string;
  achievements: string[];
}

export interface FeaturedProject {
  name: string;
  tech_stack: string[];
  summary: string;
  link?: string;
}

export interface Certification {
  name: string;
  issuer: string;
  issue_date?: string;
}

export interface CustomSectionItem {
  id: string;
  title: string;
  subtitle?: string;
  date?: string;
  location_or_link?: string;
  description?: string;
  bullet_points?: string[];
}

export interface CustomSection {
  id: string;
  section_title: string;
  section_type: 'items' | 'text';
  content_text?: string;
  items: CustomSectionItem[];
}

export interface CareerPersona {
  persona_id: string;
  target_title: string;
  alternative_titles: string[];
  is_primary: boolean;
  seniority_level: string; // "Entry-Level" | "Mid-Level" | "Senior" | "Lead"
  years_of_experience: number;
  summary_bio: string;
  skills_and_tools: SkillsAndTools;
  experience_highlights: ExperienceHighlight[];
  featured_projects: FeaturedProject[];
  certifications: Certification[];
}

export interface UserProfilePayload {
  version: string;
  personal_info: PersonalInfo;
  residence_and_mobility: ResidenceAndMobility;
  education: Education[];
  languages: LanguageProficiency[];
  career_personas: CareerPersona[];
  custom_sections?: CustomSection[];
}

export interface ProfileSummary {
  id: number;
  full_name: string;
  primary_email: string;
  current_city: string;
  current_country: string;
  willing_to_relocate: boolean;
  persona_count: number;
  primary_persona_title: string | null;
  created_at: string;
  updated_at: string;
}

export interface FullProfileResponse {
  id: number;
  profile: UserProfilePayload;
}

export interface DBStatusResponse {
  status: string;
  engine_type: 'postgresql' | 'sqlite';
  database_url_masked: string;
  counts: {
    profiles: number;
    personas: number;
    target_locations: number;
    contact_numbers: number;
  };
}

export interface ParseLatexApiResponse {
  success: boolean;
  message: string;
  stats: any;
  profile: Partial<UserProfilePayload>;
}

export function isProfileEmpty(profile: FullProfileResponse | null): boolean {
  if (!profile || !profile.profile) return true;
  const p = profile.profile;
  const hasName = Boolean(p.personal_info?.full_name?.trim());
  const personas = p.career_personas || [];
  const primaryPersona = personas.find((cp) => cp.is_primary) || personas[0];
  const hasTitle = Boolean(primaryPersona?.target_title?.trim());
  const hasSkills = Boolean(
    primaryPersona?.skills_and_tools?.core_skills?.length ||
      primaryPersona?.skills_and_tools?.programming_languages?.length
  );
  return !hasName || (!hasTitle && !hasSkills);
}

const API_BASE = 'http://127.0.0.1:8000/api/v1';
const LOCAL_STORAGE_KEY = 'tailored_profiles_fallback_v1';

// Sample Master Profile for 1-Click Prefill (Ahmed El-Sayed)
export const SAMPLE_PROFILE: UserProfilePayload = {
  version: '1.1.0',
  personal_info: {
    full_name: 'Ahmed El-Sayed',
    primary_email: 'ahmed.elsayed@example.com',
    contact_numbers: [
      {
        country_code: 'EG',
        dial_code: '+20',
        phone_number: '1001234567',
        is_primary: true,
        label: 'Egypt Mobile (Primary)',
      },
      {
        country_code: 'SA',
        dial_code: '+966',
        phone_number: '501234567',
        is_primary: false,
        label: 'Saudi Mobile (Zain SIM for Gulf HR)',
      },
    ],
    links: {
      linkedin: 'https://linkedin.com/in/ahmed-elsayed',
      github: 'https://github.com/ahmed-elsayed',
      portfolio: 'https://ahmedelsayed.dev',
    },
  },
  residence_and_mobility: {
    current_residence: {
      city: 'Cairo',
      country: 'Egypt',
    },
    willing_to_relocate: true,
    target_locations: [
      {
        location_id: 'loc_cairo',
        city: 'Cairo',
        country: 'Egypt',
        work_modes: ['Hybrid', 'Remote'],
        is_active_for_search: true,
      },
      {
        location_id: 'loc_riyadh',
        city: 'Riyadh',
        country: 'Saudi Arabia',
        work_modes: ['On-site', 'Hybrid', 'Remote'],
        is_active_for_search: true,
      },
      {
        location_id: 'loc_remote',
        city: 'Remote',
        country: 'Global',
        work_modes: ['Remote'],
        is_active_for_search: true,
      },
    ],
  },
  education: [
    {
      institution: 'Cairo University',
      degree: 'B.S. in Computer Science',
      field_of_study: 'Information Systems',
      graduation_year: 2021,
      grade_or_gpa: 'Very Good (Honor)',
    },
  ],
  languages: [
    { language: 'Arabic', proficiency: 'Native' },
    { language: 'English', proficiency: 'Professional Working' },
  ],
  career_personas: [
    {
      persona_id: 'data_scientist_track',
      target_title: 'Data Scientist',
      alternative_titles: ['Machine Learning Engineer', 'AI Engineer'],
      is_primary: true,
      seniority_level: 'Mid-Level',
      years_of_experience: 3,
      summary_bio:
        'Data Scientist with 3+ years building predictive ML models, NLP pipelines, and production inference APIs with Python, PyTorch, and Docker.',
      skills_and_tools: {
        core_skills: ['Machine Learning', 'Deep Learning', 'NLP', 'Feature Engineering', 'A/B Testing'],
        programming_languages: ['Python', 'SQL', 'R'],
        frameworks_and_libraries: ['PyTorch', 'Scikit-Learn', 'Pandas', 'FastAPI'],
        tools_and_platforms: ['Docker', 'MLflow', 'PostgreSQL', 'Git'],
      },
      experience_highlights: [
        {
          company: 'Swvl',
          role: 'Data Scientist',
          start_date: '2022-08',
          end_date: 'Present',
          location: 'Cairo, Egypt',
          achievements: [
            'Built a dynamic route pricing regression model that improved ride margins by 7.4%.',
            'Deployed production sentiment analysis model processing 50k+ user reviews monthly.',
          ],
        },
      ],
      featured_projects: [
        {
          name: 'Customer Churn Early-Warning Predictor',
          tech_stack: ['Python', 'XGBoost', 'FastAPI', 'PostgreSQL'],
          summary: 'Trained and deployed an XGBoost pipeline predicting user churn with 88% ROC-AUC.',
          link: 'https://github.com/ahmed-elsayed/churn-predictor',
        },
      ],
      certifications: [
        {
          name: 'Deep Learning Specialization',
          issuer: 'DeepLearning.AI',
          issue_date: '2022-03',
        },
      ],
    },
    {
      persona_id: 'data_analyst_track',
      target_title: 'Data Analyst',
      alternative_titles: ['Business Intelligence Analyst', 'Product Analyst'],
      is_primary: false,
      seniority_level: 'Mid-Level',
      years_of_experience: 3,
      summary_bio:
        'Analytical problem solver skilled in transforming complex relational databases into executive decision dashboards using SQL, Tableau, and Power BI.',
      skills_and_tools: {
        core_skills: ['Exploratory Data Analysis', 'Cohort Analysis', 'KPI Metric Formulation'],
        programming_languages: ['SQL (PostgreSQL, BigQuery)', 'Python'],
        frameworks_and_libraries: ['Pandas', 'Matplotlib', 'Seaborn'],
        tools_and_platforms: ['Power BI', 'Tableau', 'Excel', 'Metabase'],
      },
      experience_highlights: [
        {
          company: 'Swvl',
          role: 'Product Data Analyst (Cross-functional)',
          start_date: '2022-08',
          end_date: 'Present',
          location: 'Cairo, Egypt',
          achievements: [
            'Designed executive daily active rider dashboard in Metabase.',
            'Wrote optimized PostgreSQL queries reducing reporting ETL runtimes by 42%.',
          ],
        },
      ],
      featured_projects: [
        {
          name: 'E-Commerce Cohort Retention & LTV Dashboard',
          tech_stack: ['SQL', 'Power BI', 'Python'],
          summary: 'Built end-to-end dashboard tracking customer lifetime value (LTV) and 30-day retention.',
          link: 'https://github.com/ahmed-elsayed/retention-bi-dashboard',
        },
      ],
      certifications: [
        {
          name: 'Google Data Analytics Professional Certificate',
          issuer: 'Google',
          issue_date: '2021-11',
        },
      ],
    },
  ],
  custom_sections: [
    {
      id: 'sec_publications',
      section_title: 'Publications & Research Papers',
      section_type: 'items',
      items: [
        {
          id: 'pub_1',
          title: 'Dynamic Route Pricing via Constrained Reinforcement Learning',
          subtitle: 'IEEE Transactions on Intelligent Transportation Systems',
          date: '2023',
          location_or_link: 'https://doi.org/10.1109/TITS.2023.101',
          description: 'Lead author on novel pricing algorithms deployed across high-density Cairo commuter corridors.',
          bullet_points: [
            'Evaluated real-world route efficiency gains across 50,000+ daily commuter trips.',
          ],
        },
      ],
    },
    {
      id: 'sec_awards',
      section_title: 'Honors & Awards',
      section_type: 'items',
      items: [
        {
          id: 'award_1',
          title: 'First Place - National AI & FinTech Hackathon',
          subtitle: 'Ministry of Communications & Information Technology (MCIT)',
          date: '2023',
          location_or_link: 'Cairo, Egypt',
          description: 'Awarded first prize out of 120 regional teams for predictive credit scoring model.',
          bullet_points: [],
        },
      ],
    },
  ],
};

// LocalStorage helpers for offline resiliency
function getLocalProfiles(): FullProfileResponse[] {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveLocalProfile(profile: UserProfilePayload): FullProfileResponse {
  const existing = getLocalProfiles();
  const nextId = existing.length > 0 ? Math.max(...existing.map((e) => e.id)) + 1 : 1;
  const newRecord: FullProfileResponse = { id: nextId, profile };
  existing.unshift(newRecord);
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(existing));
  return newRecord;
}

function updateLocalProfile(id: number, profile: UserProfilePayload): FullProfileResponse {
  const existing = getLocalProfiles();
  const idx = existing.findIndex((e) => e.id === id);
  const updatedRecord: FullProfileResponse = { id, profile };
  if (idx >= 0) {
    existing[idx] = updatedRecord;
  } else {
    existing.unshift(updatedRecord);
  }
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(existing));
  return updatedRecord;
}

function deleteLocalProfile(id: number): boolean {
  const existing = getLocalProfiles();
  const filtered = existing.filter((e) => e.id !== id);
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(filtered));
  return true;
}

export const ProfileAPI = {
  /**
   * Save a newly generated profile to the backend database (or local storage fallback)
   */
  async createProfile(data: UserProfilePayload): Promise<{ data: FullProfileResponse; isOffline: boolean }> {
    try {
      const res = await fetch(`${API_BASE}/profiles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        throw new Error(`API returned HTTP ${res.status}: ${await res.text()}`);
      }

      const created = await res.json();
      return { data: created, isOffline: false };
    } catch (err) {
      console.warn('Backend API unavailable. Saving to local storage fallback:', err);
      const fallback = saveLocalProfile(data);
      return { data: fallback, isOffline: true };
    }
  },

  /**
   * Updates an existing Master Profile in the backend database (or local storage fallback)
   */
  async updateProfile(id: number, data: UserProfilePayload): Promise<{ data: FullProfileResponse; isOffline: boolean }> {
    try {
      const res = await fetch(`${API_BASE}/profiles/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        throw new Error(`API returned HTTP ${res.status}: ${await res.text()}`);
      }

      const updated = await res.json();
      return { data: updated, isOffline: false };
    } catch (err) {
      console.warn('Backend API unavailable. Updating local storage fallback:', err);
      const fallback = updateLocalProfile(id, data);
      return { data: fallback, isOffline: true };
    }
  },

  /**
   * Deletes a Master Profile by ID
   */
  async deleteProfile(id: number): Promise<{ success: boolean; isOffline: boolean }> {
    try {
      const res = await fetch(`${API_BASE}/profiles/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return { success: true, isOffline: false };
    } catch {
      deleteLocalProfile(id);
      return { success: true, isOffline: true };
    }
  },

  /**
   * Fetch list of saved profiles
   */
  async listProfiles(): Promise<{ profiles: ProfileSummary[]; isOffline: boolean }> {
    try {
      const res = await fetch(`${API_BASE}/profiles`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const list = await res.json();
      return { profiles: list, isOffline: false };
    } catch {
      const local = getLocalProfiles().map((item) => {
        const primaryPersona =
          item.profile.career_personas.find((p) => p.is_primary) || item.profile.career_personas[0];
        return {
          id: item.id,
          full_name: item.profile.personal_info.full_name,
          primary_email: item.profile.personal_info.primary_email,
          current_city: item.profile.residence_and_mobility.current_residence.city,
          current_country: item.profile.residence_and_mobility.current_residence.country,
          willing_to_relocate: item.profile.residence_and_mobility.willing_to_relocate,
          persona_count: item.profile.career_personas.length,
          primary_persona_title: primaryPersona ? primaryPersona.target_title : 'Candidate',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
      });
      return { profiles: local, isOffline: true };
    }
  },

  /**
   * Fetch full profile by ID
   */
  async getProfile(id: number): Promise<FullProfileResponse | null> {
    try {
      const res = await fetch(`${API_BASE}/profiles/${id}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      const local = getLocalProfiles();
      return local.find((p) => p.id === id) || null;
    }
  },

  /**
   * Check database status
   */
  async getDbStatus(): Promise<DBStatusResponse | null> {
    try {
      const res = await fetch(`${API_BASE}/profiles/system/db-status`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  /**
   * Switch primary persona on an existing profile
   */
  async setPrimaryPersona(profileId: number, personaId: string): Promise<FullProfileResponse | null> {
    try {
      const res = await fetch(`${API_BASE}/profiles/${profileId}/personas/${personaId}/primary`, {
        method: 'PATCH',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return null;
    }
  },

  /**
   * Parse LaTeX CV content into a structured candidate profile
   */
  async parseLatex(latexContent: string): Promise<ParseLatexApiResponse> {
    try {
      const res = await fetch(`${API_BASE}/profiles/parse-latex`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ latex_content: latexContent }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn('Backend parse-latex endpoint unavailable, running local parser:', err);
      const localParsed = parseLatexCvClient(latexContent);
      return {
        success: true,
        message: `Extracted ${localParsed.stats.experience_count} experiences, ${localParsed.stats.education_count} degrees, and ${localParsed.stats.skills_count} skills.`,
        stats: localParsed.stats,
        profile: localParsed.profile,
      };
    }
  },
};
