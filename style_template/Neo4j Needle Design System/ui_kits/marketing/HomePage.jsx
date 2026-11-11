var { Button, Tag, CodeBlock, Card } = window.__NDL;

function Hero() {
  return (
    <section style={{ background: 'var(--gradient-baltic)', color: '#FCF9F6' }}>
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '96px 32px', display: 'flex', gap: 64, alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '4px 12px', borderRadius: 9999, border: '1px solid rgba(252,249,246,0.3)', fontSize: 12, fontWeight: 600, marginBottom: 24 }}>
            <span style={{ width: 6, height: 6, borderRadius: 9999, background: 'var(--brand-highlight-yellow)' }} />
            Aura 5.26 is generally available
          </div>
          <h1 style={{
            fontFamily: 'var(--font-display)', fontWeight: 500, fontSize: 56, lineHeight: 1.2, margin: 0,
            fontFeatureSettings: '"lnum" 1, "pnum" 1', letterSpacing: '-0.01em',
          }}>Ask harder questions<br />of your data</h1>
          <p style={{ fontSize: 20, lineHeight: 1.5, color: '#E7FAFB', marginTop: 24, maxWidth: 520 }}>
            Store data as nodes and relationships, then traverse them in milliseconds. Neo4j is the graph database behind fraud detection, supply chains, recommendations and knowledge graphs.
          </p>
          <div style={{ display: 'flex', gap: 12, marginTop: 32 }}>
            <button style={{
              height: 48, padding: '0 24px', borderRadius: 'var(--radius-control)', border: 0, cursor: 'pointer',
              background: '#FCF9F6', color: '#014063', fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: 16, letterSpacing: '0.016rem',
            }}>Start free</button>
            <button style={{
              height: 48, padding: '0 24px', borderRadius: 'var(--radius-control)', cursor: 'pointer',
              background: 'transparent', color: '#FCF9F6', border: '1px solid rgba(252,249,246,0.5)',
              fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: 16, letterSpacing: '0.016rem',
            }}>Talk to sales</button>
          </div>
          <div style={{ height: 3, width: 88, background: 'var(--brand-periwinkle)', borderRadius: 9999, marginTop: 48 }} />
        </div>
        <div style={{ flex: 1, maxWidth: 480 }}>
          <div style={{ background: '#FCF9F6', borderRadius: 'var(--radius-xl)', padding: 24, boxShadow: 'var(--elevation-overlay)' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-weaker)', marginBottom: 12 }}>Find fraud rings three hops out</div>
            <CodeBlock code={"MATCH (a:Account)-[:TRANSFERRED*1..3]->(b:Account)\nWHERE a.flagged = true\nRETURN b.id, count(*) AS hops\nORDER BY hops DESC LIMIT 10"} />
            <div style={{ display: 'flex', gap: 6, marginTop: 16, flexWrap: 'wrap' }}>
              <Tag size="small" color="primary">Cypher</Tag><Tag size="small">31 ms</Tag><Tag size="small">4.8M relationships</Tag>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function LogoBand() {
  return (
    <section style={{ background: 'var(--brand-off-white)', borderBottom: '1px solid var(--border-weak)' }}>
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '32px', display: 'flex', alignItems: 'center', gap: 48 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-weaker)', whiteSpace: 'nowrap' }}>Trusted in production by</span>
        <div style={{ display: 'flex', gap: 40, flex: 1, justifyContent: 'space-between', opacity: 0.55 }}>
          {['Customer logo', 'Customer logo', 'Customer logo', 'Customer logo', 'Customer logo'].map((l, i) => (
            <div key={i} style={{
              flex: 1, height: 32, borderRadius: 'var(--radius-s)', border: '1px dashed var(--border-strong)',
              display: 'grid', placeItems: 'center', fontSize: 11, color: 'var(--text-weakest)',
            }}>{l}</div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Features() {
  const items = [
    { t: 'Native graph storage', d: 'Relationships are stored as first-class records, so a traversal is a pointer hop, not a join. Query time stays flat as the graph grows.', c: 'var(--brand-forest)' },
    { t: 'Cypher, the graph language', d: 'Draw the pattern you are looking for and the database finds it. Cypher is the basis of the ISO GQL standard.', c: 'var(--brand-baltic-dark)' },
    { t: 'Graph data science', d: 'Sixty-five algorithms — centrality, community detection, similarity, embeddings — run in-database on the whole graph.', c: 'var(--brand-marigold)' },
  ];
  return (
    <section style={{ background: 'var(--brand-off-white)' }}>
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '96px 32px' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 500, fontSize: 40, lineHeight: 1.2, margin: 0, color: 'var(--brand-black)', fontFeatureSettings: '"lnum" 1, "pnum" 1' }}>
          Connections change everything
        </h2>
        <p style={{ fontSize: 20, lineHeight: 1.5, color: 'var(--text-weak)', marginTop: 16, maxWidth: 620 }}>
          Relational databases store rows and reconstruct relationships at query time. A graph database stores the relationships.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24, marginTop: 48 }}>
          {items.map((i) => (
            <div key={i.t} style={{ background: 'var(--surface)', border: '1px solid var(--border-weak)', borderRadius: 'var(--radius-xl)', padding: 32, boxShadow: 'var(--elevation-raised)' }}>
              <div style={{ width: 40, height: 4, background: i.c, borderRadius: 9999 }} />
              <h3 className="ndl-title-3" style={{ color: 'var(--text)', marginTop: 20, marginBottom: 8 }}>{i.t}</h3>
              <p className="ndl-body-l" style={{ color: 'var(--text-weak)', margin: 0 }}>{i.d}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Quote() {
  return (
    <section style={{ background: 'var(--brand-cream)' }}>
      <div style={{ maxWidth: 860, margin: '0 auto', padding: '96px 32px', textAlign: 'center' }}>
        <blockquote style={{
          fontFamily: 'var(--font-display)', fontWeight: 500, fontSize: 32, lineHeight: 1.3, margin: 0,
          color: 'var(--brand-black)', fontFeatureSettings: '"lnum" 1, "pnum" 1',
        }}>
          “We moved a query that took eleven minutes in Postgres down to under a second. The model matched the problem, so the query stopped fighting it.”
        </blockquote>
        <div style={{ marginTop: 24, fontSize: 14, fontWeight: 700, color: 'var(--text)' }}>Placeholder attribution</div>
        <div style={{ fontSize: 14, color: 'var(--text-weak)' }}>No customer quotes were supplied — replace before publishing.</div>
      </div>
    </section>
  );
}

function Stats() {
  return (
    <section style={{ background: 'var(--gradient-forest)', color: '#FCF9F6' }}>
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '64px 32px', display: 'flex', gap: 48 }}>
        {[['84,000+', 'Community members'], ['800+', 'Enterprise customers'], ['65', 'Graph algorithms'], ['ISO GQL', 'Standard query language']].map(([v, l]) => (
          <div key={l} style={{ flex: 1 }}>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 500, fontSize: 40, lineHeight: 1.2, fontFeatureSettings: '"lnum" 1, "pnum" 1' }}>{v}</div>
            <div style={{ fontSize: 14, color: 'rgba(252,249,246,0.85)', marginTop: 4 }}>{l}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section style={{ background: 'var(--brand-off-white)' }}>
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '96px 32px' }}>
        <div style={{ background: 'var(--brand-baltic-darkest)', borderRadius: 'var(--radius-2xl)', padding: 64, display: 'flex', alignItems: 'center', gap: 48 }}>
          <div style={{ flex: 1 }}>
            <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 500, fontSize: 40, lineHeight: 1.2, margin: 0, color: '#FCF9F6', fontFeatureSettings: '"lnum" 1, "pnum" 1' }}>
              Start with a free instance
            </h2>
            <p style={{ fontSize: 16, lineHeight: 1.5, color: '#CFD1D4', marginTop: 12, maxWidth: 480 }}>
              200,000 nodes and 400,000 relationships, no card required. Load a sample dataset and run your first traversal in under five minutes.
            </p>
          </div>
          <button style={{
            height: 48, padding: '0 24px', borderRadius: 'var(--radius-control)', border: 0, cursor: 'pointer',
            background: '#FCF9F6', color: '#014063', fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: 16, letterSpacing: '0.016rem', whiteSpace: 'nowrap',
          }}>Start free</button>
        </div>
      </div>
    </section>
  );
}

function HomePage() {
  return <div><Hero /><LogoBand /><Features /><Quote /><Stats /><CTA /></div>;
}

Object.assign(window, { HomePage });
