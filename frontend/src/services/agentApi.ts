import { API_BASE, apiFetch, generateTraceparent, getAccessToken } from './apiClient';
import type { AiActionCard, AiAuditItem, AiProposalItem, AiResourceItem } from '../components/common/CalmAiCoachSidecar';

export interface AgentThread {
  id: string;
  surface: string;
  scope: string;
  doc_id?: string | null;
  job_id?: string | null;
  title: string;
}

export interface BehavioralMemoryFact {
  id: string;
  category: string;
  fact_text: string;
  confidence: number;
  source_event_ids: string[];
  last_reinforced_at: string;
}

export interface StreamTurnHandlers {
  onThinkingStep?: (step: string) => void;
  onTextDelta?: (delta: string) => void;
  onProposalCard?: (card: AiProposalItem) => void;
  onActionCard?: (card: AiActionCard) => void;
  onResourceList?: (resources: { heading: string; items: AiResourceItem[] }) => void;
  onAuditSummary?: (audit: { heading: string; items: AiAuditItem[] }) => void;
  onDone?: (meta: { message_id: string; checkpoint_id: string; langfuse_trace_id?: string }) => void;
}

export const AgentAPI = {
  async listThreads(surface?: string): Promise<AgentThread[]> {
    const qs = surface ? `?surface=${encodeURIComponent(surface)}` : '';
    return apiFetch(`/agent/threads${qs}`);
  },

  async createThread(payload: { surface: string; scope?: string; doc_id?: string; job_id?: string; title?: string }): Promise<AgentThread> {
    return apiFetch('/agent/threads', { method: 'POST', body: payload });
  },

  async streamMessage(
    threadId: string,
    payload: {
      prompt: string;
      mode: string;
      focused_anchor?: { id: string; label: string } | null;
      job_id?: string;
      doc_id?: string;
    },
    handlers: StreamTurnHandlers
  ): Promise<void> {
    const token = getAccessToken();
    const res = await fetch(`${API_BASE}/agent/threads/${threadId}/messages:stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        traceparent: generateTraceparent(),
        'X-Feature-Key': 'ai.coach.chat_turn',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok || !res.body) {
      throw new Error(`Coach stream failed (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let currentEvent = 'message';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
          const raw = line.slice(5).trim();
          if (!raw) continue;
          try {
            const data = JSON.parse(raw);
            if (currentEvent === 'thinking_step') handlers.onThinkingStep?.(data.step);
            else if (currentEvent === 'text_delta') handlers.onTextDelta?.(data.delta);
            else if (currentEvent === 'proposal_card') handlers.onProposalCard?.(data);
            else if (currentEvent === 'action_card') handlers.onActionCard?.(data);
            else if (currentEvent === 'resource_list') handlers.onResourceList?.(data);
            else if (currentEvent === 'audit_summary') handlers.onAuditSummary?.(data);
            else if (currentEvent === 'done') handlers.onDone?.(data);
          } catch {
            // ignore malformed sse chunk
          }
        }
      }
    }
  },

  async resolveProposal(proposalId: string, action: 'apply' | 'skip' | 'undo' | 'refine', refine_instruction?: string) {
    return apiFetch<{ proposal: Record<string, unknown>; langfuse_eval_score: number }>(
      `/agent/proposals/${proposalId}/resolve`,
      {
        method: 'POST',
        body: { action, refine_instruction },
        featureKey: 'ai.coach.proposal.resolve',
      }
    );
  },

  async confirmAction(actionId: string, confirm: boolean = true) {
    return apiFetch(`/agent/actions/${actionId}/confirm`, {
      method: 'POST',
      body: { confirm },
      featureKey: 'ai.coach.action.confirm',
    });
  },

  async getMemory(): Promise<{
    behavior_profile: Record<string, unknown> | null;
    memory_facts: BehavioralMemoryFact[];
    proactive_suggestions: Array<Record<string, unknown>>;
  }> {
    return apiFetch('/agent/memory');
  },

  async deleteMemoryFact(factId: string): Promise<void> {
    await apiFetch(`/agent/memory/${factId}`, { method: 'DELETE' });
  },

  async clearAllMemory(): Promise<void> {
    await apiFetch('/agent/memory', { method: 'DELETE' });
  },
};
