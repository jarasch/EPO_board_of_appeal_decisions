var { Button, IconButton, Tooltip, Tabs, Tag, Badge, DataTable, CodeBlock, GraphLegend, LoadingSpinner, Banner } = window.__NDL;

const NODE_COLORS = ['#FFDF81', '#C990C0', '#F79767', '#56C7E4', '#F16767', '#D8C7AE'];
const LABELS = [{ label: 'Person', count: 412 }, { label: 'Company', count: 38 }, { label: 'Product', count: 1204 }, { label: 'Order', count: 8802 }];

const NODES = [
  { id: 1, x: 380, y: 210, r: 30, c: 0, t: 'Ada K.' }, { id: 2, x: 540, y: 140, r: 26, c: 1, t: 'Neo4j' },
  { id: 3, x: 550, y: 310, r: 24, c: 2, t: 'Graph DB' }, { id: 4, x: 260, y: 310, r: 22, c: 3, t: '#4021' },
  { id: 5, x: 280, y: 120, r: 22, c: 0, t: 'Tomas B.' }, { id: 6, x: 700, y: 220, r: 20, c: 2, t: 'GDS' },
  { id: 7, x: 430, y: 400, r: 20, c: 3, t: '#4088' }, { id: 8, x: 700, y: 380, r: 18, c: 4, t: 'Priya R.' },
  { id: 9, x: 200, y: 210, r: 18, c: 5, t: 'EU-W1' }, { id: 10, x: 600, y: 70, r: 16, c: 1, t: 'Aura' },
];
const EDGES = [[1,2],[1,3],[1,4],[5,2],[3,6],[4,7],[7,1],[8,6],[9,1],[2,10],[5,9],[8,3]];

function GraphCanvas() {
  return (
    <svg width="100%" height="100%" viewBox="0 0 900 480" preserveAspectRatio="xMidYMid slice" style={{ display: 'block' }}>
      {EDGES.map(([a, b], i) => {
        const n1 = NODES.find((n) => n.id === a), n2 = NODES.find((n) => n.id === b);
        return <line key={i} x1={n1.x} y1={n1.y} x2={n2.x} y2={n2.y} stroke="var(--border-strong)" strokeWidth="1.5" />;
      })}
      {NODES.map((n) => (
        <g key={n.id}>
          <circle cx={n.x} cy={n.y} r={n.r} fill={NODE_COLORS[n.c]} stroke="var(--surface)" strokeWidth="2" />
          <text x={n.x} y={n.y + 4} textAnchor="middle" style={{ font: '600 11px var(--font-sans)', fill: '#1A1B1D' }}>{n.t}</text>
        </g>
      ))}
    </svg>
  );
}

function Panel({ children, style }) {
  return (
    <div style={{
      background: 'var(--surface)', border: '1px solid var(--border-weak)', borderRadius: 'var(--radius-card-lg)',
      boxShadow: 'var(--elevation-overlay)', ...style,
    }}>{children}</div>
  );
}

function QueryScreen() {
  const [query, setQuery] = React.useState("MATCH (p:Person)-[:WORKS_AT]->(c:Company)\nWHERE c.name = 'Neo4j'\nRETURN p, c LIMIT 25");
  const [tab, setTab] = React.useState('graph');
  const [running, setRunning] = React.useState(false);
  const [active, setActive] = React.useState(LABELS.map((l) => l.label));
  const [error, setError] = React.useState(false);

  const run = () => {
    setRunning(true);
    setTimeout(() => { setRunning(false); setError(query.indexOf('PURCHASED') > -1); }, 900);
  };

  return (
    <div style={{ position: 'relative', height: '100%', background: 'var(--canvas)', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', inset: 0 }}><GraphCanvas /></div>

      <Panel style={{ position: 'absolute', top: 16, left: 16, right: 16, padding: 12 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
          <textarea value={query} onChange={(e) => setQuery(e.target.value)} spellCheck={false}
            style={{
              flex: 1, minWidth: 0, height: 78, resize: 'none', boxSizing: 'border-box',
              fontFamily: 'var(--font-code)', fontSize: 14, lineHeight: 1.43, color: 'var(--text)',
              background: 'var(--canvas)', border: '1px solid var(--border-weak)', borderRadius: 'var(--radius-m)',
              padding: '8px 12px', outlineColor: 'var(--primary-focus)', outlineOffset: 2,
            }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <Button onClick={run} isLoading={running}>{running ? 'Running' : 'Run query'}</Button>
            <Button fill="text" size="small"><Ic d={ICONS.sparkle} s={16} /> Cypher assist</Button>
          </div>
        </div>
      </Panel>

      <Panel style={{ position: 'absolute', top: 130, left: 16, width: 216, padding: 16 }}>
        <GraphLegend labels={LABELS} activeLabels={active} onToggle={(l) => setActive((a) => a.indexOf(l) > -1 ? a.filter((x) => x !== l) : a.concat(l))} />
        <div style={{ marginTop: 16, borderTop: '1px solid var(--border-weak)', paddingTop: 12 }}>
          <div style={{ fontWeight: 700, fontSize: 12, color: 'var(--text-weaker)', marginBottom: 8 }}>Relationship types</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {['WORKS_AT', 'ORDERED', 'CONTAINS'].map((t) => <Tag key={t} size="small">{t}</Tag>)}
          </div>
        </div>
      </Panel>

      <Panel style={{ position: 'absolute', top: 130, right: 16, width: 300, padding: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <span style={{ width: 12, height: 12, borderRadius: 9999, background: '#FFDF81' }} />
          <span className="ndl-title-4" style={{ color: 'var(--text)' }}>Person</span>
          <div style={{ flex: 1 }} />
          <IconButton size="small" ariaLabel="Close inspector"><Ic d={ICONS.close} s={16} /></IconButton>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[['name', "'Ada Kensington'"], ['title', "'Staff engineer'"], ['joined', "date('2019-04-02')"], ['elementId', "'4:9f2a:118'"]].map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, fontSize: 12, lineHeight: 1.67 }}>
              <span style={{ color: 'var(--text-weaker)', fontFamily: 'var(--font-code)' }}>{k}</span>
              <span style={{ color: 'var(--text)', fontFamily: 'var(--font-code)', textAlign: 'right', wordBreak: 'break-all' }}>{v}</span>
            </div>
          ))}
        </div>
      </Panel>

      <Panel style={{ position: 'absolute', bottom: 216, right: 16, padding: 4, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Tooltip content="Zoom in" placement="left"><IconButton ariaLabel="Zoom in"><Ic d={ICONS.zoomIn} /></IconButton></Tooltip>
        <Tooltip content="Zoom out" placement="left"><IconButton ariaLabel="Zoom out"><Ic d={ICONS.zoomOut} /></IconButton></Tooltip>
        <Tooltip content="Fit to view" placement="left"><IconButton ariaLabel="Fit to view"><Ic d={ICONS.fit} /></IconButton></Tooltip>
      </Panel>

      <Panel style={{ position: 'absolute', bottom: 16, left: 16, right: 16, height: 188, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '0 16px' }}>
          <Tabs size="small" value={tab} onChange={setTab} items={[
            { value: 'graph', label: 'Graph' }, { value: 'table', label: 'Table', count: 25 }, { value: 'plan', label: 'Query plan' },
          ]} />
        </div>
        <div style={{ padding: 16, overflow: 'auto' }}>
          {error && <Banner type="danger" title="Query failed" icon={<Ic d={ICONS.close} s={18} />}>
            Unknown relationship type <code className="ndl-code">PURCHASED_BY</code>. Run <code className="ndl-code">CALL db.relationshipTypes()</code> to list valid types.
          </Banner>}
          {running && <LoadingSpinner label="Running query…" />}
          {!running && !error && tab === 'graph' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 14, color: 'var(--text-weak)' }}>
              <Badge color="success" hasDot>Completed</Badge>
              <span>25 nodes, 24 relationships returned in <span className="ndl-code">31 ms</span>.</span>
            </div>
          )}
          {!running && !error && tab === 'table' && (
            <DataTable isDense
              columns={[{ key: 'p', header: 'p.name' }, { key: 'c', header: 'c.name' }, { key: 'id', header: 'elementId', isCode: true }]}
              rows={[
                { p: 'Ada Kensington', c: 'Neo4j', id: '4:9f2a:118' },
                { p: 'Tomas Bergh', c: 'Neo4j', id: '4:9f2a:204' },
                { p: 'Priya Raman', c: 'Neo4j', id: '4:9f2a:377' },
              ]} />
          )}
          {!running && !error && tab === 'plan' && (
            <CodeBlock language="plain" code={'Operator          Estimated Rows   Rows\nProduceResults                25     25\nFilter                        25     25\nExpand(All)                  412    412\nNodeByLabelScan              412    412'} />
          )}
        </div>
      </Panel>
    </div>
  );
}

Object.assign(window, { QueryScreen });
