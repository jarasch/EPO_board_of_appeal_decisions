import React from 'react';

export function Tooltip({ children, content, placement = 'top' }) {
  const [open, setOpen] = React.useState(false);
  const pos = {
    top: { bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: 6 },
    bottom: { top: '100%', left: '50%', transform: 'translateX(-50%)', marginTop: 6 },
    left: { right: '100%', top: '50%', transform: 'translateY(-50%)', marginRight: 6 },
    right: { left: '100%', top: '50%', transform: 'translateY(-50%)', marginLeft: 6 },
  }[placement];
  return (
    <span style={{ position: 'relative', display: 'inline-flex' }}
      onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}>
      {children}
      {open && (
        <span role="tooltip" style={{
          position: 'absolute', ...pos, zIndex: 30, whiteSpace: 'nowrap',
          background: 'var(--text)', color: 'var(--text-inverse)',
          fontFamily: 'var(--font-sans)', fontSize: 12, lineHeight: 1.67,
          padding: '4px 8px', borderRadius: 'var(--radius-s)', boxShadow: 'var(--elevation-overlay)',
        }}>{content}</span>
      )}
    </span>
  );
}
