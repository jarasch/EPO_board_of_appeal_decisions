import React from 'react';

export function Breadcrumbs({ items = [], onNavigate }) {
  return (
    <nav aria-label="Breadcrumb" style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--font-sans)', fontSize: 14, lineHeight: 1.43, flexWrap: 'wrap' }}>
      {items.map((it, i) => {
        const last = i === items.length - 1;
        return (
          <React.Fragment key={i}>
            {last
              ? <span aria-current="page" style={{ color: 'var(--text)', fontWeight: 700 }}>{it.label}</span>
              : <a href={it.href || '#'} onClick={(e) => { if (onNavigate) { e.preventDefault(); onNavigate(it, i); } }}
                  style={{ color: 'var(--text-weak)', textDecoration: 'none' }}>{it.label}</a>}
            {!last && (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text-weakest)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6" /></svg>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
