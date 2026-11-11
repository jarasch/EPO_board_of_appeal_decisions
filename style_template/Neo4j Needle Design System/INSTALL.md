# Using the Needle design system on another machine

No build step, no npm install. Everything needed is in this folder.

## 1. Copy the folder

Drop the whole unzipped folder anywhere on disk. Keep the structure intact — paths inside the files are relative.

## 2. Use it in an HTML page

```html
<link rel="stylesheet" href="path/to/needle/styles.css">
<script src="path/to/needle/_ds_bundle.js"></script>
```

`styles.css` carries every token (colour, type, spacing, shape, elevation) as CSS custom properties, plus the `@font-face` rules. The bundle exposes the React components on a global namespace:

```html
<div id="root"></div>
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js"></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js"></script>
<script>
  const { Button, TextInput, Card } = window.Neo4jNeedleDesignSystem_eb581b;
  ReactDOM.createRoot(document.getElementById('root'))
    .render(React.createElement(Button, { variant: 'primary' }, 'Run query'));
</script>
```

React 18 must be loaded before the bundle is used. The namespace is `Neo4jNeedleDesignSystem_eb581b` (also recorded in `_ds_manifest.json`); alias it locally if you prefer: `const N = window.Neo4jNeedleDesignSystem_eb581b`.

## 3. Browse the system

Open any `.html` file in `components/`, `guidelines/` or `tokens/` directly in a browser — each is a self-contained specimen card. `thumbnail.html` is the brand tile.

`ui_kits/` holds two worked examples (Aura console, marketing site) showing the components in composition.

## What's in here

| Path | Contents |
| --- | --- |
| `styles.css` | Tokens + font faces. The only stylesheet you need to link. |
| `_ds_bundle.js` | Compiled components on `window.<Namespace>`. |
| `_ds_manifest.json` | Machine-readable index: namespace, components, tokens, fonts. |
| `components/` | Source `.jsx` + `.d.ts` types + specimen cards. |
| `tokens/`, `guidelines/` | Specimen cards for colour, type, spacing, brand. |
| `assets/` | Logos and brand marks. |
| `ui_kits/` | Two example applications. |
| `readme.md` | Authoring notes and the open-items list. |

Dark theme: set `data-theme="dark"` on `<html>` or any container — the dark token scope is defined in `styles.css`.

## Caveats to pass on

- Icons are Lucide substitutions, not Neo4j's own icon set.
- Elevation tokens are defined for the light theme only.
- Logo SVGs were repaired from stripped exports; replace with clean brand-team files when available. The white horizontal lockup exists as PNG only.
