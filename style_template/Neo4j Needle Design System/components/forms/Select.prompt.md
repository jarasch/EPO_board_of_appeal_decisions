Use `Select` for one choice from a known list of 4+. For 2–3 short options prefer `Radio`.

```jsx
<Select label="Region" value={region} onChange={setRegion}
  options={[{value:'eu-west-1',label:'Europe (Ireland)'},{value:'us-east-1',label:'US East (N. Virginia)'}]} />
```
