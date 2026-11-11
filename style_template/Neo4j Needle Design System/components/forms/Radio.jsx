import React from 'react';

export function Radio({ label, value, name, isChecked = false, onChange, isDisabled = false, helpText }) {
  return (
    <label style={{ display: 'inline-flex', gap: 8, alignItems: 'flex-start', cursor: isDisabled ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)' }}>
      <span style={{
        width: 18, height: 18, flex: '0 0 18px', marginTop: 1, borderRadius: 9999, boxSizing: 'border-box',
        background: isDisabled ? 'var(--disabled-fill)' : 'var(--surface)',
        border: `${isChecked ? 5 : 1}px solid ${isDisabled ? 'var(--disabled-border)' : isChecked ? 'var(--primary-fill)' : 'var(--border-strong)'}`,
        transition: 'border 140ms ease-out',
      }}>
        <input type="radio" name={name} value={value} checked={isChecked} disabled={isDisabled}
          onChange={() => onChange && onChange(value)} style={{ position: 'absolute', opacity: 0, width: 0, height: 0 }} />
      </span>
      <span>
        <span style={{ fontSize: 14, lineHeight: 1.43, color: isDisabled ? 'var(--disabled-text)' : 'var(--text)' }}>{label}</span>
        {helpText && <span style={{ display: 'block', fontSize: 12, lineHeight: 1.67, color: isDisabled ? 'var(--disabled-text)' : 'var(--text-weaker)' }}>{helpText}</span>}
      </span>
    </label>
  );
}
