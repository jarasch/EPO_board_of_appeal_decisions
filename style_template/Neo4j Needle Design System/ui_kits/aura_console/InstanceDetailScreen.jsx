var { Button, Card, Badge, Tabs, Breadcrumbs, DataTable, CodeBlock, Switch, Banner } = window.__NDL;

const CHART = [
  { day: 'Mon', a: 42, b: 18 }, { day: 'Tue', a: 61, b: 26 }, { day: 'Wed', a: 55, b: 22 },
  { day: 'Thu', a: 78, b: 31 }, { day: 'Fri', a: 92, b: 40 }, { day: 'Sat', a: 34, b: 12 }, { day: 'Sun', a: 28, b: 10 },
];

function BarChart() {
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, height: 140 }}>
        {CHART.map((d) => (
          <div key={d.day} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
            <div style={{ display: 'flex', gap: 3, alignItems: 'flex-end', height: 120, width: '100%', justifyContent: 'center' }}>
              <div style={{ width: '38%', height: d.a + '%', background: 'var(--chart-1)', borderRadius: '4px 4px 0 0' }} />
              <div style={{ width: '38%', height: d.b + '%', background: 'var(--chart-2)', borderRadius: '4px 4px 0 0' }} />
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-weaker)' }}>{d.day}</div>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 16, marginTop: 12 }}>
        {[['Read queries', 'var(--chart-1)'], ['Write queries', 'var(--chart-2)']].map(([l, c]) => (
          <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-weak)' }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: c }} />{l}
          </div>
        ))}
      </div>
    </div>
  );
}

function InstanceDetailScreen({ instance, onBack }) {
  const [tab, setTab] = React.useState('overview');
  const [logging, setLogging] = React.useState(true);
  const [pauseNight, setPauseNight] = React.useState(false);
  const uri = 'neo4j+s://' + instance.name + '.databases.neo4j.io';

  return (
    <div style={{ padding: 32, boxSizing: 'border-box' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <Breadcrumbs onNavigate={onBack} items={[{ label: 'Instances' }, { label: instance.name }]} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '12px 0 20px' }}>
          <h1 className="ndl-title-1" style={{ margin: 0, color: 'var(--text)' }}>{instance.name}</h1>
          <Badge color={instance.tone} hasDot>{instance.status}</Badge>
          <div style={{ flex: 1 }} />
          <Button fill="outlined" color="neutral">Pause instance</Button>
          <Button>Open in Query</Button>
        </div>

        <Tabs value={tab} onChange={setTab} items={[
          { value: 'overview', label: 'Overview' },
          { value: 'connect', label: 'Connect' },
          { value: 'metrics', label: 'Metrics' },
          { value: 'settings', label: 'Settings' },
        ]} />

        <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {tab === 'overview' && (
            <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
              <Card style={{ flex: 2 }} header={<h2 className="ndl-title-4" style={{ margin: 0 }}>Query volume, last 7 days</h2>}>
                <BarChart />
              </Card>
              <Card style={{ flex: 1 }} header={<h2 className="ndl-title-4" style={{ margin: 0 }}>Details</h2>}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {[['Memory', instance.size], ['Compute', instance.cpu], ['Region', instance.region], ['Version', 'Neo4j ' + instance.version], ['Nodes', instance.nodes], ['Relationships', instance.rels]].map(([k, v]) => (
                    <div key={k} style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                      <span className="ndl-body-m" style={{ color: 'var(--text-weak)' }}>{k}</span>
                      <span className="ndl-body-m" style={{ color: 'var(--text)', fontWeight: 600 }}>{v}</span>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}

          {tab === 'connect' && (
            <>
              <Banner type="info" title="Credentials are shown once" icon={<Ic d={ICONS.help} s={18} />}>
                Download the credentials file when the instance is created. Neo4j does not store the password.
              </Banner>
              <Card header={<h2 className="ndl-title-4" style={{ margin: 0 }}>Connection URI</h2>}>
                <CodeBlock language="plain" onCopy={() => {}} code={uri} />
              </Card>
              <Card header={<h2 className="ndl-title-4" style={{ margin: 0 }}>Python driver</h2>}>
                <CodeBlock language="plain" onCopy={() => {}} showLineNumbers code={'from neo4j import GraphDatabase\n\ndriver = GraphDatabase.driver(\n    "' + uri + '",\n    auth=("neo4j", "<password>"))\n\nrecords, _, _ = driver.execute_query(\n    "MATCH (p:Person) RETURN p.name LIMIT 25")'} />
              </Card>
            </>
          )}

          {tab === 'metrics' && (
            <Card header={<h2 className="ndl-title-4" style={{ margin: 0 }}>Slowest queries</h2>} padding="none">
              <DataTable isDense
                columns={[
                  { key: 'q', header: 'Query', isCode: true },
                  { key: 'calls', header: 'Calls', align: 'right', isCode: true },
                  { key: 'p95', header: 'p95', align: 'right', isCode: true },
                ]}
                rows={[
                  { q: 'MATCH (p:Person)-[:ORDERED*1..3]->(o:Order) RETURN o', calls: '4,102', p95: '812 ms' },
                  { q: 'MATCH (c:Company {name: $name}) RETURN c', calls: '88,410', p95: '14 ms' },
                  { q: 'MATCH (p:Product)<-[:CONTAINS]-(o:Order) RETURN p, count(o)', calls: '1,204', p95: '2,140 ms' },
                ]} />
            </Card>
          )}

          {tab === 'settings' && (
            <Card header={<h2 className="ndl-title-4" style={{ margin: 0 }}>Instance settings</h2>}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <Switch label="Enable query logging" isChecked={logging} onChange={setLogging} />
                <Switch label="Pause instance overnight (22:00–06:00 UTC)" isChecked={pauseNight} onChange={setPauseNight} />
                <div style={{ borderTop: '1px solid var(--border-weak)', paddingTop: 16 }}>
                  <Button color="danger" fill="outlined">Delete instance</Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { InstanceDetailScreen });
