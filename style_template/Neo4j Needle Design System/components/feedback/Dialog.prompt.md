Use `Dialog` for a decision that must be made before continuing. The title is a sentence-case question or statement; the confirm button names the object.

```jsx
<Dialog isOpen={open} title="Delete instance orders-prod?" onClose={close}
  actions={<><Button fill="outlined" color="neutral" onClick={close}>Cancel</Button>
            <Button color="danger" onClick={del}>Delete instance</Button></>}>
  This removes 1.2M nodes and cannot be undone.
</Dialog>
```

Renders `position:absolute`, so give the containing surface `position:relative`.
