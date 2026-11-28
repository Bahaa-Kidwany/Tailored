/**
 * Cover Letter API Service
 * Handles generation and persistence of targeted cover letters
 */

import { apiFetchRaw } from './apiClient';

export interface CoverLetterItem {
  doc_id: string;
  job_id?: number | null;
  subject_line: string;
  body_markdown: string;
  company_name?: string | null;
  job_title?: string | null;
  recipient_email?: string | null;
  source_label?: string | null;
  created_at: string;
}

export interface GenerateCoverLetterParams {
  base_cv_text: string;
  job_id?: number;
  job_title?: string;
  company_name?: string;
  job_description_text?: string;
  company_website_url?: string;
  tone?: string;
}

export const CoverLetterAPI = {
  async generateCoverLetter(params: GenerateCoverLetterParams): Promise<{ coverLetter: CoverLetterItem; isOffline: boolean }> {
    try {
      const res = await apiFetchRaw('/cover-letter', {
        method: 'POST',
        body: params,
        featureKey: 'studio.cover_letter.generate',
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return { coverLetter: data, isOffline: false };
    } catch (err) {
      console.warn('Backend cover letter generation unavailable, using local synthesizer:', err);
      const doc_id = `cl_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      const role = params.job_title || 'Target Role';
      const company = params.company_name || 'Hiring Team';

      const subject_line = `Application for ${role} - ${company}`;
      const body_markdown = `Subject: ${subject_line}

Dear ${company} Hiring Team,

I am writing to express my enthusiastic interest in the ${role} position at ${company}. With a strong background in software engineering and data systems, I have built a career delivering measurable technical outcomes and scalable solutions.

Having reviewed the requirements for this role, I am particularly drawn to your team's technical vision. In my previous work, I have consistently applied core engineering principles—optimizing architectures, improving data throughput, and collaborating closely with cross-functional stakeholders to solve mission-critical problems.

Key highlights of my qualification for this role:
• Proven track record architecting and deploying resilient production systems.
• Deep hands-on proficiency aligned with ${role} core competencies.
• A commitment to verifiable code quality, high-impact collaboration, and iterative delivery.

I would welcome the opportunity to discuss how my technical expertise and problem-solving mindset can contribute directly to ${company}'s milestones. Please find my tailored CV attached for your review.

Thank you for your time and consideration.

Sincerely,
Candidate`;

      const fallbackItem: CoverLetterItem = {
        doc_id,
        job_id: params.job_id || null,
        subject_line,
        body_markdown,
        company_name: company,
        job_title: role,
        created_at: new Date().toISOString(),
      };

      return { coverLetter: fallbackItem, isOffline: true };
    }
  },

  async listCoverLetters(): Promise<{ coverLetters: CoverLetterItem[]; isOffline: boolean }> {
    try {
      const res = await apiFetchRaw('/cover-letter');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return { coverLetters: data, isOffline: false };
    } catch {
      return { coverLetters: [], isOffline: true };
    }
  },
};

