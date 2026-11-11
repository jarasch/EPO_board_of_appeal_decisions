var { SideNavigation, Badge, IconButton, Tooltip } = window.__NDL;

function Ic({ d, s = 20 }) {
  return <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">{d.map((p,i)=><path key={i} d={p}/>)}</svg>;
}

const ICONS = {
  database: ['M3 5c0-1.7 4-3 9-3s9 1.3 9 3-4 3-9 3-9-1.3-9-3z','M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5','M3 12c0 1.7 4 3 9 3s9-1.3 9-3'],
  terminal: ['m4 17 6-6-6-6','M12 19h8'],
  upload: ['M12 3v12','m7 8 5-5 5 5','M3 17v2a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2'],
  sparkle: ['M12 3 13.9 8.6 19.5 10.5 13.9 12.4 12 18 10.1 12.4 4.5 10.5 10.1 8.6z'],
  users: ['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2','M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8','M22 21v-2a4 4 0 0 0-3-3.9'],
  settings: ['M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6','M19.6 13.4a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2v.2a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-2.9-1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0-1.2-2.9H4a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.2-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 2.9-1.2V4a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 2.9 1.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.2a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.5 1z'],
  help: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20','M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3','M12 17h.01'],
  bell: ['M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9','M10.3 21a2 2 0 0 0 3.4 0'],
  plus: ['M12 5v14','M5 12h14'],
  search: ['m21 21-4.3-4.3','M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16'],
  play: ['m5 3 14 9-14 9V3z'],
  close: ['M18 6 6 18','M6 6l12 12'],
  copy: ['M8 4h10a2 2 0 0 1 2 2v10','M4 8h10a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V10a2 2 0 0 1 2-2z'],
  zoomIn: ['M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16','m21 21-4.3-4.3','M11 8v6','M8 11h6'],
  zoomOut: ['M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16','m21 21-4.3-4.3','M8 11h6'],
  fit: ['M8 3H5a2 2 0 0 0-2 2v3','M16 3h3a2 2 0 0 1 2 2v3','M16 21h3a2 2 0 0 0 2-2v-3','M8 21H5a2 2 0 0 1-2-2v-3'],
  pause: ['M10 4H6v16h4z','M18 4h-4v16h4z'],
  trash: ['M3 6h18','M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6','M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2'],
};

function TopBar({ title, children }) {
  return (
    <header style={{
      height: 56, flex: '0 0 56px', display: 'flex', alignItems: 'center', gap: 12, padding: '0 24px',
      background: 'var(--surface)', borderBottom: '1px solid var(--border-weak)', boxSizing: 'border-box',
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>{title}</div>
      {children}
      <Tooltip content="Notifications"><IconButton ariaLabel="Notifications"><Ic d={ICONS.bell} /></IconButton></Tooltip>
      <Tooltip content="Help"><IconButton ariaLabel="Help"><Ic d={ICONS.help} /></IconButton></Tooltip>
      <div style={{
        width: 32, height: 32, borderRadius: 9999, background: 'var(--primary-fill)', color: 'var(--text-inverse)',
        display: 'grid', placeItems: 'center', fontWeight: 700, fontSize: 12, marginLeft: 4,
      }}>AK</div>
    </header>
  );
}

function AppShell({ page, onNavigate, title, topBarActions, children }) {
  return (
    <div style={{ display: 'flex', height: '100%', background: 'var(--canvas)', fontFamily: 'var(--font-sans)' }}>
      <SideNavigation
        value={page} onChange={onNavigate} width={228}
        header={<img src="../../assets/logo-lockup-horizontal.svg" alt="Neo4j Graph Intelligence Platform" style={{ width: 148, display: 'block' }} />}
        items={[
          { value: 'instances', label: 'Instances', icon: <Ic d={ICONS.database} /> },
          { value: 'query', label: 'Query', icon: <Ic d={ICONS.terminal} /> },
          { value: 'import', label: 'Import', icon: <Ic d={ICONS.upload} /> },
          { value: 'assist', label: 'Cypher assist', icon: <Ic d={ICONS.sparkle} />, trailing: <Badge color="discovery">New</Badge> },
          { isSection: true, label: 'Organisation' },
          { value: 'members', label: 'Members', icon: <Ic d={ICONS.users} /> },
          { value: 'settings', label: 'Settings', icon: <Ic d={ICONS.settings} /> },
        ]}
        footer={<div style={{ fontSize: 12, lineHeight: 1.67, color: 'var(--text-weaker)' }}>Kensington Retail<br /><span style={{ color: 'var(--text-weakest)' }}>Professional plan</span></div>}
      />
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <TopBar title={title}>{topBarActions}</TopBar>
        <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>{children}</div>
      </div>
    </div>
  );
}

Object.assign(window, { Ic, ICONS, TopBar, AppShell });
