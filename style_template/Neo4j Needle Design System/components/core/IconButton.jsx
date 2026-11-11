import React from 'react';

const SIZES = { small: 28, medium: 36, large: 44 };

export function IconButton({ children, ariaLabel, size = 'medium', fill = 'text', color = 'neutral', isDisabled = false, isActive = false, onClick, ...rest }) {
  const [hover, setHover] = React.useState(false);
  const [press, setPress] = React.useState(false);
  const d = SIZES[size] || SIZES.medium;
  const accent = color === 'danger' ? 'var(--danger-text)' : color === 'primary' ? 'var(--primary-icon)' : 'var(--text-weak)';

  const bg = press || isActive ? 'var(--neutral-pressed)' : hover ? 'var(--neutral-hover)' : 'transparent';

  return (
    <button
      type="button" aria-label={ariaLabel} disabled={isDisabled} onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => { setHover(false); setPress(false); }}
      onMouseDown={() => setPress(true)} onMouseUp={() => setPress(false)}
      style={{
        width: d, height: d, display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        borderRadius: 'var(--radius-control)', boxSizing: 'border-box',
        background: fill === 'outlined' ? (bg === 'transparent' ? 'var(--surface)' : bg) : bg,
        border: fill === 'outlined' ? '1px solid var(--border-strong)' : '1px solid transparent',
        color: isDisabled ? 'var(--disabled-text)' : accent, cursor: isDisabled ? 'not-allowed' : 'pointer',
        transition: 'background-color 140ms ease-out, color 140ms ease-out', padding: 0,
      }}
      {...rest}
    >
      {children}
    </button>
  );
}
