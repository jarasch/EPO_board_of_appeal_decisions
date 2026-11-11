# Aura console UI kit

An interactive recreation of the product surface described by the Needle specification: instance management (canvas → surface → content) and a graph query workspace (canvas → content with floating panels).

**These screens are original compositions built from the Needle spec, not recreations of Neo4j's shipping Aura UI** — no product codebase, Figma file or screenshot was supplied. Content is fictional sample data.

## Screens

| File | Screen | Layout pattern |
| --- | --- | --- |
| `Shell.jsx` | Fixed side navigation, top bar, inline icon set | — |
| `InstancesScreen.jsx` | Instance list with stats, filters, table and create/delete dialogs | Management: canvas → surface → content |
| `InstanceDetailScreen.jsx` | Overview, Connect, Metrics and Settings tabs for one instance | Management |
| `QueryScreen.jsx` | Cypher editor, graph canvas, legend, inspector, zoom and results panels | Data: canvas → content, floating panels |

## Interactions

- Side nav switches screens; unbuilt surfaces show an honest empty state rather than invented UI.
- Filter and region select narrow the instance table live.
- Clicking an instance row opens its detail screen; the breadcrumb returns.
- **Create instance** and the row delete action open real dialogs.
- On Query: edit the Cypher and press **Run query** — a spinner runs, then results appear. Putting `PURCHASED_BY` in the query produces the error banner.
- Result tabs switch between graph summary, table and query plan.

## Notes

- Every visual value comes from `styles.css` tokens. Icons are inline 24px / 2px-stroke outlines matching the Lucide substitution documented in `readme.md`.
- The graph visualisation is a static layout using the graph node palette in order — it is a specimen, not a force-layout engine.
