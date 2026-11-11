import React from 'react';

export function TextInput({ label, value, onChange, placeholder, helpText, errorText, isDisabled = false, isReadOnly = false, size = 'medium', leftIcon, rightIcon, type = 'text', isFullWidth = false }) {
  const [focus, setFocus] = React.useState(false);
  const h = size === 'small' ? 28 : size === 'large' ? 44 : 36;
  const invalid = Boolean(errorText);
  const border = isDisabled ? 'var(--disabled-border)' : invalid ? 'var(--danger-text)' : focus ? 'var(--primary-focus)' : 'var(--border-strong)';
  return (
    <label style={{ display: isFullWidth ? 'flex' : 'inline-flex', flexDirection: 'column', gap: 4, width: isFullWidth ? '100%' : undefined, fontFamily: 'var(--font-sans)' }}>
      {label && <span style={{ fontWeight: 700, fontSize: 14, lineHeight: 1.43, color: isDisabled ? 'var(--disabled-text)' : 'var(--text)' }}>{label}</span>}
      <span style={{
        display: 'flex', alignItems: 'center', gap: 8, height: h, padding: '0 12px', boxSizing: 'border-box',
        background: isDisabled ? 'var(--disabled-fill)' : 'var(--surface)', border: `1px solid ${border}`,
        outline: focus ? '2px solid var(--primary-focus)' : 'none', outlineOffset: 2,
        borderRadius: 'var(--radius-input)', transition: 'border-color 140ms ease-out',
        color: 'var(--text-weak)',
      }}>
        {leftIcon}
        <input
          type={type} value={value} placeholder={placeholder} disabled={isDisabled} readOnly={isReadOnly}
          onChange={(e) => onChange && onChange(e.target.value)}
          onFocus={() => setFocus(true)} onBlur={() => setFocus(false)}
          style={{
            flex: 1, minWidth: 0, border: 0, outline: 'none', background: 'transparent',
            fontFamily: 'var(--font-sans)', fontSize: size === 'small' ? 12 : 14,
            color: isDisabled ? 'var(--disabled-text)' : 'var(--text)', WebkitTextFillColor: isDisabled ? 'var(--disabled-text)' : undefined,
          }}
        />
        {rightIcon}
      </span>
      {(helpText || errorText) && (
        <span style={{ fontSize: 12, lineHeight: 1.67, color: invalid ? 'var(--danger-text)' : 'var(--text-weaker)' }}>{errorText || helpText}</span>
      )}
    </label>
  );
}
