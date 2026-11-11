# Neo4j Needle Design System

Needle is the design system behind Neo4j's product UI and marketing surfaces. Neo4j is a graph database and knowledge-graph platform; the design system spans the Aura console, graph exploration and query tools, dashboards, and the marketing site.

The character of the system is calm, natural and confident. The palette is drawn from green landscapes, the deep sea and desert light, with warm neutrals and restrained accent use. It is deliberately not a bright generic SaaS blue: the interface primary is a deep sea blue (`#0A6190`), and the warmer brand hues (Baltic, Forest, Marigold, Hibiscus, Cream) are reserved for marketing.

## Sources

Everything in this system was built from material supplied directly by the user:

- **Brand specification** — a written Needle spec covering fonts, type scale, light and dark theme tokens, chart and graph-node palettes, radii, spacing, elevation, layout rules, the marketing brand palette, gradient rules, and an explicit "avoid" list. That spec is the source of truth; every value here is copied from it verbatim.
- **Logo pack** — full-colour, black and white marks, wordmarks and lockups (horizontal and stacked) in SVG, PNG, JPG, EPS and PDF, in RGB, CMYK and Pantone. Originals are in `uploads/`; the ones this system uses are copied into `assets/`.
- **Fonts** — `SyneNeo-Medium.otf`, `SyneNeo-SemiBold.otf`, `SyneNeo-Bold.otf`, supplied by the brand and copied into `assets/fonts/`.

No Figma file, codebase or repository was provided. No screenshots of the live product were provided. **The UI kits in this project are therefore original screens composed from the specification's layout rules and tokens — they are not recreations of Neo4j's shipping product UI.** If you want pixel-accurate product recreations, attach the product codebase or a Figma link and they can be rebuilt against it.

### Logo variants — what is actually present

Present in `assets/` and verified rendering:

| Variant | Wordmark | Mark only | Lockup (with strapline) |
| --- | --- | --- | --- |
| Full colour | `logo.svg`, `logo.png` | `logo-mark.svg` | `logo-lockup-horizontal.svg`, `logo-lockup-stacked.svg` |
| White / reversed | `logo-white.svg`, `logo-white.png` | `logo-mark-white.svg` | `logo-lockup-stacked-white.svg` |
| Black | `logo-black.svg` | `logo-mark-black.svg` | `logo-lockup-horizontal-black.svg` |

**Genuinely missing:** a white/reversed *horizontal* lockup in SVG — only the stacked white lockup was supplied as SVG (`logo-lockup-horizontal-white.png` exists in `uploads/` as a raster only). All `.eps` and `.pdf` originals are in `uploads/` but are not usable on the web.

**Repair note — the supplied SVG exports were broken.** `logo.svg`, `logo-mark.svg`, `logo-white.svg`, `logo-mark-white.svg`, `logo-black.svg`, `logo-mark-black.svg` and `logo-lockup-stacked-white.svg` each shipped with their `<style>` block stripped by the exporter. Each file contains three stacked layers (`#Full_color`, `#White`, `#Black`) whose visibility and fills were driven entirely by CSS classes (`.st0`–`.st3`) that were not in the file. With no stylesheet, all three layers rendered at once and every fill fell back to black — so the *white* mark rendered black on dark backgrounds.

These files were repaired, not recoloured: the two unused layers were removed and explicit `fill` attributes applied to the layer the filename names. The two colours used — `#014063` for the node mark and `#181414` for the wordmark — were read from the brand's own working exports (`logo-lockup-horizontal.svg`, `logo-lockup-stacked.svg`), which carry explicit fills. No colour was invented. **Ask the brand team for clean SVG exports and replace these.**

### Substitutions to be aware of

- **Public Sans** and **Fira Code** were not supplied as files. Both are open-source and load from Google Fonts. If Neo4j ships self-hosted copies, drop the files into `assets/fonts/` and replace the `@import` in `tokens/fonts.css`.
- **Icons** — no icon set was supplied. See ICONOGRAPHY below; the system currently uses a **Lucide substitution** (24px grid, 2px stroke, round caps, outline only). This is flagged, deliberate, and should be replaced when the real set arrives.

### Derived, not from source

Every colour, radius, spacing step, type value and elevation level in `tokens/` is copied verbatim from the supplied spec. The following are **derived** — the spec defines no value for them, so a choice was made and is marked as such in the CSS:

| Derived value | What was chosen | Why |
| --- | --- | --- |
| **Disabled states** | Light: fill `#E2E3E5`, text `#A8ACB2`, border `#E2E3E5`. Dark: fill `#3C3F44`, text `#818790`, border `#3C3F44`. | The spec defines no disabled token. These reuse existing border-weak and text-weakest values rather than introducing new colour. Consumed by Button, IconButton, TextInput, Select, Checkbox, Radio and Switch — replacing the previous blanket `opacity`, which no component now uses. |
| **Dark-theme elevation** | `none` — no dark shadow was invented. | The spec defines elevation for the light theme only. On dark surfaces, depth comes from `--border-weak` `#3C3F44` and the canvas→surface step `#1A1B1D` → `#212325`. |
| **Icon set** | Lucide, 24px / 2px stroke, outline only. | No icon set was supplied. |
| **Component-level spacing** | Button and input heights 28 / 36 / 44, card padding 16 / 24, internal gaps. | The spec gives a spacing scale but no per-component metrics. All chosen values sit on the scale except the exceptions listed below. |
| **Motion timings** | 120–160ms `ease-out` on colour and opacity. | The spec describes restraint but gives no durations. |

### Conformance audit — off-scale values

A pass over every `.jsx`, `.html` and `.css` file found the following values **not** on the spacing scale (2/4/6/8/12/16/20/24/32/48/64) or radius scale (4/6/8/12/16/24/full). These are listed rather than silently corrected — tell me which to change:

| Location | Value | What it does |
| --- | --- | --- |
| `components/feedback/Banner.jsx` | `marginTop: 1` | Optical alignment of the leading icon to the first text line |
| `components/forms/Checkbox.jsx` | `marginTop: 1` | Optical alignment of the box to the label baseline |
| `components/forms/Radio.jsx` | `marginTop: 1` | Same |
| `components/forms/Switch.jsx` | `top: 3` | Knob inset inside the 22px track |
| `ui_kits/aura_console/InstanceDetailScreen.jsx` | `gap: 3`, `borderRadius: 2` | Gap between paired chart bars; bar cap radius |
| `ui_kits/aura_console/QueryScreen.jsx` | `top: 130` | Vertical offset of the left and right floating panels below the editor panel |
| `ui_kits/marketing/HomePage.jsx` | `gap: 40` | Customer logo band spacing |
| `ui_kits/marketing/PricingPage.jsx` | `marginTop: 3` | Optical alignment of the check icon |
| `guidelines/spacing-scale.card.html` | `border-radius: 2px` | Cap on the 2px and 4px scale swatches, which cannot take a 4px radius |

All other spacing and radius values conform. Radii use the intent aliases (`--radius-control` 8px, `--radius-input` 8px, `--radius-card` 12px, `--radius-card-lg` 16px, `--radius-pill` full).

### Focus ring conformance

The ring is `2px solid var(--primary-focus)` at `2px` offset — `#30839D` light, `#5DB3BF` dark — declared once in `tokens/base.css` as `*:focus-visible`. Button, IconButton, Tabs, SideNavigation, Breadcrumbs and links inherit it.

`TextInput`, `Select` and the Cypher editor textarea originally opted out with `outline: none` and substituted a tint ring; they now use the token ring. On `TextInput` the ring sits on the field wrapper rather than the bare `<input>`, so the whole control rings as one. **No component falls back to a browser-default focus outline, and none suppresses the ring.**

### Typography binding

Verified in the browser: `.ndl-display` computes to `Syne`, `document.fonts.check('500 40px Syne')` returns `true`, and the only registered Syne faces are the three `@font-face` rules pointing at the supplied `assets/fonts/SyneNeo-*.otf`. **No Google Syne is imported anywhere.** Lining proportional figures resolve (`font-feature-settings: "lnum", "pnum"`).

No surface sets the word "Neo4j" in Syne. Every occurrence is in Public Sans, in Fira Code as query content, or is supplied logo artwork.

---

## CONTENT FUNDAMENTALS

**Voice.** Calm, plain and technically literate. The reader is assumed to be an engineer, data scientist or architect who does not need to be sold to twice. Confidence comes from precision, not from volume: state what a thing does and what it costs, then stop.

**Person.** Address the reader as *you*. Refer to the product by name rather than as *we* ("Aura provisions the instance", not "we'll spin one up for you"). Reserve *we* for company statements — pricing, policy, roadmap.

**Casing.** Sentence case everywhere: page titles, section headings, buttons, menu items, table headers, tabs, toasts. Never Title Case, never ALL CAPS as a styling device — a label that needs emphasis gets weight 700, not capitals. Product names keep their own casing: Neo4j, Aura, Cypher, Bloom, GDS.

**Buttons and actions.** Verb-first and specific. "Create instance", "Run query", "Connect to instance", "Download credentials". Not "Submit", "OK", "Get started now". Destructive actions name the object: "Delete instance", never just "Delete" when the object is off-screen.

**Empty and error states.** Say what happened, then what to do. "No instances yet. Create one to start querying." / "Query failed: unknown relationship type `PURCHASED_BY`. Check the type name or run `CALL db.relationshipTypes()`." Errors surface the real message, including Cypher or driver text — engineers debug faster with the raw string than with a friendly paraphrase.

**Numbers and units.** Real, specific, and never rounded into vagueness. "4 GB memory, 2 CPU" not "plenty of headroom". "1.2M nodes, 4.8M relationships". Latency in ms, size in GB, cost per hour.

**Technical terms.** Use graph vocabulary directly and consistently: node, relationship, label, property, pattern, traversal, index, constraint, instance, database. Do not translate them into generic database words (never "row", "table", "join").

**Marketing copy** runs a half-step warmer but never louder. Headlines are short declaratives set in Syne — "Connections change everything", "Ask harder questions of your data". Subheads in Public Sans explain the mechanism in one sentence. No superlative stacking, no "revolutionary", no exclamation marks.

**Emoji.** Not used. Not in product, not in marketing, not in docs.

**The "j" rule.** Never set the word "Neo4j" — or any word containing a lowercase *j* — in Syne. In this typeface the *j* is visually indistinguishable from an *i*. Use Public Sans for those words even inside a Syne headline, or use the supplied logo artwork.

---

## VISUAL FOUNDATIONS

### Colour

Two layers, and they must not be mixed:

1. **Theme tokens** drive every interface control. Light theme sits on a `#F5F6F6` canvas with `#FFFFFF` surfaces; dark theme sits on `#1A1B1D` canvas with `#212325` surfaces. Interface primary is `#0A6190` in light, flipping to the light Baltic `#8FE3E8` in dark so it stays legible on a near-black canvas. Semantic colours are Success (green), Warning (yellow), Danger (red-orange) and Discovery/AI (violet) — the last exists specifically to mark generated or AI-assisted content.
2. **Brand palette** is for marketing and hero surfaces only: Baltic, Forest, Marigold, Hibiscus, Cream, Dark Gray `#4F4E4D` and warm off-white. Periwinkle `#6A82FF` and Highlight Yellow `#FAFF00` are punctuation — a rule, an underline, a single dot — never a base or a large fill.

Never use brand teal `#4C99A4` on a button or a link. Never introduce a colour that is not in `tokens/`.

**Data colour** is a third, separate concern. Charts use a fixed categorical order of twelve; graph visualisations use a different, softer, twelve-colour node palette (pale yellow, orchid, coral, sky). Both are used in order, never picked for aesthetics.

### Backgrounds

No pure white page backgrounds. Light pages sit on `#F5F6F6`; white is a *surface*, something that sits on top. Marketing pages may use warm off-white `#FCF9F6` or Cream `#F2EAD4` as a band background.

Gradients are backgrounds only, never fills on type, icons or controls. A gradient must stay tonal within a single hue — Baltic or Forest only — run at 45 degrees, lightest at the top right. Two-hue gradients are forbidden.

No photographic textures, patterns or hand-drawn illustration are defined in the supplied spec. When imagery is needed the tone is natural and slightly warm — landscape, water, desert light — cool in the Baltic direction and warm in the Marigold direction, never saturated or high-contrast stock.

### Type

Syne 500 for display headlines at large sizes only, with proportional lining figures (`font-feature-settings: "lnum" 1, "pnum" 1`) — never oldstyle. Everything else, including every piece of UI text, is Public Sans: 400 body, 600 subheadings, 700 titles. Code is Fira Code 400.

Titles carry `+0.016rem` tracking; display and body do not. The scale tops out at 40px for display and 30px for Title 1 — this is a system for dense, information-rich screens, not for oversized hero type.

### Shape

Radii: 4, 6, 8, 12, 16, 24 and full. Controls and inputs are 8px. Cards are 12–16px. Pills and tags are full. Hard 90-degree corners are never used — even a full-bleed panel gets its corners softened where it meets another surface.

### Depth

Two elevation levels only:

- `raised` — `0 1px 2px rgba(26,27,29,0.18)`, for cards and surfaces that lift off the canvas
- `overlay` — `0 4px 8px rgba(26,27,29,0.12)`, for menus, popovers, dialogs and floating panels

**Both are light-theme only.** The source spec defines no dark-theme shadow and none was invented: in dark theme `--elevation-raised` and `--elevation-overlay` resolve to `none`, and depth is carried by the `#3C3F44` weak border plus the canvas-to-surface step from `#1A1B1D` to `#212325`.

Nothing heavier. Depth is otherwise expressed with borders (`#E2E3E5` weak, `#BBBEC3` strong) and with the canvas/surface/raised-surface stack.

### Cards

A card is a `#FFFFFF` surface, 12 or 16px radius, a 1px `#E2E3E5` border, and the `raised` shadow. Padding comes off the spacing scale — 16px for compact list cards, 24px for content cards. No coloured left borders, no gradient card backgrounds, no card that is only a shadow with no border.

### Interaction states

- **Hover on neutral surfaces** — a `#6F757E` overlay at 10%. It darkens light surfaces and lightens dark ones with one token, which is why it is expressed as an overlay rather than a colour.
- **Pressed on neutral surfaces** — the same overlay at 20%.
- **Hover on primary** — `#02507B` in light, `#5DB3BF` in dark (the light theme darkens, the dark theme lightens).
- **Pressed on primary** — `#014063` light, `#4C99A4` dark.
- **Danger** has its own hover and pressed pair.
- **Focus** is a 2px `#30839D` ring at 2px offset (light) — always visible, never removed.
- No scale, no lift, no shrink on press. Buttons change colour, not size.

### Motion

Restrained. Transitions are short colour and opacity changes — 120–160ms, `ease-out` — on hover, focus and state change. Panels and dialogs fade with a small translate (4–8px), not a slide or a bounce. No spring easing, no attention-seeking loops. The one place motion is expressive is graph visualisation, where force-layout settling is the animation.

### Transparency and blur

Used for exactly two things: the neutral hover/pressed overlays, and the floating panels over a graph canvas, where a surface at high opacity (not blur-heavy glass) keeps the visualisation legible beneath. No frosted-glass chrome elsewhere.

### Layout

Two patterns, chosen by screen type:

- **Data and graph-heavy screens** — canvas, then content, with floating panels. The visualisation reads as continuous beneath fixed UI; panels sit on top with `overlay` elevation rather than carving the viewport into columns.
- **Management and admin screens** — canvas, then a surface layer, then content. A conventional stacked layout: page background, a white surface, content inside it.

Fixed elements: the top bar and the left navigation are fixed; the graph canvas scrolls and zooms beneath them.

### Spacing

2, 4, 6, 8, 12, 16, 20, 24, 32, 48, 64. Nothing off this scale — no 10px, no 14px, no 36px.

---

## ICONOGRAPHY

**No icon set was supplied with the brand material.** The system links **Lucide** from CDN as a flagged substitution: 24px grid, 2px stroke, round caps and joins, outline-only. That weight and construction sits closest to the calm, technical tone of the rest of the system. **If Neo4j has its own icon font, sprite or SVG set, supply it and this substitution should be replaced.**

Usage rules that apply regardless of which set ships:

- **Outline only.** No filled icon variants, no duotone, no two-colour icons.
- **Sizes** come off the spacing scale: 16px inside dense controls and table rows, 20px in buttons and nav, 24px standalone.
- Icons take `--primary-icon` when interactive and part of a primary action, `--text-weak` when decorative or secondary, and the matching semantic text token inside a status message.
- Icons never carry the brand marketing colours.
- An icon alone is never the only label for a destructive or ambiguous action — pair with text or a tooltip.

**Emoji are never used as icons.** **Unicode glyphs are never used as icons** either — no arrows made from `→`, no bullets standing in for status dots. The one exception is arithmetic and comparison symbols inside code and query text, where they are content, not iconography.

**Brand marks** live in `assets/`. Use `logo-lockup-horizontal.svg` in headers and footers, `logo-mark.svg` (the three-node glyph alone) as a favicon, app icon or when space is tight, and the white variants on dark or Baltic surfaces. Never recolour the marks, never redraw them, never set the wordmark in live type — the supplied artwork is the only correct rendering.

---

## INDEX

**Root**

| File | What it is |
| --- | --- |
| `readme.md` | This document — context, content fundamentals, visual foundations, iconography |
| `SKILL.md` | Agent-Skills entry point, for use outside this project |
| `styles.css` | Global CSS entry point — a list of `@import`s only. Consumers link this one file |
| `thumbnail.html` | Homepage tile for the design system |

**Tokens** (`tokens/`) — `fonts.css` (`@font-face` + Google Fonts), `typography.css` (families, scale, type-role classes), `colors.css` (raw palette), `theme-light.css`, `theme-dark.css` (semantic aliases), `brand.css` (marketing palette + gradients), `data-viz.css` (chart and graph-node series), `spacing.css`, `shape.css` (radii + elevation), `base.css` (element resets, link colours, focus ring).

**Assets** (`assets/`) — full-colour, black and white wordmarks, the standalone mark, horizontal and stacked lockups (SVG + PNG), and the three SyneNeo font files under `assets/fonts/`.

**Components** (`components/`)

- `core/` — Button, IconButton, Tag, Badge, Card
- `forms/` — TextInput, Select, Checkbox, Radio, Switch
- `feedback/` — Banner, Dialog, Tooltip, LoadingSpinner
- `navigation/` — Tabs, Breadcrumbs, SideNavigation
- `data/` — DataTable, CodeBlock, GraphLegend

**UI kits** (`ui_kits/`)

- `aura_console/` — the product surface: instance list, instance detail, and a graph query workspace showing the floating-panel layout
- `marketing/` — the marketing surface: hero, feature band and pricing, showing the brand palette and gradient rules

**Guidelines** (`guidelines/`) — the foundation specimen cards that populate the Design System tab: colour, type, spacing, shape, elevation and brand cards.
