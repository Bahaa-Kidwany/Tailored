import type {
  AiChatMessage,
  AiResourceItem,
  AiAuditItem,
} from '../components/common/CalmAiCoachSidecar';
import { cleanCompanyName, cleanTargetJobTitle, type CvFitSummary } from '../services/cvFitApi';
import type { CoverLetterItem } from '../services/coverLetterApi';
import type { JobItem } from '../services/jobsApi';
import type { UserProfilePayload } from '../services/profileApi';
import { hasDirectRecruiterEmail, type PipelineItem } from '../services/pipelineStorage';
import { evaluateAllPersonas } from './fitEngine';

interface CoachWorkspaceContext {
  prompt: string;
  surface: 'cv' | 'cover-letter';
  activeJob: JobItem;
  profile: UserProfilePayload;
  tailoredDocs: CvFitSummary[];
  coverLetters: CoverLetterItem[];
  radarJobs: JobItem[];
  pipelineItems: PipelineItem[];
}

export function buildWorkspaceCoachReply(ctx: CoachWorkspaceContext): AiChatMessage | null {
  const q = ctx.prompt.toLowerCase();
  const company = cleanCompanyName(ctx.activeJob.company_name);
  const role = cleanTargetJobTitle(ctx.activeJob.title);
  const now = Date.now();

  // 1. Cross-page action request: Pipeline mark applied / add / stage change / draft follow-up
  if (
    (/\b(mark|move|set|add|track)\b/.test(q) && /\b(pipeline|applied|interview|saved)\b/.test(q)) ||
    q.includes('stage to applied')
  ) {
    const existingPipe = ctx.pipelineItems.find((p) => p.job.id === ctx.activeJob.id);
    const nextStatus = q.includes('interview') ? 'interview' : q.includes('saved') ? 'saved' : 'applied';
    const nextLabel = nextStatus === 'interview' ? 'Interview' : nextStatus === 'saved' ? 'Saved' : 'Applied';
    return {
      id: `ws_act_${now}`,
      role: 'assistant',
      text: `Ready to update ${company} (${role}) in your Application Pipeline:`,
      actionCard: {
        id: `act_${now}`,
        title: existingPipe ? `Move ${company} to ${nextLabel}` : `Track ${company} as ${nextLabel}`,
        description:
          nextStatus === 'applied'
            ? 'Freezes your current CV snapshot and sets the 7-day follow-up reminder cleanly.'
            : `Updates ${company} directly in your Pipeline CRM without leaving the studio.`,
        targetBadge: `Pipeline · ${nextLabel}`,
        confirmLabel: 'Confirm Update',
        status: 'pending',
        actionType: 'pipeline_stage',
        payload: { jobId: ctx.activeJob.id, status: nextStatus },
      },
    };
  }

  // 2. Follow-up / Pipeline overdue / @Pipeline audit
  if (
    q.includes('@pipeline') ||
    /\b(follow-up|followup|follow up|overdue|pipeline|nudge|pending)\b/.test(q)
  ) {
    const appliedItems = ctx.pipelineItems.filter((p) => p.status === 'applied');
    const readyItems = ctx.pipelineItems.filter((p) => p.status === 'in_process');
    const auditItems: AiAuditItem[] = [
      ...appliedItems.slice(0, 2).map((item) => ({
        id: `aud_fu_${item.id}`,
        sentiment: 'down' as const,
        title: `${cleanCompanyName(item.job.company_name)} · Follow-up overdue`,
        detail: `${cleanTargetJobTitle(item.job.title)} (${item.recruiter_email || 'External Portal'})`,
        actionLabel: 'Draft Follow-Up',
        actionType: 'open_followup' as const,
        payloadId: String(item.job.id),
      })),
      ...readyItems.slice(0, 2).map((item) => ({
        id: `aud_rd_${item.id}`,
        sentiment: 'up' as const,
        title: `${cleanCompanyName(item.job.company_name)} · Package ready to send`,
        detail: `${cleanTargetJobTitle(item.job.title)} (${hasDirectRecruiterEmail(item.job) ? item.recruiter_email : 'External Portal'})`,
        actionLabel: 'Open Outreach',
        actionType: 'open_letter' as const,
        payloadId: String(item.job.id),
      })),
    ];

    if (auditItems.length === 0) {
      auditItems.push({
        id: 'aud_clear',
        sentiment: 'up',
        title: 'Pipeline is clear',
        detail: `${ctx.pipelineItems.length} tracked applications · zero overdue follow-ups`,
      });
    }

    return {
      id: `ws_aud_${now}`,
      role: 'assistant',
      text: `Checked your Pipeline CRM (${ctx.pipelineItems.length} tracked threads):`,
      audit: {
        heading: 'Pipeline Attention Summary',
        items: auditItems,
      },
    };
  }

  // 3. Available CVs / Recommend CV to attach / @Saved CVs
  if (
    q.includes('@saved cvs') ||
    /\b(available cvs|my cvs|show.*cvs|which cv|best cv|attach.*cv|compare.*cv|pick.*cv|resume)\b/.test(q)
  ) {
    const items: AiResourceItem[] = ctx.tailoredDocs.slice(0, 3).map((doc) => ({
      id: `res_cv_${doc.doc_id}`,
      kind: 'cv',
      title: `${cleanCompanyName(doc.company_name || company)} · ${cleanTargetJobTitle(doc.job_title || role)}`,
      subtitle: `${doc.bullet_diffs_count} tailored bullets · ${doc.parsed_skills.slice(0, 3).join(', ') || 'Production stack'}`,
      fitScore: doc.fit_score ?? 92,
      meta: doc.job_id === ctx.activeJob.id ? 'Exact role match' : 'Tailored CV',
      primaryLabel: ctx.surface === 'cover-letter' ? 'Use CV' : 'Load Draft',
      payloadId: doc.doc_id,
    }));

    const basePersona = ctx.profile.career_personas[0];
    items.push({
      id: 'res_cv_base',
      kind: 'cv',
      title: `${basePersona?.target_title || 'Master Profile'} · Base CV`,
      subtitle: 'Master Profile PDF · Verified 0 cr baseline',
      fitScore: evaluateAllPersonas(ctx.activeJob, ctx.profile).best.overallScore,
      meta: 'Baseline PDF',
      primaryLabel: ctx.surface === 'cover-letter' ? 'Use CV' : 'Load Base',
      payloadId: 'base',
    });

    return {
      id: `ws_cvs_${now}`,
      role: 'assistant',
      text:
        ctx.surface === 'cover-letter'
          ? `Found ${items.length} CV options ready to attach for ${company}. Preview any option or attach directly:`
          : `Found ${items.length} CVs across your archive. Preview side-by-side or load one into the workbench:`,
      resources: {
        heading: `Available CVs · Ranked for ${company}`,
        items,
      },
    };
  }

  // 4. @Cover Letters lookup
  if (
    q.includes('@cover letters') ||
    /\b(cover letters|past letters|previous pitch|my letters)\b/.test(q)
  ) {
    const items: AiResourceItem[] = ctx.coverLetters.slice(0, 4).map((cl) => ({
      id: `res_cl_${cl.doc_id}`,
      kind: 'letter',
      title: `${cleanCompanyName(cl.company_name || 'Application')} · ${cleanTargetJobTitle(cl.job_title || 'Outreach')}`,
      subtitle: cl.subject_line,
      meta: 'Saved Pitch',
      primaryLabel: 'Open Pitch',
      payloadId: String(cl.job_id || ctx.activeJob.id),
    }));

    return {
      id: `ws_cls_${now}`,
      role: 'assistant',
      text: `Here are your saved cover letters (${items.length} found). Preview copy or switch directly:`,
      resources: {
        heading: 'Saved Cover Letters',
        items:
          items.length > 0
            ? items
            : [
                {
                  id: 'res_cl_curr',
                  kind: 'letter',
                  title: `${company} · ${role}`,
                  subtitle: `Current working draft (${ctx.activeJob.parsed_skills.slice(0, 3).join(', ') || 'Core stack'})`,
                  primaryLabel: 'Open Pitch',
                  payloadId: String(ctx.activeJob.id),
                },
              ],
      },
    };
  }

  // 5. @Jobs / Radar matching query
  if (
    q.includes('@jobs') ||
    /\b(other jobs|matching jobs|radar jobs|which jobs|similar jobs|find jobs)\b/.test(q)
  ) {
    const items: AiResourceItem[] = ctx.radarJobs
      .map((j) => ({ job: j, score: evaluateAllPersonas(j, ctx.profile).best.overallScore }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 4)
      .map(({ job, score }) => ({
        id: `res_job_${job.id}`,
        kind: 'job' as const,
        title: `${cleanCompanyName(job.company_name)} · ${cleanTargetJobTitle(job.title)}`,
        subtitle: `${job.location} · ${hasDirectRecruiterEmail(job) ? 'Direct Email' : 'External Portal'}`,
        fitScore: score,
        primaryLabel: ctx.surface === 'cover-letter' ? 'Draft Pitch' : 'Tailor CV',
        payloadId: String(job.id),
      }));

    return {
      id: `ws_jobs_${now}`,
      role: 'assistant',
      text: `Top matches from your Job Radar ranked against your Master Profile:`,
      resources: {
        heading: 'Top Workspace Job Matches',
        items,
      },
    };
  }

  // 6. @Master Profile / Projects / Skills lookup
  if (
    q.includes('@master profile') ||
    /\b(master profile|my profile|what projects|which projects|my metrics|gap|missing skills)\b/.test(q)
  ) {
    const bestEval = evaluateAllPersonas(ctx.activeJob, ctx.profile).best;
    const primaryPersona =
      ctx.profile.career_personas.find((p) => p.persona_id === bestEval.personaId) ||
      ctx.profile.career_personas[0];
    const items: AiAuditItem[] = [
      ...bestEval.matchedSkills.slice(0, 3).map((sk) => ({
        id: `mp_up_${sk}`,
        sentiment: 'up' as const,
        title: `Verified skill match: ${sk}`,
        detail: `Backed by ${primaryPersona?.experience_highlights[0]?.company || 'Master Profile'} production delivery.`,
      })),
      ...bestEval.missingSkills.slice(0, 2).map((sk) => ({
        id: `mp_gap_${sk}`,
        sentiment: 'down' as const,
        title: `Missing JD token: ${sk}`,
        detail: `Not explicitly named for ${company}; frame adjacent architecture work in your opening pitch.`,
        actionLabel: 'Inject Bridge',
        actionType: 'inject_text' as const,
        payloadId: sk,
      })),
    ];

    return {
      id: `ws_mp_${now}`,
      role: 'assistant',
      text: `Audited your Master Profile against ${company} (${bestEval.personaTitle}):`,
      audit: {
        heading: `Master Profile Check · ${company}`,
        items,
      },
    };
  }

  return null;
}
