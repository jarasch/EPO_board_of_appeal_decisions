import React from 'react';

export function Tag({ children, color = 'neutral', size = 'medium', onRemove }) {
  const map = {
    neutral: { fg: 'var(--text-weak)', bg: 'var(--canvas)', bd: 'var(--border-weak)' },
    primary: { fg: 'var(--primary-text)', bg: 'var(--primary-bg)', bd: 'var(--primary-border-weak)' },
    success: { fg: 'var(--success-text)', bg: 'var(--success-bg)', bd: 'var(--success-border-weak)' },
    warning: { fg: 'var(--warning-text)', bg: 'var(--warning-bg)', bd: 'var(--warning-border-weak)' },
    danger: { fg: 'var(--danger-text)', bg: 'var(--danger-bg)', bd: 'var(--danger-border-weak)' },
    discovery: { fg: 'var(--discovery-text)', bg: 'var(--discovery-bg)', bd: 'var(--discovery-border-weak)' },
  };
  const c = map[color] || map.neutral;
  const s = size === 'small' ? { h: 20, fs: 12, px: 8 } : { h: 24, fs: 12, px: 12 };
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6, height: s.h, padding: `0 ${s.px}px`,
      borderRadius: 'var(--radius-pill)', background: c.bg, color: c.fg, border: `1px solid ${c.bd}`,
      fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: s.fs, lineHeight: 1, whiteSpace: 'nowrap', boxSizing: 'border-box',
    }}>
      {children}
      {onRemove && (
        <button type="button" aria-label="Remove" onClick={onRemove} style={{ background: 'none', border: 0, padding: 0, color: 'inherit', cursor: 'pointer', display: 'inline-flex', opacity: 0.7 }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12" /></svg>
        </button>
      )}
    </span>
  );
}
