var { Button } = window.__NDL;

function SiteHeader({ onNav, page }) {
  const links = ['Product', 'Solutions', 'Developers', 'Pricing', 'Company'];
  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 20, background: 'var(--brand-off-white)',
      borderBottom: '1px solid var(--border-weak)',
    }}>
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '0 32px', height: 72, display: 'flex', alignItems: 'center', gap: 32 }}>
        <a href="#" onClick={(e) => { e.preventDefault(); onNav('home'); }} style={{ display: 'flex' }}>
          <img src="../../assets/logo-lockup-horizontal.svg" alt="Neo4j Graph Intelligence Platform" style={{ width: 168, display: 'block' }} />
        </a>
        <nav style={{ display: 'flex', gap: 4, flex: 1 }}>
          {links.map((l) => {
            const key = l.toLowerCase();
            const active = page === key;
            return (
              <a key={l} href="#" onClick={(e) => { e.preventDefault(); onNav(key); }}
                style={{
                  padding: '8px 12px', borderRadius: 'var(--radius-control)', textDecoration: 'none',
                  fontWeight: active ? 700 : 600, fontSize: 14,
                  color: active ? 'var(--primary-text)' : 'var(--text-weak)',
                  background: active ? 'var(--primary-bg)' : 'transparent',
                }}>{l}</a>
            );
          })}
        </nav>
        <Button fill="text" size="small">Sign in</Button>
        <Button size="medium">Start free</Button>
      </div>
    </header>
  );
}

function SiteFooter() {
  const cols = [
    ['Product', ['Aura', 'Graph Data Science', 'Cypher', 'Bloom', 'Connectors']],
    ['Developers', ['Documentation', 'Developer guides', 'Community forum', 'GraphAcademy', 'Drivers']],
    ['Company', ['About', 'Customers', 'Careers', 'Newsroom', 'Contact']],
  ];
  return (
    <footer style={{ background: 'var(--brand-black)', color: '#FCF9F6' }}>
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '64px 32px 32px', display: 'flex', gap: 64 }}>
        <div style={{ width: 260 }}>
          <img src="../../assets/logo-lockup-stacked-white.svg" alt="Neo4j" style={{ width: 160, display: 'block' }} />
          <p style={{ fontSize: 14, lineHeight: 1.43, color: '#A8ACB2', marginTop: 20 }}>
            The graph database and knowledge graph platform for connected data.
          </p>
        </div>
        {cols.map(([title, items]) => (
          <div key={title} style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: 14, letterSpacing: '0.016rem', marginBottom: 12 }}>{title}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {items.map((i) => <a key={i} href="#" onClick={(e) => e.preventDefault()} style={{ fontSize: 14, color: '#CFD1D4', textDecoration: 'none' }}>{i}</a>)}
            </div>
          </div>
        ))}
      </div>
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '24px 32px 48px', borderTop: '1px solid #3C3F44', display: 'flex', gap: 24, fontSize: 12, color: '#818790' }}>
        <span>© 2026 Neo4j, Inc.</span><span>Privacy</span><span>Terms</span><span>Trust centre</span>
      </div>
    </footer>
  );
}

Object.assign(window, { SiteHeader, SiteFooter });
