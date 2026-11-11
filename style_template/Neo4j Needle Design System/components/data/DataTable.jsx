import React from 'react';

export function DataTable({ columns = [], rows = [], isDense = false, emptyText = 'No results.', onRowClick }) {
  const padY = isDense ? 6 : 12;
  return (
    <div style={{ border: '1px solid var(--border-weak)', borderRadius: 'var(--radius-card)', overflow: 'hidden', background: 'var(--surface)', fontFamily: 'var(--font-sans)' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: isDense ? 12 : 14 }}>
        <thead>
          <tr style={{ background: 'var(--canvas)' }}>
            {columns.map((c) => (
              <th key={c.key} style={{
                textAlign: c.align || 'left', padding: `${padY}px 16px`, width: c.width,
                fontWeight: 700, fontSize: 12, lineHeight: 1.67, color: 'var(--text-weaker)',
                borderBottom: '1px solid var(--border-weak)', whiteSpace: 'nowrap',
              }}>{c.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr><td colSpan={columns.length} style={{ padding: 32, textAlign: 'center', color: 'var(--text-weaker)' }}>{emptyText}</td></tr>
          )}
          {rows.map((r, i) => (
            <Row key={r.id ?? i} row={r} columns={columns} padY={padY} onClick={onRowClick} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Row({ row, columns, padY, onClick }) {
  const [hover, setHover] = React.useState(false);
  return (
    <tr onClick={() => onClick && onClick(row)}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{ background: hover && onClick ? 'var(--neutral-hover)' : 'transparent', cursor: onClick ? 'pointer' : undefined, transition: 'background-color 140ms ease-out' }}>
      {columns.map((c) => (
        <td key={c.key} style={{
          padding: `${padY}px 16px`, textAlign: c.align || 'left', color: 'var(--text)',
          borderBottom: '1px solid var(--border-weak)', fontFamily: c.isCode ? 'var(--font-code)' : 'inherit',
          verticalAlign: 'middle',
        }}>{c.render ? c.render(row) : row[c.key]}</td>
      ))}
    </tr>
  );
}
