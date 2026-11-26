import React, { useState, useRef, useEffect } from 'react';
import { TailoredIcon } from '../../brand/TailoredIcons';

export interface AiProposalItem {
  id: string;
  targetAnchorId: string;
  targetLabel: string;
  oldText: string;
  newText: string;
  status: 'pending' | 'applied' | 'skipped';
  isMetricQuestion?: boolean;
}

export interface AiResourceItem {
  id: string;
  kind: 'cv' | 'letter' | 'job' | 'pipeline';
  title: string;
  subtitle: string;
  fitScore?: number;
  meta?: string;
  primaryLabel: string;
  payloadId: string;
}

export interface AiActionCard {
  id: string;
  title: string;
  description: string;
  targetBadge: string;
  confirmLabel: string;
  status: 'pending' | 'confirmed' | 'cancelled';
  actionType: 'pipeline_stage' | 'open_followup';
  payload?: { jobId: number; status?: string };
}

export interface AiAuditItem {
  id: string;
  sentiment: 'up' | 'down';
  title: string;
  detail: string;
  actionLabel?: string;
  actionType?: 'open_followup' | 'open_letter' | 'inject_text';
  payloadId?: string;
}

export interface AiChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  thinkingSummary?: string;
  proposal?: AiProposalItem;
  resources?: { heading: string; items: AiResourceItem[] };
  actionCard?: AiActionCard;
  audit?: { heading: string; items: AiAuditItem[] };
}

export interface CalmAiCoachSidecarProps {
  title: string;
  groundedContextLabel: string;
  messages: AiChatMessage[];
  isStreaming: boolean;
  focusedAnchor: { id: string; label: string } | null;
  onClearFocusedAnchor: () => void;
  onSendMessage: (prompt: string, mode: string) => void;
  onStopStreaming?: () => void;
  onApplyProposal: (proposalId: string) => void;
  onSkipProposal: (proposalId: string) => void;
  onUndoProposal: (proposalId: string) => void;
  onRefineProposal: (proposalId: string, instruction: string) => void;
  onHoverProposal: (anchorId: string | null) => void;
  onLocateAnchor: (anchorId: string) => void;
  onSwapSide: () => void;
  onCollapse: () => void;
  onNewThread: () => void;
  starterPrompts: string[];
  modes?: string[];
  mode: string;
  onChangeMode: (m: string) => void;
  threadHistoryLabels?: string[];
  onSwitchHistory?: (label: string) => void;
  contextSummary?: React.ReactNode;
  variant?: 'default' | 'atelier';
  threadScope?: 'role' | 'workspace';
  onChangeThreadScope?: (scope: 'role' | 'workspace') => void;
  enableWorkspaceMentions?: boolean;
  onPreviewResource?: (item: AiResourceItem) => void;
  onSelectResource?: (item: AiResourceItem) => void;
  onConfirmAction?: (actionId: string) => void;
  onCancelAction?: (actionId: string) => void;
  onAuditAction?: (item: AiAuditItem) => void;
}

/**
 * Canonical Calm AI Chat Shape (00 §5):
 * - 44px quiet header (Coach · Grounded + Swap / History / New / Collapse)
 * - Right-aligned compact User Capsule (max 82%)
 * - Left-aligned 100% borderless AI prose + 1-line collapsible Thinking Accordion
 * - 3-stage Proposal Diff Card (Active -> In-Place Refine Morph -> 1-line Applied Receipt)
 * - Floating diagonal-cut Composer Dock with conditional top Target Rim
 */
export const CalmAiCoachSidecar: React.FC<CalmAiCoachSidecarProps> = ({
  title,
  groundedContextLabel,
  messages,
  isStreaming,
  focusedAnchor,
  onClearFocusedAnchor,
  onSendMessage,
  onStopStreaming,
  onApplyProposal,
  onSkipProposal,
  onUndoProposal,
  onRefineProposal,
  onHoverProposal,
  onLocateAnchor,
  onSwapSide,
  onCollapse,
  onNewThread,
  starterPrompts,
  modes = ['Surgical', 'Metrics+', 'Condense', 'Fact Audit'],
  mode,
  onChangeMode,
  threadHistoryLabels = ['Current Thread', 'Initial Baseline Pass'],
  onSwitchHistory,
  contextSummary,
  variant = 'default',
  threadScope = 'role',
  onChangeThreadScope,
  enableWorkspaceMentions = false,
  onPreviewResource,
  onSelectResource,
  onConfirmAction,
  onCancelAction,
  onAuditAction,
}) => {
  const isAtelier = variant === 'atelier';
  const [draft, setDraft] = useState('');
  const [refineOpenId, setRefineOpenId] = useState<string | null>(null);
  const [refineText, setRefineText] = useState('');
  const [expandedThinking, setExpandedThinking] = useState<Record<string, boolean>>({});
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isModeOpen, setIsModeOpen] = useState(false);
  const [isMentionOpen, setIsMentionOpen] = useState(false);
  const [autoScrollLocked, setAutoScrollLocked] = useState(true);
  const [metricInput, setMetricInput] = useState('');

  const streamRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const modeWrapRef = useRef<HTMLDivElement>(null);
  const mentionWrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isModeOpen && !isMentionOpen) return;
    const onDown = (e: MouseEvent) => {
      if (modeWrapRef.current && !modeWrapRef.current.contains(e.target as Node)) {
        setIsModeOpen(false);
      }
      if (mentionWrapRef.current && !mentionWrapRef.current.contains(e.target as Node)) {
        setIsMentionOpen(false);
      }
    };
    window.addEventListener('mousedown', onDown);
    return () => window.removeEventListener('mousedown', onDown);
  }, [isModeOpen, isMentionOpen]);

  useEffect(() => {
    if (focusedAnchor) {
      inputRef.current?.focus();
    }
  }, [focusedAnchor]);

  useEffect(() => {
    if (autoScrollLocked && streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight;
    }
  }, [messages, isStreaming, autoScrollLocked]);

  // Keyboard shortcuts for latest pending proposal: Enter / Esc / R (when not typing)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement;
      const typing = el?.tagName === 'INPUT' || el?.tagName === 'TEXTAREA' || el?.isContentEditable;
      if (typing) return;
      const latestPending = [...messages]
        .reverse()
        .find((m) => m.proposal && m.proposal.status === 'pending')?.proposal;
      if (!latestPending) return;
      if (e.key.toLowerCase() === 'r') {
        e.preventDefault();
        setRefineOpenId(latestPending.id);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [messages]);

  const handleScroll = () => {
    const el = streamRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
    setAutoScrollLocked(nearBottom);
  };

  const submitDraft = () => {
    const clean = draft.trim();
    if (!clean || isStreaming) return;
    setDraft('');
    onSendMessage(clean, mode);
  };

  const iconBtnClass = isAtelier ? 't-atelier-icon-btn' : 't-btn t-btn--ghost t-btn--sm';
  const iconBtnStyle = isAtelier ? undefined : { padding: '4px 6px' };

  return (
    <section className="t-chat-pane" aria-label={title}>
      {/* 1. Quiet Panel Header */}
      <header className="t-chat-header" style={{ position: 'relative' }}>
        {isAtelier ? (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-start',
              gap: 3,
              minWidth: 0,
              flex: 1,
              marginRight: 8,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, minWidth: 0, maxWidth: '100%' }}>
              <TailoredIcon name="chat" size={15} withNotch={false} />
              <span className="t-atelier-coach-title">{title}</span>
            </div>
            <span className="t-atelier-context-pill" title={groundedContextLabel}>
              {groundedContextLabel}
            </span>
          </div>
        ) : (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              minWidth: 0,
              flex: 1,
              overflow: 'hidden',
              marginRight: 6,
            }}
          >
            <TailoredIcon name="chat" size={16} withNotch />
            <span style={{ fontWeight: 600, fontSize: 13, whiteSpace: 'nowrap' }}>{title}</span>
            <span
              className="t-mono"
              style={{
                fontSize: 10.5,
                color: 'var(--n500)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
              title={groundedContextLabel}
            >
              · {groundedContextLabel}
            </span>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: isAtelier ? 4 : 2, flexShrink: 0 }}>
          <button
            type="button"
            onClick={onSwapSide}
            className={iconBtnClass}
            style={iconBtnStyle}
            title="Swap AI Chat left / right (Alt+S)"
          >
            <TailoredIcon name="swap" size={14} />
          </button>

          <button
            type="button"
            onClick={() => setIsHistoryOpen((v) => !v)}
            className={iconBtnClass}
            style={iconBtnStyle}
            title="Conversation threads"
          >
            <TailoredIcon name="clock" size={14} />
          </button>

          <button
            type="button"
            onClick={onNewThread}
            className={iconBtnClass}
            style={iconBtnStyle}
            title="Start fresh thread"
          >
            <TailoredIcon name="plus" size={14} />
          </button>

          <button
            type="button"
            onClick={onCollapse}
            className={iconBtnClass}
            style={iconBtnStyle}
            title="Collapse AI Chat (])"
          >
            <TailoredIcon name="close" size={14} />
          </button>
        </div>

        {isHistoryOpen && (
          <div className="t-popover" style={{ top: 'calc(100% + 4px)', right: 12, width: 254, padding: 10 }}>
            {onChangeThreadScope && (
              <div style={{ marginBottom: 10, paddingBottom: 8, borderBottom: '1px solid rgba(26, 20, 18, 0.08)' }}>
                <div className={isAtelier ? 't-atelier-popover-label' : 't-label'} style={{ marginBottom: 6 }}>
                  Coach Context Scope
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  {(['role', 'workspace'] as const).map((sc) => (
                    <button
                      key={sc}
                      type="button"
                      className={`t-atelier-popover-chip ${threadScope === sc ? 't-atelier-popover-chip--active' : ''}`}
                      onClick={() => onChangeThreadScope(sc)}
                    >
                      {sc === 'role' ? 'This Role' : 'All Workspace'}
                    </button>
                  ))}
                </div>
              </div>
            )}
            <div
              className={isAtelier ? 't-atelier-popover-label' : 't-label'}
              style={isAtelier ? { padding: '0 8px' } : { color: 'var(--n500)', marginBottom: 6, padding: '0 6px' }}
            >
              Threads
            </div>
            {threadHistoryLabels.map((lbl) => (
              <button
                key={lbl}
                type="button"
                className={isAtelier ? 't-atelier-menu-row' : undefined}
                onClick={() => {
                  setIsHistoryOpen(false);
                  onSwitchHistory?.(lbl);
                }}
                style={
                  isAtelier
                    ? undefined
                    : {
                        width: '100%',
                        textAlign: 'left',
                        padding: '7px 8px',
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: 13,
                        color: 'var(--ink)',
                      }
                }
              >
                {lbl}
              </button>
            ))}
          </div>
        )}
      </header>

      {contextSummary && (
        <div
          style={{
            background: 'var(--chalk)',
            borderBottom: '1.5px solid var(--n300)',
            padding: '12px 18px',
            flexShrink: 0,
          }}
        >
          {contextSummary}
        </div>
      )}

      {/* 2. Generous Borderless Conversation Stream */}
      <div ref={streamRef} onScroll={handleScroll} className="t-chat-stream">
        {messages.map((msg) => {
          if (msg.role === 'user') {
            return (
              <div key={msg.id} className="t-chat-user-wrap">
                <div className="t-chat-user-capsule">{msg.text}</div>
              </div>
            );
          }

          const prop = msg.proposal;
          const isThinkingOpen = !!expandedThinking[msg.id];
          const isRefining = prop && refineOpenId === prop.id;

          return (
            <div
              key={msg.id}
              className={isAtelier ? 't-atelier-ai-turn' : undefined}
              style={isAtelier ? undefined : { display: 'flex', flexDirection: 'column', gap: 6 }}
            >
              {msg.thinkingSummary && (
                <button
                  type="button"
                  onClick={() =>
                    setExpandedThinking((prev) => ({ ...prev, [msg.id]: !prev[msg.id] }))
                  }
                  className="t-thinking-accordion"
                  style={{
                    background: 'transparent',
                    borderTop: 'none',
                    borderRight: 'none',
                    borderBottom: 'none',
                    textAlign: 'left',
                    cursor: 'pointer',
                  }}
                >
                  {isThinkingOpen ? '▾' : '▸'} {msg.thinkingSummary}
                </button>
              )}

              {isThinkingOpen && (
                <div
                  style={{
                    fontSize: 12,
                    color: 'var(--n500)',
                    paddingLeft: 12,
                    borderLeft: '2px solid var(--n300)',
                  }}
                >
                  Verified claim anchors against candidate Master Profile · Zero unverified metrics
                  added.
                </div>
              )}

              {/* Borderless Editorial AI Prose */}
              <div className="t-chat-ai-prose">{msg.text}</div>

              {/* Optional Metric Prompt when Master Profile lacks number */}
              {prop?.isMetricQuestion && prop.status === 'pending' && (
                <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
                  <input
                    className="t-input"
                    style={{ padding: '6px 10px', fontSize: 13 }}
                    value={metricInput}
                    onChange={(e) => setMetricInput(e.target.value)}
                    placeholder="Enter real number (e.g., 42% or 1,400 routes)..."
                  />
                  <button
                    type="button"
                    className="t-btn t-btn--ink t-btn--sm"
                    onClick={() => {
                      if (!metricInput.trim()) return;
                      onRefineProposal(prop.id, `Insert verified metric: ${metricInput.trim()}`);
                      setMetricInput('');
                    }}
                  >
                    Insert
                  </button>
                </div>
              )}

              {/* Proposal Card Lifecycle: Active -> In-Place Refine -> 1-Line Collapsed Receipt */}
              {prop && prop.status === 'pending' && (
                <div
                  className="t-proposal-card"
                  onMouseEnter={() => onHoverProposal(prop.targetAnchorId)}
                  onMouseLeave={() => onHoverProposal(null)}
                >
                  <div className="t-proposal-head">
                    <span>{prop.targetLabel}</span>
                    <button
                      type="button"
                      className={isAtelier ? 't-atelier-locate-btn' : undefined}
                      onClick={() => onLocateAnchor(prop.targetAnchorId)}
                      style={
                        isAtelier
                          ? undefined
                          : {
                              background: 'transparent',
                              border: 'none',
                              color: 'var(--dye)',
                              fontFamily: 'var(--font-mono)',
                              fontSize: 10.5,
                              fontWeight: 600,
                              letterSpacing: '0.08em',
                              textTransform: 'uppercase',
                              cursor: 'pointer',
                            }
                      }
                    >
                      Locate
                    </button>
                  </div>

                  <div className="t-proposal-diff">
                    {prop.oldText && (
                      <div className="t-diff-old">
                        {isAtelier ? (
                          <>
                            <span className="t-signal-down" style={{ marginTop: 6 }} aria-hidden="true" />
                            <span style={{ textDecoration: 'line-through' }}>{prop.oldText}</span>
                          </>
                        ) : (
                          prop.oldText
                        )}
                      </div>
                    )}
                    <div className="t-diff-new">
                      {isAtelier ? (
                        <>
                          <span className="t-signal-up" style={{ marginTop: 6 }} aria-hidden="true" />
                          <span>{prop.newText}</span>
                        </>
                      ) : (
                        prop.newText
                      )}
                    </div>
                  </div>

                  {isRefining ? (
                    <div
                      className="t-proposal-foot"
                      style={{ flexDirection: 'column', alignItems: 'stretch', gap: 8 }}
                    >
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {['Shorter', 'More metrics', 'Less jargon'].map((chip) => (
                          <button
                            key={chip}
                            type="button"
                            className={isAtelier ? 't-atelier-btn-tonal' : 't-btn t-btn--subtle t-btn--sm'}
                            style={isAtelier ? { padding: '5px 11px', fontSize: 12 } : { padding: '4px 9px', fontSize: 10 }}
                            onClick={() => {
                              setRefineOpenId(null);
                              onRefineProposal(prop.id, chip);
                            }}
                          >
                            {chip}
                          </button>
                        ))}
                      </div>
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          if (!refineText.trim()) return;
                          const val = refineText.trim();
                          setRefineText('');
                          setRefineOpenId(null);
                          onRefineProposal(prop.id, val);
                        }}
                        style={{ display: 'flex', gap: 6 }}
                      >
                        <input
                          className={isAtelier ? 't-atelier-inline-input' : 't-input'}
                          style={isAtelier ? undefined : { padding: '5px 9px', fontSize: 12.5 }}
                          value={refineText}
                          onChange={(e) => setRefineText(e.target.value)}
                          placeholder="Type quick tweak..."
                          autoFocus
                        />
                        <button
                          type="submit"
                          className={isAtelier ? 't-atelier-btn-primary' : 't-btn t-btn--ink t-btn--sm'}
                        >
                          Steer
                        </button>
                        <button
                          type="button"
                          onClick={() => setRefineOpenId(null)}
                          className={isAtelier ? 't-atelier-btn-ghost' : 't-btn t-btn--ghost t-btn--sm'}
                        >
                          <TailoredIcon name="close" size={12} />
                        </button>
                      </form>
                    </div>
                  ) : (
                    <div className="t-proposal-foot">
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button
                          type="button"
                          className={isAtelier ? 't-atelier-btn-primary' : 't-btn t-btn--primary t-btn--sm'}
                          onClick={() => onApplyProposal(prop.id)}
                        >
                          <TailoredIcon name="check" size={12} />
                          <span>Apply</span>
                        </button>
                        <button
                          type="button"
                          className={isAtelier ? 't-atelier-btn-tonal' : 't-btn t-btn--outline t-btn--sm'}
                          onClick={() => onSkipProposal(prop.id)}
                        >
                          Skip
                        </button>
                      </div>
                      <button
                        type="button"
                        className={isAtelier ? 't-atelier-btn-ghost' : 't-btn t-btn--ghost t-btn--sm'}
                        onClick={() => setRefineOpenId(prop.id)}
                      >
                        {isAtelier ? 'Refine' : 'Refine...'}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {prop && prop.status === 'applied' && (
                <div className="t-applied-receipt">
                  {isAtelier ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                      <span className="t-signal-up" aria-hidden="true" />
                      <span>Applied to {prop.targetLabel}</span>
                    </span>
                  ) : (
                    <span>Applied to {prop.targetLabel}</span>
                  )}
                  <button
                    type="button"
                    className={isAtelier ? 't-atelier-btn-ghost' : undefined}
                    onClick={() => onUndoProposal(prop.id)}
                    style={
                      isAtelier
                        ? { padding: '3px 9px', fontSize: 12.5, color: 'var(--ink)' }
                        : {
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--ink)',
                            fontFamily: 'var(--font-mono)',
                            fontSize: 10.5,
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            cursor: 'pointer',
                            borderBottom: '1.5px solid var(--ink)',
                          }
                    }
                  >
                    Undo
                  </button>
                </div>
              )}

              {prop && prop.status === 'skipped' && (
                <div className="t-skipped-receipt">
                  <span>Skipped edit for {prop.targetLabel}</span>
                  <button
                    type="button"
                    className={isAtelier ? 't-atelier-btn-ghost' : undefined}
                    onClick={() => onRefineProposal(prop.id, 'Suggest an alternative angle')}
                    style={
                      isAtelier
                        ? { padding: '3px 9px', fontSize: 12.5 }
                        : {
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--n700)',
                            fontFamily: 'var(--font-mono)',
                            fontSize: 10.5,
                            cursor: 'pointer',
                          }
                    }
                  >
                    Retry
                  </button>
                </div>
              )}

              {/* Card Type 2: Selectable Resource List Card */}
              {msg.resources && (
                <div className="t-coach-card">
                  <div className="t-coach-card-head">
                    <span>{msg.resources.heading}</span>
                    <span className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                      {msg.resources.items.length} found
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '6px 10px 10px' }}>
                    {msg.resources.items.map((res) => (
                      <div key={res.id} className="t-coach-resource-row">
                        <div style={{ minWidth: 0, flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <span
                              style={{
                                fontWeight: 600,
                                fontSize: 13,
                                color: 'var(--ink)',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {res.title}
                            </span>
                            {res.fitScore !== undefined && (
                              <span
                                className="t-mono"
                                style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: 4,
                                  fontSize: 11,
                                  fontWeight: 600,
                                  color: res.fitScore >= 75 ? 'var(--green)' : res.fitScore < 50 ? 'var(--alarm)' : 'var(--ink)',
                                  flexShrink: 0,
                                }}
                              >
                                {res.fitScore >= 75 && <span className="t-signal-up" aria-hidden="true" />}
                                {res.fitScore < 50 && <span className="t-signal-down" aria-hidden="true" />}
                                <span>{Math.round(res.fitScore)}%</span>
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: 12, color: 'var(--n500)', marginTop: 2 }}>{res.subtitle}</div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0 }}>
                          {onPreviewResource && (
                            <button
                              type="button"
                              className="t-atelier-icon-btn"
                              title={`Preview ${res.title}`}
                              aria-label={`Preview ${res.title}`}
                              onClick={() => onPreviewResource(res)}
                            >
                              <TailoredIcon name="eye" size={14} />
                            </button>
                          )}
                          {onSelectResource && (
                            <button
                              type="button"
                              className="t-atelier-btn-tonal"
                              style={{ padding: '5px 10px', fontSize: 12 }}
                              onClick={() => onSelectResource(res)}
                            >
                              {res.primaryLabel}
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Card Type 3: Cross-Page Confirm Action Card */}
              {msg.actionCard && msg.actionCard.status === 'pending' && (
                <div className="t-coach-card">
                  <div className="t-coach-card-head">
                    <span>Cross-Page Action</span>
                    <span className="t-dash-tag t-dash-tag--mist">{msg.actionCard.targetBadge}</span>
                  </div>
                  <div style={{ padding: '8px 14px 10px' }}>
                    <div style={{ fontWeight: 600, fontSize: 13.5, color: 'var(--ink)' }}>
                      {msg.actionCard.title}
                    </div>
                    <div style={{ fontSize: 12.5, color: 'var(--n700)', marginTop: 3, lineHeight: 1.48 }}>
                      {msg.actionCard.description}
                    </div>
                  </div>
                  <div className="t-proposal-foot">
                    <button
                      type="button"
                      className="t-atelier-btn-primary"
                      onClick={() => onConfirmAction?.(msg.actionCard!.id)}
                    >
                      <TailoredIcon name="check" size={12} />
                      <span>{msg.actionCard.confirmLabel}</span>
                    </button>
                    <button
                      type="button"
                      className="t-atelier-btn-ghost"
                      onClick={() => onCancelAction?.(msg.actionCard!.id)}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {msg.actionCard && msg.actionCard.status === 'confirmed' && (
                <div className="t-applied-receipt">
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <span className="t-signal-up" aria-hidden="true" />
                    <span>Done · {msg.actionCard.title}</span>
                  </span>
                </div>
              )}

              {msg.actionCard && msg.actionCard.status === 'cancelled' && (
                <div className="t-skipped-receipt">
                  <span>Cancelled · {msg.actionCard.title}</span>
                </div>
              )}

              {/* Card Type 4: Workspace Audit Card */}
              {msg.audit && (
                <div className="t-coach-card">
                  <div className="t-coach-card-head">
                    <span>{msg.audit.heading}</span>
                    <span className="t-mono" style={{ fontSize: 11, color: 'var(--n500)' }}>
                      {msg.audit.items.length}
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '6px 10px 10px' }}>
                    {msg.audit.items.map((aud) => (
                      <div key={aud.id} className="t-coach-audit-row">
                        <span
                          className={aud.sentiment === 'up' ? 't-signal-up' : 't-signal-down'}
                          style={{ marginTop: 5 }}
                          aria-hidden="true"
                        />
                        <div style={{ minWidth: 0, flex: 1 }}>
                          <div style={{ fontWeight: 600, fontSize: 12.5, color: 'var(--ink)' }}>{aud.title}</div>
                          <div style={{ fontSize: 12, color: 'var(--n500)', marginTop: 1 }}>{aud.detail}</div>
                        </div>
                        {aud.actionLabel && onAuditAction && (
                          <button
                            type="button"
                            className="t-atelier-btn-tonal"
                            style={{ padding: '4px 10px', fontSize: 11.5 }}
                            onClick={() => onAuditAction(aud)}
                          >
                            {aud.actionLabel}
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {isStreaming &&
          (isAtelier ? (
            <div className="t-atelier-thinking-live">
              <span className="t-atelier-thinking-notch" />
              <span>Drafting grounded edit...</span>
            </div>
          ) : (
            <div className="t-thinking-accordion">
              Checking Master Profile &amp; composing grounded suggestion...
            </div>
          ))}
      </div>

      {!autoScrollLocked && (
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 4 }}>
          <button
            type="button"
            className="t-btn t-btn--ink t-btn--sm"
            onClick={() => {
              setAutoScrollLocked(true);
              if (streamRef.current) streamRef.current.scrollTop = streamRef.current.scrollHeight;
            }}
          >
            Jump to latest
          </button>
        </div>
      )}

      {/* Conditional Starter Chips (only when conversation has <= 1 turn) */}
      {messages.length <= 1 && starterPrompts.length > 0 && (
        <div
          className={isAtelier ? 't-atelier-starters' : undefined}
          style={isAtelier ? undefined : { padding: '0 16px 4px', display: 'flex', gap: 6, flexWrap: 'wrap' }}
        >
          {starterPrompts.map((sp) => (
            <button
              key={sp}
              type="button"
              onClick={() => onSendMessage(sp, mode)}
              className={isAtelier ? 't-atelier-starter-btn' : 't-chip t-chip--notch'}
              style={isAtelier ? undefined : { cursor: 'pointer', background: 'var(--chalk)' }}
            >
              {sp}
            </button>
          ))}
        </div>
      )}

      {/* 3. Floating Rounded-Diagonal Composer Dock (16px inset) */}
      <div className="t-composer-wrap">
        <div className="t-composer-dock">
          {focusedAnchor && (
            <div className="t-composer-target-rim">
              <span>Focused: {focusedAnchor.label}</span>
              <button
                type="button"
                onClick={onClearFocusedAnchor}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: 2 }}
                aria-label="Clear target anchor"
              >
                <TailoredIcon name="close" size={12} />
              </button>
            </div>
          )}

          <textarea
            ref={inputRef}
            rows={2}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitDraft();
              }
            }}
            className="t-composer-input"
            placeholder={
              isAtelier
                ? 'Ask to sharpen a bullet, add a metric, or tighten...'
                : 'Ask to tighten phrasing, quantify a real win, or @ target a section...'
            }
          />

          <div className="t-composer-bar">
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {isAtelier && enableWorkspaceMentions && (
                <div className="t-atelier-mode-wrap" ref={mentionWrapRef}>
                  <button
                    type="button"
                    className={`t-atelier-mode-btn ${isMentionOpen ? 't-atelier-mode-btn--open' : ''}`}
                    onClick={() => {
                      setIsMentionOpen((v) => !v);
                      setIsModeOpen(false);
                    }}
                    title="Reference workspace CVs, Letters, Pipeline, or Profile"
                    aria-haspopup="menu"
                    aria-expanded={isMentionOpen}
                  >
                    <span style={{ fontWeight: 600 }}>@</span>
                  </button>
                  {isMentionOpen && (
                    <div className="t-atelier-mode-menu" style={{ minWidth: 204 }} role="menu" aria-label="Workspace references">
                      {[
                        { token: '@Saved CVs', hint: 'Preview or attach' },
                        { token: '@Cover Letters', hint: 'Past outreach hooks' },
                        { token: '@Pipeline', hint: 'Follow-ups & stages' },
                        { token: '@Jobs', hint: 'Radar matches' },
                        { token: '@Master Profile', hint: 'Projects & gaps' },
                      ].map((item) => (
                        <button
                          key={item.token}
                          type="button"
                          role="menuitem"
                          className="t-atelier-mode-option"
                          onClick={() => {
                            setDraft((prev) => `${prev ? `${prev.trim()} ` : ''}${item.token} `);
                            setIsMentionOpen(false);
                            setTimeout(() => inputRef.current?.focus(), 10);
                          }}
                        >
                          <span style={{ fontWeight: 600 }}>{item.token}</span>
                          <span style={{ fontSize: 11, color: 'var(--n500)' }}>{item.hint}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {isAtelier ? (
                <div className="t-atelier-mode-wrap" ref={modeWrapRef}>
                  <button
                    type="button"
                    className={`t-atelier-mode-btn ${isModeOpen ? 't-atelier-mode-btn--open' : ''}`}
                    onClick={() => {
                      setIsModeOpen((v) => !v);
                      setIsMentionOpen(false);
                    }}
                    aria-haspopup="listbox"
                    aria-expanded={isModeOpen}
                  >
                    <span>{mode}</span>
                    <TailoredIcon name="chevronDown" size={11} />
                  </button>
                  {isModeOpen && (
                    <div className="t-atelier-mode-menu" role="listbox" aria-label="Assistant mode">
                      {modes.map((m) => (
                        <button
                          key={m}
                          type="button"
                          role="option"
                          aria-selected={mode === m}
                          className={`t-atelier-mode-option ${mode === m ? 't-atelier-mode-option--active' : ''}`}
                          onClick={() => {
                            onChangeMode(m);
                            setIsModeOpen(false);
                          }}
                        >
                          <span>{m}</span>
                          {mode === m && <TailoredIcon name="check" size={12} color="var(--ink)" />}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <select
                  value={mode}
                  onChange={(e) => onChangeMode(e.target.value)}
                  aria-label="Assistant mode"
                  style={{
                    background: 'transparent',
                    border: '1px solid var(--n300)',
                    padding: '3px 7px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 10.5,
                    textTransform: 'uppercase',
                    color: 'var(--ink)',
                  }}
                >
                  {modes.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              )}
              <span className="t-mono" style={{ fontSize: 10.5, color: 'var(--n500)', whiteSpace: 'nowrap', flexShrink: 0 }}>
                0 cr
              </span>
            </div>

            {isStreaming ? (
              <button
                type="button"
                onClick={onStopStreaming}
                className={isAtelier ? 't-atelier-btn-tonal' : 't-btn t-btn--ink t-btn--sm'}
              >
                <TailoredIcon name="stop" size={12} />
                <span>Stop</span>
              </button>
            ) : (
              <button
                type="button"
                disabled={!draft.trim()}
                onClick={submitDraft}
                className={isAtelier ? 't-atelier-send-btn' : 't-btn t-btn--primary t-btn--sm'}
              >
                <TailoredIcon name="send" size={12} />
                <span>Send</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};
