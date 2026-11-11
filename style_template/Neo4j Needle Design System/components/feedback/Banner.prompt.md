Use `Banner` for a message tied to the surface it sits on. Say what happened, then what to do.

```jsx
<Banner type="danger" title="Query failed"
  actions={<Button fill="outlined" size="small">View log</Button>}>
  Unknown relationship type `PURCHASED_BY`. Run <code>CALL db.relationshipTypes()</code> to list valid types.
</Banner>
```

`type="discovery"` marks AI-generated or AI-assisted content.
