---
name: neo4j-needle-design
description: Use this skill to generate well-branded interfaces and assets for Neo4j (Needle design system), either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the readme.md file within this skill, and explore the other available files.
If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.
If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

Quick orientation:

- `styles.css` is the single entry point — link it and every token is available.
- `tokens/` holds the values. Theme tokens (`--canvas`, `--surface`, `--primary-fill`, …) drive interface controls; `tokens/brand.css` holds the marketing-only palette, which must never be used for controls.
- `components/` holds React primitives, each with a `.prompt.md` giving usage.
- `ui_kits/aura_console/` and `ui_kits/marketing/` show the two surfaces assembled.
- `assets/` holds the logos and the Syne font files. Never redraw or recolour a mark.

Hard rules: no pure white page backgrounds, no 90° card corners, no shadow heavier than the two defined levels, no two-hue gradients, brand teal `#4C99A4` never on a button or link, and never set the word "Neo4j" (or any word with a lowercase j) in Syne.
