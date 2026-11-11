import React from 'react';

export function Select({ label, value, onChange, options = [], placeholder = 'Select…', helpText, errorText, isDisabled = false, size = 'medium', isFullWidth = false }) {
  const [focus, setFocus] = React.useState(false);
  const h = size === 'small' ? 28 : size === 'large' ? 44 : 36;
  const invalid = Boolean(errorText);
  return (
    <label style={{ display: isFullWidth ? 'flex' : 'inline-flex', flexDirection: 'column', gap: 4, width: isFullWidth ? '100%' : undefined, fontFamily: 'var(--font-sans)' }}>
      {label && <span style={{ fontWeight: 700, fontSize: 14, lineHeight: 1.43, color: isDisabled ? 'var(--disabled-text)' : 'var(--text)' }}>{label}</span>}
      <span style={{ position: 'relative', display: 'block' }}>
        <select
          value={value} disabled={isDisabled} onChange={(e) => onChange && onChange(e.target.value)}
          onFocus={() => setFocus(true)} onBlur={() => setFocus(false)}
          style={{
            width: '100%', height: h, padding: '0 36px 0 12px', boxSizing: 'border-box', appearance: 'none',
            background: isDisabled ? 'var(--disabled-fill)' : 'var(--surface)',
            border: `1px solid ${isDisabled ? 'var(--disabled-border)' : invalid ? 'var(--danger-text)' : focus ? 'var(--primary-focus)' : 'var(--border-strong)'}`,
            outline: focus ? '2px solid var(--primary-focus)' : 'none', outlineOffset: 2,
            borderRadius: 'var(--radius-input)',
            fontFamily: 'var(--font-sans)', fontSize: size === 'small' ? 12 : 14,
            color: isDisabled ? 'var(--disabled-text)' : value ? 'var(--text)' : 'var(--text-weakest)',
            transition: 'border-color 140ms ease-out', cursor: isDisabled ? 'not-allowed' : 'pointer',
          }}
        >
          {!value && <option value="">{placeholder}</option>}
          {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-weak)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}><path d="m6 9 6 6 6-6" /></svg>
      </span>
      {(helpText || errorText) && <span style={{ fontSize: 12, lineHeight: 1.67, color: invalid ? 'var(--danger-text)' : 'var(--text-weaker)' }}>{errorText || helpText}</span>}
    </label>
  );
}
