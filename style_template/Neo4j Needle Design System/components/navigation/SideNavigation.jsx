import React from 'react';

export function SideNavigation({ items = [], value, onChange, header, footer, isCollapsed = false, width = 240 }) {
  return (
    <nav style={{
      width: isCollapsed ? 64 : width, flex: `0 0 ${isCollapsed ? 64 : width}px`, height: '100%', boxSizing: 'border-box',
      background: 'var(--surface)', borderRight: '1px solid var(--border-weak)',
      display: 'flex', flexDirection: 'column', fontFamily: 'var(--font-sans)', transition: 'width 160ms ease-out',
    }}>
      {header && <div style={{ padding: isCollapsed ? '16px 12px' : 16, borderBottom: '1px solid var(--border-weak)' }}>{header}</div>}
      <div style={{ flex: 1, overflowY: 'auto', padding: 8, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {items.map((it) => it.isSection
          ? <div key={it.label} style={{ padding: isCollapsed ? '12px 0 4px' : '12px 12px 4px', fontSize: 12, fontWeight: 700, color: 'var(--text-weakest)', letterSpacing: '0.016rem' }}>{isCollapsed ? '' : it.label}</div>
          : <NavItem key={it.value} item={it} active={it.value === value} isCollapsed={isCollapsed} onClick={() => onChange && onChange(it.value)} />)}
      </div>
      {footer && <div style={{ padding: 12, borderTop: '1px solid var(--border-weak)' }}>{footer}</div>}
    </nav>
  );
}

function NavItem({ item, active, isCollapsed, onClick }) {
  const [hover, setHover] = React.useState(false);
  return (
    <button type="button" onClick={onClick} title={isCollapsed ? String(item.label) : undefined}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: 12, width: '100%', boxSizing: 'border-box',
        padding: isCollapsed ? '8px 0' : '8px 12px', justifyContent: isCollapsed ? 'center' : 'flex-start',
        background: active ? 'var(--primary-bg)' : hover ? 'var(--neutral-hover)' : 'transparent',
        border: 0, borderRadius: 'var(--radius-control)', cursor: 'pointer', textAlign: 'left',
        color: active ? 'var(--primary-text)' : 'var(--text-weak)',
        fontFamily: 'var(--font-sans)', fontWeight: active ? 700 : 600, fontSize: 14, lineHeight: 1.43,
        transition: 'background-color 140ms ease-out, color 140ms ease-out',
      }}>
      {item.icon && <span style={{ display: 'flex', flexShrink: 0 }}>{item.icon}</span>}
      {!isCollapsed && <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.label}</span>}
      {!isCollapsed && item.trailing}
    </button>
  );
}
