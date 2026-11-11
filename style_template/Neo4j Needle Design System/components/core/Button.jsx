import React from 'react';

const SIZES = {
  small: { height: 28, padding: '0 12px', fontSize: 12, gap: 6 },
  medium: { height: 36, padding: '0 16px', fontSize: 14, gap: 8 },
  large: { height: 44, padding: '0 20px', fontSize: 16, gap: 8 },
};

export function Button({
  children, fill = 'filled', color = 'primary', size = 'medium',
  isDisabled = false, isLoading = false, isFullWidth = false,
  htmlAttributes = {}, onClick, ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const [press, setPress] = React.useState(false);
  const s = SIZES[size] || SIZES.medium;

  const tokens = color === 'danger'
    ? { base: 'var(--danger-text)', hover: 'var(--danger-hover)', pressed: 'var(--danger-pressed)', tint: 'var(--danger-bg)' }
    : { base: 'var(--primary-fill)', hover: 'var(--primary-hover)', pressed: 'var(--primary-pressed)', tint: 'var(--primary-bg)' };

  const accent = press ? tokens.pressed : hover ? tokens.hover : tokens.base;

  let style = {
    display: isFullWidth ? 'flex' : 'inline-flex', width: isFullWidth ? '100%' : undefined,
    alignItems: 'center', justifyContent: 'center', gap: s.gap,
    height: s.height, padding: s.padding, boxSizing: 'border-box',
    fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: s.fontSize, lineHeight: 1,
    letterSpacing: '0.016rem', borderRadius: 'var(--radius-control)',
    border: '1px solid transparent', cursor: isDisabled ? 'not-allowed' : 'pointer',
    transition: 'background-color 140ms ease-out, color 140ms ease-out, border-color 140ms ease-out',
    whiteSpace: 'nowrap',
  };

  if (fill === 'filled') {
    style = { ...style, background: color === 'neutral' ? 'var(--text)' : accent, color: 'var(--text-inverse)' };
    if (color === 'neutral') style.color = 'var(--text-inverse)';
  } else if (fill === 'outlined') {
    style = { ...style, background: press ? 'var(--neutral-pressed)' : hover ? 'var(--neutral-hover)' : 'transparent',
      color: color === 'neutral' ? 'var(--text)' : accent,
      borderColor: color === 'neutral' ? 'var(--border-strong)' : accent };
  } else {
    style = { ...style, background: press ? 'var(--neutral-pressed)' : hover ? 'var(--neutral-hover)' : 'transparent',
      color: color === 'neutral' ? 'var(--text)' : accent };
  }

  // DERIVED — the source spec defines no disabled token; see tokens/theme-light.css.
  if (isDisabled) {
    style = { ...style,
      background: fill === 'filled' ? 'var(--disabled-fill)' : 'transparent',
      color: 'var(--disabled-text)',
      borderColor: fill === 'outlined' ? 'var(--disabled-border)' : 'transparent' };
  }

  return (
    <button
      type="button" disabled={isDisabled || isLoading} style={style} onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => { setHover(false); setPress(false); }}
      onMouseDown={() => setPress(true)} onMouseUp={() => setPress(false)}
      {...htmlAttributes} {...rest}
    >
      {isLoading && <Spinner />}
      {children}
    </button>
  );
}

function Spinner() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="2" opacity="0.3" />
      <path d="M8 1.5A6.5 6.5 0 0 1 14.5 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <animateTransform attributeName="transform" type="rotate" from="0 8 8" to="360 8 8" dur="0.7s" repeatCount="indefinite" />
      </path>
    </svg>
  );
}
