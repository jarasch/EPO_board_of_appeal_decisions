import React from 'react';

export function Banner({ title, children, type = 'info', icon, onDismiss, actions }) {
  const map = {
    info: { fg: 'var(--primary-text)', bg: 'var(--primary-bg)', bd: 'var(--primary-border-weak)' },
    success: { fg: 'var(--success-text)', bg: 'var(--success-bg)', bd: 'var(--success-border-weak)' },
    warning: { fg: 'var(--warning-text)', bg: 'var(--warning-bg)', bd: 'var(--warning-border-weak)' },
    danger: { fg: 'var(--danger-text)', bg: 'var(--danger-bg)', bd: 'var(--danger-border-weak)' },
    discovery: { fg: 'var(--discovery-text)', bg: 'var(--discovery-bg)', bd: 'var(--discovery-border-weak)' },
  };
  const c = map[type] || map.info;
  return (
    <div role="status" style={{
      display: 'flex', gap: 12, padding: 16, background: c.bg, border: `1px solid ${c.bd}`,
      borderRadius: 'var(--radius-card)', fontFamily: 'var(--font-sans)',
    }}>
      {icon && <span style={{ color: c.fg, display: 'flex', flexShrink: 0, marginTop: 1 }}>{icon}</span>}
      <div style={{ flex: 1, minWidth: 0 }}>
        {title && <div style={{ fontWeight: 700, fontSize: 14, lineHeight: 1.43, letterSpacing: '0.016rem', color: c.fg }}>{title}</div>}
        {children && <div style={{ fontSize: 14, lineHeight: 1.43, color: 'var(--text-weak)', marginTop: title ? 4 : 0 }}>{children}</div>}
        {actions && <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>{actions}</div>}
      </div>
      {onDismiss && (
        <button type="button" aria-label="Dismiss" onClick={onDismiss} style={{ background: 'none', border: 0, padding: 0, cursor: 'pointer', color: 'var(--text-weak)', display: 'flex', height: 20 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12" /></svg>
        </button>
      )}
    </div>
  );
}
