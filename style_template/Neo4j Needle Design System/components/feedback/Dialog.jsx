import React from 'react';

export function Dialog({ isOpen = true, title, children, actions, onClose, size = 'medium' }) {
  if (!isOpen) return null;
  const w = size === 'small' ? 400 : size === 'large' ? 720 : 560;
  return (
    <div role="dialog" aria-modal="true" onClick={onClose} style={{
      position: 'absolute', inset: 0, background: 'rgba(26,27,29,0.45)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, zIndex: 40,
    }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        width: w, maxWidth: '100%', background: 'var(--surface)', borderRadius: 'var(--radius-card-lg)',
        boxShadow: 'var(--elevation-overlay)', border: '1px solid var(--border-weak)',
        fontFamily: 'var(--font-sans)', overflow: 'hidden',
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, padding: '24px 24px 0' }}>
          <div style={{ flex: 1, fontWeight: 700, fontSize: 20, lineHeight: 1.4, letterSpacing: '0.016rem', color: 'var(--text)' }}>{title}</div>
          {onClose && (
            <button type="button" aria-label="Close" onClick={onClose} style={{ background: 'none', border: 0, padding: 4, margin: -4, cursor: 'pointer', color: 'var(--text-weak)', display: 'flex' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12" /></svg>
            </button>
          )}
        </div>
        <div style={{ padding: '12px 24px 24px', fontSize: 14, lineHeight: 1.43, color: 'var(--text-weak)' }}>{children}</div>
        {actions && <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: 16, borderTop: '1px solid var(--border-weak)', background: 'var(--canvas)' }}>{actions}</div>}
      </div>
    </div>
  );
}
