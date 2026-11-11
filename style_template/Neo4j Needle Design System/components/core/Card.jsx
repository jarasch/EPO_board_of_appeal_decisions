import React from 'react';

export function Card({ children, header, footer, padding = 'medium', isInteractive = false, onClick, style: styleProp }) {
  const [hover, setHover] = React.useState(false);
  const pad = padding === 'none' ? 0 : padding === 'small' ? 16 : 24;
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        background: 'var(--surface)', border: '1px solid ' + (isInteractive && hover ? 'var(--border-strong)' : 'var(--border-weak)'),
        borderRadius: 'var(--radius-card)', boxShadow: 'var(--elevation-raised)',
        cursor: isInteractive ? 'pointer' : undefined, overflow: 'hidden',
        transition: 'border-color 140ms ease-out', ...styleProp,
      }}
    >
      {header && <div style={{ padding: `${pad === 0 ? 16 : pad}px ${pad === 0 ? 16 : pad}px 0` }}>{header}</div>}
      <div style={{ padding: pad }}>{children}</div>
      {footer && <div style={{ padding: `0 ${pad === 0 ? 16 : pad}px ${pad === 0 ? 16 : pad}px`, borderTop: '1px solid var(--border-weak)', paddingTop: 16 }}>{footer}</div>}
    </div>
  );
}
