import React from 'react';

export function Badge({ children, color = 'neutral', hasDot = false }) {
  const map = {
    neutral: { fg: 'var(--text-weak)', bg: 'var(--canvas)', dot: 'var(--text-weakest)' },
    primary: { fg: 'var(--primary-text)', bg: 'var(--primary-bg)', dot: 'var(--primary-fill)' },
    success: { fg: 'var(--success-text)', bg: 'var(--success-bg)', dot: 'var(--success-text)' },
    warning: { fg: 'var(--warning-text)', bg: 'var(--warning-bg)', dot: 'var(--warning-text)' },
    danger: { fg: 'var(--danger-text)', bg: 'var(--danger-bg)', dot: 'var(--danger-text)' },
    discovery: { fg: 'var(--discovery-text)', bg: 'var(--discovery-bg)', dot: 'var(--discovery-text)' },
  };
  const c = map[color] || map.neutral;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6, height: 24, padding: '0 8px',
      borderRadius: 'var(--radius-xs)', background: c.bg, color: c.fg,
      fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: 12, lineHeight: 1, boxSizing: 'border-box',
    }}>
      {hasDot && <span style={{ width: 6, height: 6, borderRadius: 9999, background: c.dot }} />}
      {children}
    </span>
  );
}
