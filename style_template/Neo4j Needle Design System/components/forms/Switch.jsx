import React from 'react';

export function Switch({ label, isChecked = false, onChange, isDisabled = false, size = 'medium' }) {
  const w = size === 'small' ? 32 : 40, h = size === 'small' ? 18 : 22, k = h - 6;
  return (
    <label style={{ display: 'inline-flex', gap: 8, alignItems: 'center', cursor: isDisabled ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)' }}>
      <span style={{
        width: w, height: h, flex: `0 0 ${w}px`, borderRadius: 9999, boxSizing: 'border-box', position: 'relative',
        background: isDisabled ? 'var(--disabled-fill)' : isChecked ? 'var(--primary-fill)' : 'var(--border-strong)',
        transition: 'background-color 140ms ease-out',
      }}>
        <input type="checkbox" checked={isChecked} disabled={isDisabled} onChange={(e) => onChange && onChange(e.target.checked)}
          style={{ position: 'absolute', opacity: 0, width: 0, height: 0 }} />
        <span style={{
          position: 'absolute', top: 3, left: isChecked ? w - k - 3 : 3, width: k, height: k, borderRadius: 9999,
          background: isDisabled ? 'var(--disabled-text)' : 'var(--surface)', boxShadow: 'var(--elevation-raised)', transition: 'left 140ms ease-out',
        }} />
      </span>
      {label && <span style={{ fontSize: 14, lineHeight: 1.43, color: isDisabled ? 'var(--disabled-text)' : 'var(--text)' }}>{label}</span>}
    </label>
  );
}
