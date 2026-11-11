import React from 'react';

export function Checkbox({ label, isChecked = false, isIndeterminate = false, onChange, isDisabled = false, helpText }) {
  const on = isChecked || isIndeterminate;
  return (
    <label style={{ display: 'inline-flex', gap: 8, alignItems: 'flex-start', cursor: isDisabled ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)' }}>
      <span style={{
        width: 18, height: 18, flex: '0 0 18px', marginTop: 1, borderRadius: 'var(--radius-xs)', boxSizing: 'border-box',
        background: isDisabled ? 'var(--disabled-fill)' : on ? 'var(--primary-fill)' : 'var(--surface)',
        border: `1px solid ${isDisabled ? 'var(--disabled-border)' : on ? 'var(--primary-fill)' : 'var(--border-strong)'}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: 'background-color 140ms ease-out, border-color 140ms ease-out',
      }}>
        <input type="checkbox" checked={isChecked} disabled={isDisabled} onChange={(e) => onChange && onChange(e.target.checked)}
          style={{ position: 'absolute', opacity: 0, width: 0, height: 0 }} />
        {isIndeterminate
          ? <svg width="10" height="10" viewBox="0 0 24 24" stroke={isDisabled ? 'var(--disabled-text)' : 'var(--text-inverse)'} strokeWidth="4" strokeLinecap="round"><path d="M5 12h14" /></svg>
          : isChecked && <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={isDisabled ? 'var(--disabled-text)' : 'var(--text-inverse)'} strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5" /></svg>}
      </span>
      <span>
        <span style={{ fontSize: 14, lineHeight: 1.43, color: isDisabled ? 'var(--disabled-text)' : 'var(--text)' }}>{label}</span>
        {helpText && <span style={{ display: 'block', fontSize: 12, lineHeight: 1.67, color: isDisabled ? 'var(--disabled-text)' : 'var(--text-weaker)' }}>{helpText}</span>}
      </span>
    </label>
  );
}
