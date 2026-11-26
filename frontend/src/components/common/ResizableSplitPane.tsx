import React, { useState, useRef, useEffect, useCallback } from 'react';

export interface ResizableSplitPaneProps {
  storageKey: string;
  defaultLeftPct?: number;
  minLeftPx?: number;
  minRightPx?: number;
  left: React.ReactNode;
  right: React.ReactNode;
  swapped?: boolean;
  hideSecondary?: boolean;
  height?: string;
}

export const ResizableSplitPane: React.FC<ResizableSplitPaneProps> = ({
  storageKey,
  defaultLeftPct = 40,
  minLeftPx = 320,
  minRightPx = 360,
  left,
  right,
  swapped = false,
  hideSecondary = false,
  height = '100%',
}) => {
  const fullKey = `tailored_split_${storageKey}`;
  const containerRef = useRef<HTMLDivElement>(null);
  const [leftPct, setLeftPct] = useState<number>(() => {
    const raw = localStorage.getItem(fullKey);
    const parsed = raw ? parseFloat(raw) : NaN;
    return Number.isFinite(parsed) && parsed >= 20 && parsed <= 80 ? parsed : defaultLeftPct;
  });
  const [dragging, setDragging] = useState(false);

  const persist = useCallback(
    (pct: number) => {
      try {
        localStorage.setItem(fullKey, pct.toFixed(2));
      } catch {
        // ignore storage restrictions
      }
    },
    [fullKey]
  );

  useEffect(() => {
    if (!dragging) return;
    const onMove = (e: MouseEvent) => {
      const el = containerRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      if (rect.width <= 0) return;
      const rawX = e.clientX - rect.left;
      const minPct = (minLeftPx / rect.width) * 100;
      const maxPct = 100 - (minRightPx / rect.width) * 100;
      const next = Math.max(minPct, Math.min(maxPct, (rawX / rect.width) * 100));
      setLeftPct(next);
      persist(next);
    };
    const onUp = () => setDragging(false);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, [dragging, minLeftPx, minRightPx, persist]);

  const resetSplit = () => {
    setLeftPct(defaultLeftPct);
    persist(defaultLeftPct);
  };

  if (hideSecondary) {
    return (
      <div ref={containerRef} className="t-split-container" style={{ height }}>
        <div className="t-split-pane" style={{ flex: 1 }}>
          {left}
        </div>
      </div>
    );
  }

  const firstPane = swapped ? right : left;
  const secondPane = swapped ? left : right;
  const firstPct = swapped ? 100 - leftPct : leftPct;

  return (
    <div ref={containerRef} className="t-split-container" style={{ height }}>
      <div className="t-split-pane" style={{ width: `${firstPct}%`, flexShrink: 0 }}>
        {firstPane}
      </div>
      <div
        role="separator"
        aria-orientation="vertical"
        title="Drag to resize · Double-click to reset"
        className={`t-splitter ${dragging ? 't-splitter--dragging' : ''}`}
        onMouseDown={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDoubleClick={resetSplit}
      />
      <div className="t-split-pane" style={{ flex: 1 }}>
        {secondPane}
      </div>
    </div>
  );
};
