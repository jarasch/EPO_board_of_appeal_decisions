Use `IconButton` for compact toolbar and panel actions where the icon alone is unambiguous.

```jsx
<IconButton ariaLabel="Close panel" onClick={close}><X size={20} /></IconButton>
<IconButton ariaLabel="Zoom in" fill="outlined" size="small"><Plus size={16} /></IconButton>
```

Icon sizes: 16px in a small button, 20px in medium, 24px in large. Outline icons only.
