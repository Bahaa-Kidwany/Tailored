import { apiFetchRaw, getAccessToken } from './apiClient';
import { extractEmail, normalizeServerJob, resolveServerJobId, type JobItem } from './jobsApi';
import type { CoverLetterItem } from './coverLetterApi';

export type PipelineStatus = 'saved' | 'in_process' | 'applied' | 'interview' | 'archived';

export function hasDirectRecruiterEmail(job: JobItem): boolean {
  if (!job) return false;
  if (job.recruiter_email && job.recruiter_email.trim().length > 0) return true;
  if (extractEmail(job.raw_description || '')) return true;

  const src = (job.source_type || '').toLowerCase();
  const url = (job.url || '').toLowerCase();
  return (
    src === 'linkedin_posts' ||
    src === 'recruiter_post' ||
    src === 'custom_post' ||
    src === 'description_paste' ||
    url.includes('/posts/') ||
    url.includes('/feed/update/') ||
    url.includes('activity-') ||
    url.includes('activity:')
  );
}

/**
 * Pipeline tracks EVERY committed application (both Direct Email outreach & External Portal links).
 */
export function isEligibleForPipeline(job: JobItem): boolean {
  return Boolean(job);
}

export interface PipelineItem {
  id: string; // e.g. "pipe_101" or server numeric id as string "1"
  job: JobItem;
  status: PipelineStatus;
  saved_at: string;
  applied_at?: string | null;
  recruiter_email?: string | null;
  tailored_cv_doc_id?: string | null;
  cover_letter?: CoverLetterItem | null;
  notes?: string;
}

export interface OutreachPackage {
  item_id: number;
  job_title: string;
  company_name: string;
  to_email: string;
  subject: string;
  body_markdown: string;
  gmail_web_url: string;
  mailto_url: string;
  cv_pdf_download_url?: string | null;
  cover_letter_download_url?: string | null;
  candidate_name: string;
  candidate_email: string;
  candidate_phone: string;
}

const STORAGE_KEY = 'tailored_application_pipeline_v1';
const MIGRATED_FLAG_KEY = 'tailored_pipeline_migrated_to_db_v1';

function resolveServerItemId(id: string): string | null {
  if (!id || id.startsWith('pipe_') || id.startsWith('local')) {
    const match = id.match(/^pipe_([0-9a-f-]{8,}|\d+)$/);
    return match ? match[1] : null;
  }
  return id;
}

export const PipelineStorage = {
  /**
   * Synchronously returns items from local storage cache.
   */
  getItems(): PipelineItem[] {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      if (!data) return [];
      const parsed = JSON.parse(data) as PipelineItem[];
      return parsed.filter((it) => Boolean(it?.job));
    } catch {
      return [];
    }
  },

  /**
   * Updates local storage cache.
   */
  saveItems(items: PipelineItem[]): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch (e) {
      console.warn('Failed to save pipeline to localStorage', e);
    }
  },

  /**
   * Fetches the latest pipeline items directly from the backend database.
   */
  async fetchServerItems(profileId?: number): Promise<PipelineItem[]> {
    try {
      if (!getAccessToken()) return this.getItems();
      const url = profileId ? `/pipeline?profile_id=${profileId}` : '/pipeline';
      const res = await apiFetchRaw(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const serverItems = await res.json();
      const mapped: PipelineItem[] = serverItems.map((s: any) => ({
        id: String(s.id),
        job: normalizeServerJob(
          s.job || {
            id: s.job_id || s.id,
            title: s.job_title || 'Target Opportunity',
            company_name: s.company_name || 'Company',
            url: s.job_url || '',
            source_type: s.channel === 'direct_email' ? 'recruiter_post' : 'web',
            recruiter_email: s.recruiter_email,
          }
        ),
        status: s.status as PipelineStatus,
        saved_at: s.saved_at || s.created_at,
        applied_at: s.applied_at,
        recruiter_email: s.recruiter_email,
        tailored_cv_doc_id: s.tailored_cv_doc_id,
        cover_letter: s.cover_letter
          ? {
              doc_id: s.cover_letter.doc_id,
              subject_line: s.cover_letter.subject_line,
              body_markdown: s.cover_letter.body_markdown,
              created_at: s.cover_letter.created_at,
            }
          : null,
        notes: s.notes,
      }));
      this.saveItems(mapped);
      return mapped;
    } catch (err) {
      console.warn('Could not reach backend /pipeline API, using local cache:', err);
      return this.getItems();
    }
  },

  /**
   * Synchronizes localStorage with backend database:
   * 1. If not yet migrated, imports local items to backend.
   * 2. Fetches fresh pipeline state from backend.
   */
  async syncWithServer(profileId?: number): Promise<PipelineItem[]> {
    try {
      if (!getAccessToken()) return this.getItems();
      const isMigrated = localStorage.getItem(MIGRATED_FLAG_KEY);
      const localItems = this.getItems();

      if (!isMigrated && localItems.length > 0) {
        try {
          await apiFetchRaw('/pipeline/batch-import', {
            method: 'POST',
            body: {
              profile_id: profileId,
              items: localItems.map((it) => ({
                job_id: resolveServerJobId(it.job.id, it.job.server_id),
                job_source_id: it.job.source_id,
                job_url: it.job.url,
                status: it.status,
                recruiter_email: it.recruiter_email,
                notes: it.notes,
                tailored_cv_doc_id: it.tailored_cv_doc_id,
                applied_at: it.applied_at,
                job: it.job,
              })),
            },
          });
          localStorage.setItem(MIGRATED_FLAG_KEY, 'true');
        } catch (importErr) {
          console.warn('Batch migration to server deferred:', importErr);
        }
      }

      return await this.fetchServerItems(profileId);
    } catch {
      return this.getItems();
    }
  },

  /**
   * Adds or updates a job in the pipeline (persisting to server and updating local cache).
   */
  addOrUpdateJob(
    job: JobItem,
    status: PipelineStatus = 'in_process',
    recruiterEmail?: string | null,
    _profileId?: number,
    pkg?: { tailoredCvDocId?: string | null; coverLetter?: CoverLetterItem | null }
  ): PipelineItem | null {
    if (!job) return null;

    const items = this.getItems();
    const existingIndex = items.findIndex(
      (it) => it.job.id === job.id || it.job.source_id === job.source_id || (job.url && it.job.url === job.url)
    );

    const email =
      recruiterEmail ||
      job.recruiter_email ||
      extractEmail(job.raw_description || '') ||
      null;

    let itemToReturn: PipelineItem;

    if (existingIndex >= 0) {
      const existing = items[existingIndex];
      const nextAppliedAt =
        status === 'applied' && !existing.applied_at ? new Date().toISOString() : existing.applied_at;
      const updated: PipelineItem = {
        ...existing,
        job: { ...existing.job, ...job },
        recruiter_email: email || existing.recruiter_email,
        status: status || existing.status,
        applied_at: nextAppliedAt,
        tailored_cv_doc_id: pkg?.tailoredCvDocId !== undefined ? pkg.tailoredCvDocId : existing.tailored_cv_doc_id,
        cover_letter: pkg?.coverLetter !== undefined ? pkg.coverLetter : existing.cover_letter,
      };
      items[existingIndex] = updated;
      itemToReturn = updated;
    } else {
      const newItem: PipelineItem = {
        id: `pipe_${job.id || Date.now()}`,
        job,
        status,
        saved_at: new Date().toISOString(),
        applied_at: status === 'applied' ? new Date().toISOString() : undefined,
        recruiter_email: email,
        tailored_cv_doc_id: pkg?.tailoredCvDocId ?? null,
        cover_letter: pkg?.coverLetter ?? null,
      };
      items.unshift(newItem);
      itemToReturn = newItem;
    }

    this.saveItems(items);

    // Asynchronously synchronize with backend database
    if (getAccessToken()) {
      apiFetchRaw('/pipeline', {
        method: 'POST',
        body: {
          job_id: resolveServerJobId(job.id, job.server_id),
          job_title: job.title,
          company_name: job.company_name,
          job_url: job.url,
          status,
          recruiter_email: email,
          tailored_cv_doc_id: pkg?.tailoredCvDocId ?? null,
        },
        featureKey: 'pipeline.item.create',
      })
        .then(async (res) => {
          if (res.ok) {
            const serverItem = await res.json();
            const currentItems = this.getItems();
            const idx = currentItems.findIndex((it) => it.job.id === job.id);
            if (idx >= 0) {
              currentItems[idx].id = String(serverItem.id);
              this.saveItems(currentItems);
            }
          }
        })
        .catch((err) => {
          console.warn('Backend /pipeline sync scheduled on next online heartbeat:', err);
        });
    }

    return itemToReturn;
  },

  updateStatus(id: string, status: PipelineStatus): PipelineItem | null {
    const items = this.getItems();
    const item = items.find((it) => it.id === id);
    if (!item) return null;
    item.status = status;
    if (status === 'applied' && !item.applied_at) {
      item.applied_at = new Date().toISOString();
    }
    this.saveItems(items);

    const serverId = resolveServerItemId(id);
    if (serverId && getAccessToken()) {
      apiFetchRaw(`/pipeline/${serverId}`, {
        method: 'PATCH',
        body: { status, applied_at: item.applied_at },
        featureKey: 'pipeline.item.update',
      }).catch((err) => console.warn('Backend updateStatus sync deferred:', err));
    }

    return item;
  },

  updateCoverLetter(id: string, coverLetter: CoverLetterItem): PipelineItem | null {
    const items = this.getItems();
    const item = items.find((it) => it.id === id);
    if (!item) return null;
    item.cover_letter = coverLetter;
    if (item.status === 'saved') {
      item.status = 'in_process';
    }
    this.saveItems(items);

    const serverId = resolveServerItemId(id);
    if (serverId && coverLetter.doc_id && getAccessToken()) {
      apiFetchRaw(`/pipeline/${serverId}`, {
        method: 'PATCH',
        body: { cover_letter_doc_id: coverLetter.doc_id },
      }).catch((err) => console.warn('Backend cover letter link deferred:', err));
    }

    return item;
  },

  updateTailoredCv(id: string, docId: string): PipelineItem | null {
    const items = this.getItems();
    const item = items.find((it) => it.id === id);
    if (!item) return null;
    item.tailored_cv_doc_id = docId;
    if (item.status === 'saved') {
      item.status = 'in_process';
    }
    this.saveItems(items);

    const serverId = resolveServerItemId(id);
    if (serverId && getAccessToken()) {
      apiFetchRaw(`/pipeline/${serverId}`, {
        method: 'PATCH',
        body: { tailored_cv_doc_id: docId },
      }).catch((err) => console.warn('Backend tailored CV link deferred:', err));
    }

    return item;
  },

  updateNotes(id: string, notes: string): PipelineItem | null {
    const items = this.getItems();
    const item = items.find((it) => it.id === id);
    if (!item) return null;
    item.notes = notes;
    this.saveItems(items);

    const serverId = resolveServerItemId(id);
    if (serverId && getAccessToken()) {
      apiFetchRaw(`/pipeline/${serverId}`, {
        method: 'PATCH',
        body: { notes },
      }).catch((err) => console.warn('Backend notes update deferred:', err));
    }

    return item;
  },

  removeItem(id: string): void {
    const items = this.getItems().filter((it) => it.id !== id);
    this.saveItems(items);

    const serverId = resolveServerItemId(id);
    if (serverId && getAccessToken()) {
      apiFetchRaw(`/pipeline/${serverId}`, {
        method: 'DELETE',
      }).catch((err) => console.warn('Backend removeItem deferred:', err));
    }
  },

  updateRecruiterEmail(id: string, email: string): PipelineItem | null {
    const items = this.getItems();
    const item = items.find((it) => it.id === id);
    if (!item) return null;
    item.recruiter_email = email;
    this.saveItems(items);

    const serverId = resolveServerItemId(id);
    if (serverId && getAccessToken()) {
      apiFetchRaw(`/pipeline/${serverId}`, {
        method: 'PATCH',
        body: { recruiter_email: email },
      }).catch((err) => console.warn('Backend recruiter_email update deferred:', err));
    }
    return item;
  },

  /**
   * Fetches structured outreach package (Gmail URL, Mailto URL, candidate contact details) from server.
   */
  async getOutreachPackage(id: string | number): Promise<OutreachPackage | null> {
    const serverId = resolveServerItemId(String(id));
    if (!serverId || !getAccessToken()) return null;
    try {
      const res = await apiFetchRaw(`/pipeline/${serverId}/outreach`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },
};
