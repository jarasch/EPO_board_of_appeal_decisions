import React from 'react';

export function Tabs({ items = [], value, onChange, size = 'medium' }) {
  const fs = size === 'small' ? 12 : 14;
  return (
    <div role="tablist" style={{ display: 'flex', gap: 4, borderBottom: '1px solid var(--border-weak)', fontFamily: 'var(--font-sans)' }}>
      {items.map((it) => {
        const active = it.value === value;
        return (
          <button key={it.value} role="tab" aria-selected={active} type="button"
            disabled={it.isDisabled}
            onClick={() => onChange && onChange(it.value)}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 8, padding: size === 'small' ? '6px 12px' : '8px 16px',
              background: 'transparent', border: 0, borderBottom: `2px solid ${active ? 'var(--primary-border)' : 'transparent'}`,
              marginBottom: -1, cursor: it.isDisabled ? 'not-allowed' : 'pointer', opacity: it.isDisabled ? 0.45 : 1,
              fontFamily: 'var(--font-sans)', fontWeight: active ? 700 : 600, fontSize: fs, lineHeight: 1.43,
              color: active ? 'var(--primary-text)' : 'var(--text-weak)',
              transition: 'color 140ms ease-out, border-color 140ms ease-out',
            }}>
            {it.icon}{it.label}
            {it.count != null && <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-weaker)' }}>{it.count}</span>}
          </button>
        );
      })}
    </div>
  );
}
