Use `Button` for any action a user can take; exactly one `fill="filled"` button per surface, everything else outlined or text.

```jsx
<Button color="primary" size="medium" onClick={run}>Run query</Button>
<Button fill="outlined" color="neutral">Cancel</Button>
<Button fill="filled" color="danger">Delete instance</Button>
```

- `fill`: `filled` | `outlined` | `text`. `color`: `primary` | `neutral` | `danger`.
- `size`: `small` (28px) | `medium` (36px) | `large` (44px). Radius is always 8px.
- Labels are sentence case and verb-first: "Create instance", not "Submit".
- Hover/press change colour only — never scale or lift.
