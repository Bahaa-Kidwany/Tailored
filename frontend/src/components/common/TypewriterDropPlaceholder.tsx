import React, { useEffect, useState } from 'react';
import { TailoredIcon, type BrandIconName } from '../../brand/TailoredIcons';

export interface TypewriterPromptItem {
  icon: BrandIconName;
  text: string;
}

export interface TypewriterDropPlaceholderProps {
  items: TypewriterPromptItem[];
  visible: boolean;
  tone?: 'dark' | 'light';
}

interface TypewriterState {
  itemIdx: number;
  charCount: number;
  phase: 'typing' | 'holding' | 'deleting' | 'switching';
}

/**
 * Animated typewriter overlay displaying one icon + rotating prompt at a time.
 */
export const TypewriterDropPlaceholder: React.FC<TypewriterDropPlaceholderProps> = ({
  items,
  visible,
  tone = 'dark',
}) => {
  const [state, setState] = useState<TypewriterState>({
    itemIdx: 0,
    charCount: 0,
    phase: 'typing',
  });

  useEffect(() => {
    if (!visible || items.length === 0) return;

    const prefersReduced =
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReduced) {
      const id = window.setTimeout(() => {
        setState((prev) => {
          const nextIdx = (prev.itemIdx + 1) % items.length;
          return {
            itemIdx: nextIdx,
            charCount: items[nextIdx]?.text.length || 0,
            phase: 'holding',
          };
        });
      }, 3000);
      return () => window.clearTimeout(id);
    }

    const currentItem = items[state.itemIdx % items.length];
    const fullLen = currentItem.text.length;

    let delay = 40;
    if (state.phase === 'typing') {
      delay = state.charCount >= fullLen ? 1650 : 40;
    } else if (state.phase === 'holding') {
      delay = 1650;
    } else if (state.phase === 'deleting') {
      delay = state.charCount <= 0 ? 220 : 22;
    } else {
      delay = 220;
    }

    const timer = window.setTimeout(() => {
      setState((prev) => {
        const len = items[prev.itemIdx % items.length]?.text.length || 0;
        if (prev.phase === 'typing') {
          const nextCount = Math.min(len, prev.charCount + 1);
          return {
            itemIdx: prev.itemIdx,
            charCount: nextCount,
            phase: nextCount >= len ? 'holding' : 'typing',
          };
        }
        if (prev.phase === 'holding') {
          return {
            itemIdx: prev.itemIdx,
            charCount: len,
            phase: 'deleting',
          };
        }
        if (prev.phase === 'deleting') {
          const nextCount = Math.max(0, prev.charCount - 1);
          return {
            itemIdx: prev.itemIdx,
            charCount: nextCount,
            phase: nextCount <= 0 ? 'switching' : 'deleting',
          };
        }
        return {
          itemIdx: (prev.itemIdx + 1) % items.length,
          charCount: 0,
          phase: 'typing',
        };
      });
    }, delay);

    return () => window.clearTimeout(timer);
  }, [visible, items, state]);

  if (!visible || items.length === 0) return null;

  const prefersReduced =
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const current = items[state.itemIdx % items.length];
  const shownText = prefersReduced ? current.text : current.text.slice(0, state.charCount);

  return (
    <div
      className={`t-typewriter-overlay ${tone === 'light' ? 't-typewriter-overlay--light' : ''}`}
      aria-hidden="true"
    >
      <span className="t-typewriter-icon">
        <TailoredIcon
          name={current.icon}
          size={14}
          color={tone === 'light' ? 'var(--dye)' : 'var(--kraft)'}
        />
      </span>
      <span className="t-typewriter-text">
        {shownText}
        {!prefersReduced && <span className="t-typewriter-caret" />}
      </span>
    </div>
  );
};
