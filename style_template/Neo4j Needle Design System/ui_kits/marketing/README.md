# Marketing UI kit

The marketing surface: home page and pricing page, built on the brand palette rather than the theme tokens.

**These pages are original compositions built from the Needle specification, not recreations of neo4j.com** — no site codebase, Figma file or screenshot was supplied. Copy and figures are illustrative.

## Files

| File | What it holds |
| --- | --- |
| `SiteChrome.jsx` | Sticky header with logo lockup and nav, dark footer |
| `HomePage.jsx` | Baltic gradient hero, customer logo band, three-up feature cards, quote band on Cream, Forest gradient stats, dark CTA panel |
| `PricingPage.jsx` | Three plan cards with the middle one featured, plus a self-managed band |

## Interactions

Header nav switches between Home and Pricing; the other nav items are inert placeholders. Everything else is static by design — this is a visual kit, not a working site.

## Rules this kit demonstrates

- Warm off-white `#FCF9F6` page background, never pure white.
- Gradients tonal within one hue (Baltic, Forest), 45°, lightest at top right.
- Periwinkle and Highlight Yellow used only as punctuation — a rule under the hero copy, a single dot in the release badge.
- Display headlines in Syne 500 with lining figures; **the word "Neo4j" is never set in Syne** — it appears only as supplied logo artwork or in Public Sans.
- Cream `#F2EAD4` as a band background for the quote section.
- Brand teal never appears on a button or a link; the buttons on light bands use the interface primary via `Button`.

## Placeholders to replace

- **Customer logos** — dashed boxes. No customer marks were supplied.
- **Quote attribution** — no customer quotes were supplied; the block is labelled as a placeholder in the page itself.
- **Hero imagery** — the spec describes natural, warm, landscape-and-water photography but supplied none. The hero uses a code specimen instead of an image.
