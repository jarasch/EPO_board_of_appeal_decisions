Use `GraphLegend` above or beside any graph visualisation. Colours are assigned by position in the node palette — never picked by hand.

```jsx
<GraphLegend labels={[{label:'Person',count:412},{label:'Company',count:38},{label:'Product',count:1204}]}
  activeLabels={active} onToggle={toggle} />
```
