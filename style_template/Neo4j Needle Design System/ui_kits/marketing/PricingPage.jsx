var { Button, Card, Badge, Tag } = window.__NDL;

const PLANS = [
  { name: 'AuraDB Free', price: '$0', unit: 'forever', blurb: 'For learning, prototypes and small side projects.',
    features: ['200k nodes, 400k relationships', '1 instance', 'Pauses after 3 days idle', 'Community support'], cta: 'Start free', featured: false },
  { name: 'AuraDB Professional', price: '$65', unit: 'per GB / month', blurb: 'For production applications that need to stay up.',
    features: ['1 GB to 128 GB memory', 'Unlimited instances', 'Daily backups, 7-day retention', 'Email support'], cta: 'Start free trial', featured: true },
  { name: 'AuraDB Business Critical', price: 'Custom', unit: 'annual contract', blurb: 'For regulated and high-availability workloads.',
    features: ['Multi-region availability', 'VPC peering and private link', 'Point-in-time recovery', '24/7 support with SLA'], cta: 'Talk to sales', featured: false },
];

function Check() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--success-text)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: 3 }}><path d="M20 6 9 17l-5-5" /></svg>;
}

function PricingPage() {
  return (
    <div style={{ background: 'var(--brand-off-white)' }}>
      <section style={{ maxWidth: 1180, margin: '0 auto', padding: '80px 32px 0', textAlign: 'center' }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 500, fontSize: 48, lineHeight: 1.2, margin: 0, color: 'var(--brand-black)', fontFeatureSettings: '"lnum" 1, "pnum" 1' }}>
          Pay for what you run
        </h1>
        <p style={{ fontSize: 20, lineHeight: 1.5, color: 'var(--text-weak)', marginTop: 16, maxWidth: 560, marginLeft: 'auto', marginRight: 'auto' }}>
          Instances are billed per GB of memory per hour. Pause an instance and you keep the storage without the compute cost.
        </p>
      </section>

      <section style={{ maxWidth: 1180, margin: '0 auto', padding: '48px 32px 96px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24, alignItems: 'stretch' }}>
          {PLANS.map((p) => (
            <div key={p.name} style={{
              background: 'var(--surface)', borderRadius: 'var(--radius-xl)', padding: 32,
              border: '1px solid ' + (p.featured ? 'var(--primary-border)' : 'var(--border-weak)'),
              boxShadow: p.featured ? 'var(--elevation-overlay)' : 'var(--elevation-raised)',
              display: 'flex', flexDirection: 'column', gap: 16,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <h2 className="ndl-title-3" style={{ margin: 0, color: 'var(--text)' }}>{p.name}</h2>
                {p.featured && <Badge color="primary">Most popular</Badge>}
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                <span style={{ fontFamily: 'var(--font-display)', fontWeight: 500, fontSize: 40, lineHeight: 1.2, color: 'var(--text)', fontFeatureSettings: '"lnum" 1, "pnum" 1' }}>{p.price}</span>
                <span className="ndl-body-m" style={{ color: 'var(--text-weaker)' }}>{p.unit}</span>
              </div>
              <p className="ndl-body-m" style={{ color: 'var(--text-weak)', margin: 0 }}>{p.blurb}</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
                {p.features.map((ft) => (
                  <div key={ft} style={{ display: 'flex', gap: 8 }}>
                    <Check /><span className="ndl-body-m" style={{ color: 'var(--text)' }}>{ft}</span>
                  </div>
                ))}
              </div>
              <Button isFullWidth size="large" fill={p.featured ? 'filled' : 'outlined'} color={p.featured ? 'primary' : 'neutral'}>{p.cta}</Button>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 48, background: 'var(--brand-cream)', borderRadius: 'var(--radius-xl)', padding: 32, display: 'flex', gap: 32, alignItems: 'center' }}>
          <div style={{ flex: 1 }}>
            <h3 className="ndl-title-3" style={{ margin: 0, color: 'var(--brand-black)' }}>Self-managed instead?</h3>
            <p className="ndl-body-l" style={{ color: 'var(--text-weak)', margin: '8px 0 0' }}>
              Neo4j Community Edition is free and open source under GPLv3. Enterprise Edition adds clustering, role-based access control and hot backups.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <Button fill="outlined" color="neutral">Download</Button>
            <Button>Compare editions</Button>
          </div>
        </div>
      </section>
    </div>
  );
}

Object.assign(window, { PricingPage });
