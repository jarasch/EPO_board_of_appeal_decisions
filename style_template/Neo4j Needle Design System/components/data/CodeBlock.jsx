import React from 'react';

const KEYWORDS = /\b(MATCH|OPTIONAL MATCH|WHERE|RETURN|WITH|CREATE|MERGE|SET|DELETE|DETACH DELETE|ORDER BY|LIMIT|SKIP|UNWIND|CALL|YIELD|AS|AND|OR|NOT|IN|COUNT|DISTINCT)\b/g;

export function CodeBlock({ code = '', language = 'cypher', showLineNumbers = false, onCopy }) {
  const lines = String(code).replace(/\n$/, '').split('\n');
  const highlight = (line) => {
    if (language !== 'cypher') return [line];
    const out = []; let last = 0; let m;
    KEYWORDS.lastIndex = 0;
    while ((m = KEYWORDS.exec(line))) {
      if (m.index > last) out.push(line.slice(last, m.index));
      out.push(<span key={m.index} style={{ color: 'var(--discovery-text)', fontWeight: 500 }}>{m[0]}</span>);
      last = m.index + m[0].length;
    }
    out.push(line.slice(last));
    return out;
  };
  return (
    <div style={{ position: 'relative', background: 'var(--canvas)', border: '1px solid var(--border-weak)', borderRadius: 'var(--radius-m)', padding: '12px 16px', overflowX: 'auto' }}>
      <pre style={{ margin: 0, fontFamily: 'var(--font-code)', fontSize: 14, lineHeight: 1.43, color: 'var(--text)' }}>
        {lines.map((l, i) => (
          <div key={i} style={{ display: 'flex', gap: 16 }}>
            {showLineNumbers && <span style={{ color: 'var(--text-weakest)', userSelect: 'none', minWidth: 16, textAlign: 'right' }}>{i + 1}</span>}
            <span>{highlight(l)}</span>
          </div>
        ))}
      </pre>
      {onCopy && (
        <button type="button" onClick={onCopy} style={{
          position: 'absolute', top: 8, right: 8, background: 'var(--surface)', border: '1px solid var(--border-weak)',
          borderRadius: 'var(--radius-s)', padding: '4px 8px', cursor: 'pointer',
          fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: 12, color: 'var(--text-weak)',
        }}>Copy</button>
      )}
    </div>
  );
}
