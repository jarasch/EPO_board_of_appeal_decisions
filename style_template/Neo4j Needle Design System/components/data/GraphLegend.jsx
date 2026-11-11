import React from 'react';

const NODE_COLORS = ['#FFDF81','#C990C0','#F79767','#56C7E4','#F16767','#D8C7AE','#8DCC93','#ECB4C9','#4D8DDA','#FFC354','#DA7294','#579380'];

export function GraphLegend({ labels = [], activeLabels, onToggle, title = 'Node labels' }) {
  return (
    <div style={{ fontFamily: 'var(--font-sans)' }}>
      {title && <div style={{ fontWeight: 700, fontSize: 12, lineHeight: 1.67, color: 'var(--text-weaker)', marginBottom: 8 }}>{title}</div>}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {labels.map((l, i) => {
          const name = typeof l === 'string' ? l : l.label;
          const count = typeof l === 'string' ? undefined : l.count;
          const color = (typeof l === 'object' && l.color) || NODE_COLORS[i % NODE_COLORS.length];
          const on = !activeLabels || activeLabels.includes(name);
          return (
            <button key={name} type="button" onClick={() => onToggle && onToggle(name)}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 6, height: 24, padding: '0 10px',
                borderRadius: 'var(--radius-pill)', border: '1px solid var(--border-weak)',
                background: on ? color : 'var(--canvas)', color: on ? '#1A1B1D' : 'var(--text-weakest)',
                fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: 12, lineHeight: 1,
                cursor: onToggle ? 'pointer' : 'default', opacity: on ? 1 : 0.6,
                transition: 'background-color 140ms ease-out, opacity 140ms ease-out',
              }}>
              {name}{count != null && <span style={{ opacity: 0.7 }}>{count}</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
