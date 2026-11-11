var { Button, Card, Badge, Tag, DataTable, TextInput, Select, Banner, Dialog, IconButton, Tooltip } = window.__NDL;

const INSTANCES = [
  { id: 'orders-prod', name: 'orders-prod', status: 'Running', tone: 'success', size: '8 GB', cpu: '2 CPU', region: 'Europe (Ireland)', version: '5.26', nodes: '1,204,880', rels: '4,812,003' },
  { id: 'catalogue-prod', name: 'catalogue-prod', status: 'Running', tone: 'success', size: '4 GB', cpu: '1 CPU', region: 'Europe (Ireland)', version: '5.26', nodes: '388,140', rels: '901,556' },
  { id: 'analytics-dev', name: 'analytics-dev', status: 'Paused', tone: 'warning', size: '2 GB', cpu: '1 CPU', region: 'US East (N. Virginia)', version: '5.26', nodes: '92,004', rels: '188,220' },
  { id: 'fraud-sandbox', name: 'fraud-sandbox', status: 'Creating', tone: 'primary', size: '2 GB', cpu: '1 CPU', region: 'US East (N. Virginia)', version: '5.26', nodes: '—', rels: '—' },
];

function InstancesScreen({ onOpenInstance }) {
  const [query, setQuery] = React.useState('');
  const [region, setRegion] = React.useState('');
  const [confirm, setConfirm] = React.useState(null);
  const rows = INSTANCES.filter((i) => i.name.includes(query) && (!region || i.region === region));

  return (
    <div style={{ position: 'relative', minHeight: '100%', padding: 32, boxSizing: 'border-box' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>

        <Banner type="warning" title="analytics-dev is paused" icon={<Ic d={ICONS.pause} s={18} />}
          actions={<Button size="small" fill="outlined" color="neutral">Resume instance</Button>}>
          Paused instances are not billed for compute but keep their storage. Data is retained for 30 days.
        </Banner>

        <div style={{ display: 'flex', gap: 16 }}>
          {[
            { label: 'Instances', value: '4', sub: '3 running' },
            { label: 'Nodes', value: '1.68M', sub: 'across all instances' },
            { label: 'Relationships', value: '5.90M', sub: 'across all instances' },
            { label: 'Estimated spend', value: '$482', sub: 'month to date' },
          ].map((s) => (
            <Card key={s.label} padding="small" style={{ flex: 1 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-weaker)', lineHeight: 1.67 }}>{s.label}</div>
              <div className="ndl-title-2" style={{ color: 'var(--text)', marginTop: 4 }}>{s.value}</div>
              <div style={{ fontSize: 12, color: 'var(--text-weakest)', lineHeight: 1.67 }}>{s.sub}</div>
            </Card>
          ))}
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, marginBottom: 12 }}>
            <TextInput placeholder="Filter instances" value={query} onChange={setQuery} leftIcon={<Ic d={ICONS.search} s={16} />} />
            <Select value={region} onChange={setRegion} placeholder="All regions"
              options={[{ value: 'Europe (Ireland)', label: 'Europe (Ireland)' }, { value: 'US East (N. Virginia)', label: 'US East (N. Virginia)' }]} />
            <div style={{ flex: 1 }} />
            <Button onClick={() => setConfirm('create')}>Create instance</Button>
          </div>

          <DataTable
            onRowClick={(r) => onOpenInstance && onOpenInstance(r)}
            columns={[
              { key: 'name', header: 'Name', render: (r) => (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontWeight: 700, color: 'var(--text)' }}>{r.name}</span>
                  <Tag size="small">{r.version}</Tag>
                </div>) },
              { key: 'status', header: 'Status', render: (r) => <Badge color={r.tone} hasDot>{r.status}</Badge> },
              { key: 'size', header: 'Size', render: (r) => r.size + ' · ' + r.cpu },
              { key: 'region', header: 'Region' },
              { key: 'nodes', header: 'Nodes', align: 'right', isCode: true },
              { key: 'rels', header: 'Relationships', align: 'right', isCode: true },
              { key: 'act', header: '', align: 'right', width: 88, render: (r) => (
                <div style={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }} onClick={(e) => e.stopPropagation()}>
                  <Tooltip content="Open in Query"><IconButton size="small" ariaLabel="Open in Query"><Ic d={ICONS.terminal} s={16} /></IconButton></Tooltip>
                  <Tooltip content="Delete instance"><IconButton size="small" color="danger" ariaLabel="Delete instance" onClick={() => setConfirm(r)}><Ic d={ICONS.trash} s={16} /></IconButton></Tooltip>
                </div>) },
            ]}
            rows={rows}
            emptyText="No instances match that filter."
          />
        </div>
      </div>

      <Dialog isOpen={Boolean(confirm) && confirm !== 'create'} size="small" onClose={() => setConfirm(null)}
        title={confirm && confirm !== 'create' ? 'Delete instance ' + confirm.name + '?' : ''}
        actions={<>
          <Button fill="outlined" color="neutral" onClick={() => setConfirm(null)}>Cancel</Button>
          <Button color="danger" onClick={() => setConfirm(null)}>Delete instance</Button>
        </>}>
        This removes {confirm && confirm !== 'create' ? confirm.nodes : ''} nodes and {confirm && confirm !== 'create' ? confirm.rels : ''} relationships. It cannot be undone.
      </Dialog>

      <Dialog isOpen={confirm === 'create'} onClose={() => setConfirm(null)} title="Create instance"
        actions={<>
          <Button fill="outlined" color="neutral" onClick={() => setConfirm(null)}>Cancel</Button>
          <Button onClick={() => setConfirm(null)}>Create instance</Button>
        </>}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <TextInput isFullWidth label="Instance name" placeholder="orders-staging" helpText="Lowercase letters, numbers and hyphens." />
          <div style={{ display: 'flex', gap: 12 }}>
            <div style={{ flex: 1 }}><Select isFullWidth label="Region" value="Europe (Ireland)" options={[{ value: 'Europe (Ireland)', label: 'Europe (Ireland)' }, { value: 'US East (N. Virginia)', label: 'US East (N. Virginia)' }]} /></div>
            <div style={{ flex: 1 }}><Select isFullWidth label="Size" value="4 GB" options={[{ value: '2 GB', label: '2 GB memory · 1 CPU' }, { value: '4 GB', label: '4 GB memory · 1 CPU' }, { value: '8 GB', label: '8 GB memory · 2 CPU' }]} /></div>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

Object.assign(window, { InstancesScreen, INSTANCES });
