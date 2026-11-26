import React, { useState, useEffect, useRef } from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { TailoredIcon } from '../../brand/TailoredIcons';

export const CommandPalette: React.FC = () => {
  const {
    isCommandPaletteOpen,
    setIsCommandPaletteOpen,
    navigateTo,
    currentProfile,
    setPrimaryPersona,
    setActiveRegionalPhone,
    ingestJobUrlOrText,
    runLiveSweep,
    resetAllPaneWidths,
    radarJobs,
    openJobInStudio,
  } = useWorkspace();

  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isCommandPaletteOpen) {
      setQuery('');
      setTimeout(() => inputRef.current?.focus(), 20);
    }
  }, [isCommandPaletteOpen]);

  if (!isCommandPaletteOpen) return null;

  const isUrlOrLongJd = /^https?:\/\//i.test(query.trim()) || query.trim().length > 80;
  const personas = currentProfile?.profile.career_personas || [];

  const commands = [
    { label: 'Go to Dashboard', group: 'Navigate', onRun: () => navigateTo('/dashboard') },
    { label: 'Go to Job Radar', group: 'Navigate', onRun: () => navigateTo('/radar') },
    { label: 'Go to Saved Shortlist', group: 'Navigate', onRun: () => navigateTo('/radar?tab=saved') },
    { label: 'Go to CV Studio & Saved CVs', group: 'Navigate', onRun: () => navigateTo('/studio') },
    { label: 'Go to Cover Letter Studio', group: 'Navigate', onRun: () => navigateTo('/cover-letters') },
    { label: 'Go to Application Pipeline', group: 'Navigate', onRun: () => navigateTo('/pipeline') },
    { label: 'Go to Master Profile', group: 'Navigate', onRun: () => navigateTo('/profile') },
    { label: 'Go to Plans & Credit Packs', group: 'Navigate', onRun: () => navigateTo('/plans') },
    { label: 'Go to Account & Security', group: 'Navigate', onRun: () => navigateTo('/account') },
    { label: 'Go to Notifications Inbox', group: 'Navigate', onRun: () => navigateTo('/notifications') },
    { label: 'Run Live Radar Sweep (Free)', group: 'Action', onRun: () => runLiveSweep() },
    { label: 'Reset All Saved Pane Widths', group: 'Ergonomics', onRun: () => resetAllPaneWidths() },
    { label: 'Switch Regional Phone: +20 Egypt', group: 'Context', onRun: () => setActiveRegionalPhone('+20') },
    { label: 'Switch Regional Phone: +966 Saudi Arabia', group: 'Context', onRun: () => setActiveRegionalPhone('+966') },
    { label: 'Switch Regional Phone: +971 UAE', group: 'Context', onRun: () => setActiveRegionalPhone('+971') },
    ...personas.map((p) => ({
      label: `Switch Persona: ${p.target_title}`,
      group: 'Persona',
      onRun: () => setPrimaryPersona(p.persona_id),
    })),
    ...radarJobs.slice(0, 5).map((j) => ({
      label: `Open in CV Studio: ${j.company_name} — ${j.title}`,
      group: 'Job',
      onRun: () => openJobInStudio(j),
    })),
  ];

  const qLow = query.toLowerCase().trim();
  const filtered = qLow
    ? commands.filter((c) => c.label.toLowerCase().includes(qLow) || c.group.toLowerCase().includes(qLow))
    : commands.slice(0, 10);

  const handleEnter = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isUrlOrLongJd) {
      setIsCommandPaletteOpen(false);
      await ingestJobUrlOrText(query, { onlySaveInterest: true });
      navigateTo('/radar?tab=saved');
      return;
    }
    if (filtered[0]) {
      setIsCommandPaletteOpen(false);
      filtered[0].onRun();
    }
  };

  return (
    <div className="t-backdrop" onClick={() => setIsCommandPaletteOpen(false)}>
      <div
        className="t-modal"
        style={{ width: '100%', maxWidth: 600, padding: 0, overflow: 'hidden' }}
        onClick={(e) => e.stopPropagation()}
      >
        <form
          onSubmit={handleEnter}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '14px 18px',
            borderBottom: '1.5px solid var(--ink)',
            background: 'var(--chalk)',
          }}
        >
          <TailoredIcon name="search" size={18} />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Jump to page, switch persona, or paste a job URL / description..."
            style={{
              flex: 1,
              border: 'none',
              background: 'transparent',
              fontFamily: 'var(--font-ui)',
              fontSize: 15,
              color: 'var(--ink)',
              outline: 'none',
            }}
          />
          <span className="t-label" style={{ color: 'var(--n500)' }}>
            ESC
          </span>
        </form>

        <div style={{ maxHeight: 380, overflowY: 'auto' }}>
          {isUrlOrLongJd && (
            <button
              type="button"
              onClick={async () => {
                setIsCommandPaletteOpen(false);
                await ingestJobUrlOrText(query, { onlySaveInterest: true });
                navigateTo('/radar?tab=saved');
              }}
              style={{
                width: '100%',
                textAlign: 'left',
                padding: '14px 18px',
                background: 'var(--kraft)',
                border: 'none',
                borderBottom: '1.5px solid var(--ink)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{ fontWeight: 600 }}>
                Ingest pasted job &amp; score fit into Saved Shortlist (Free)
              </span>
              <span className="t-label">Enter</span>
            </button>
          )}

          {filtered.map((cmd, idx) => (
            <button
              key={`${cmd.group}_${cmd.label}_${idx}`}
              type="button"
              onClick={() => {
                setIsCommandPaletteOpen(false);
                cmd.onRun();
              }}
              style={{
                width: '100%',
                textAlign: 'left',
                padding: '11px 18px',
                background: 'transparent',
                border: 'none',
                borderBottom: '1px solid var(--n100)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontFamily: 'var(--font-ui)',
                fontSize: 14,
                color: 'var(--ink)',
              }}
            >
              <span>{cmd.label}</span>
              <span className="t-label" style={{ color: 'var(--n500)' }}>
                {cmd.group}
              </span>
            </button>
          ))}

          {!isUrlOrLongJd && filtered.length === 0 && (
            <div style={{ padding: 24, textAlign: 'center', color: 'var(--n500)', fontSize: 14 }}>
              No matching commands. Paste any job URL to ingest it immediately.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
