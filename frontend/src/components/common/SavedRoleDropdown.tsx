import React, { useEffect, useMemo, useRef, useState } from 'react';
import { TailoredIcon } from '../../brand/TailoredIcons';
import { cleanCompanyName, cleanTargetJobTitle } from '../../services/cvFitApi';
import type { JobItem } from '../../services/jobsApi';
import type { UserProfilePayload } from '../../services/profileApi';
import { evaluateAllPersonas } from '../../utils/fitEngine';

export interface SavedRoleDropdownProps {
  jobs: JobItem[];
  profile: UserProfilePayload;
  label?: string;
  placeholder?: string;
  tone?: 'dark' | 'light';
  onSelectRole: (job: JobItem) => void;
}

/**
 * Custom architectural dropdown menu for starting a new CV or Cover Letter from a saved role.
 */
export const SavedRoleDropdown: React.FC<SavedRoleDropdownProps> = ({
  jobs,
  profile,
  label = 'OR START FROM A SAVED ROLE',
  placeholder = 'Select a saved role from Radar or Shortlist...',
  tone = 'dark',
  onSelectRole,
}) => {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onMouseDown = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false);
      }
    };
    window.addEventListener('mousedown', onMouseDown);
    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [open]);

  const roleOptions = useMemo(() => {
    const seen = new Set<string>();
    const list: Array<{
      job: JobItem;
      company: string;
      role: string;
      fitScore: number;
    }> = [];

    for (const job of jobs) {
      const company = cleanCompanyName(job.company_name);
      const role = cleanTargetJobTitle(job.title);
      const key = `${company.toLowerCase()}::${role.toLowerCase()}`;
      if (seen.has(key)) continue;
      seen.add(key);
      const fit = Math.round(
        job.fit_score && job.fit_score > 0
          ? job.fit_score
          : evaluateAllPersonas(job, profile).best.overallScore
      );
      list.push({ job, company, role, fitScore: fit });
    }
    return list;
  }, [jobs, profile]);

  if (roleOptions.length === 0) return null;

  return (
    <div
      ref={wrapRef}
      className={`t-cl-role-dropdown ${tone === 'light' ? 't-cl-role-dropdown--light' : ''}`}
    >
      <div
        className="t-mono"
        style={{
          fontSize: 10.5,
          letterSpacing: '0.07em',
          color: tone === 'light' ? 'var(--n500)' : 'rgba(229, 224, 218, 0.56)',
          marginBottom: 7,
        }}
      >
        {label}
      </div>

      <button
        type="button"
        className={`t-cl-role-dropdown-btn ${open ? 't-cl-role-dropdown-btn--open' : ''}`}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 9, minWidth: 0 }}>
          <TailoredIcon name="job" size={14} color={tone === 'light' ? 'var(--dye)' : 'var(--kraft)'} />
          <span
            style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              color: tone === 'light' ? 'var(--n700)' : 'rgba(229, 224, 218, 0.86)',
            }}
          >
            {placeholder}
          </span>
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <span
            className="t-mono"
            style={{
              fontSize: 10.5,
              color: tone === 'light' ? 'var(--dye)' : 'var(--kraft)',
              opacity: 0.9,
            }}
          >
            {roleOptions.length} roles
          </span>
          <TailoredIcon
            name="chevronDown"
            size={12}
            color={tone === 'light' ? 'var(--n700)' : 'var(--kraft)'}
            style={{
              transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.16s ease',
            }}
          />
        </span>
      </button>

      {open && (
        <div className="t-cl-role-dropdown-menu" role="listbox" aria-label={label}>
          {roleOptions.map(({ job, company, role, fitScore }) => (
            <button
              key={job.id}
              type="button"
              role="option"
              aria-selected={false}
              className="t-cl-role-dropdown-item"
              onClick={() => {
                setOpen(false);
                onSelectRole(job);
              }}
            >
              <div style={{ minWidth: 0, flex: 1 }}>
                <div
                  style={{
                    fontWeight: 600,
                    fontSize: 13,
                    color: 'var(--ink)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {company} · {role}
                </div>
                <div
                  className="t-mono"
                  style={{
                    fontSize: 10.5,
                    color: 'var(--n500)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    marginTop: 2,
                  }}
                >
                  {job.location || 'MENA / Remote'}
                  {job.location_type ? ` · ${job.location_type}` : ''}
                </div>
              </div>

              <span
                className={`t-dash-tag ${fitScore >= 75 ? 't-dash-tag--green' : ''}`}
                style={{
                  flexShrink: 0,
                  ...(fitScore < 75
                    ? { background: 'rgba(227, 154, 27, 0.16)', color: 'var(--ink)' }
                    : {}),
                }}
              >
                {fitScore >= 75 && <span className="t-signal-up" aria-hidden="true" />}
                <span className="t-mono">{fitScore}% Fit</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
