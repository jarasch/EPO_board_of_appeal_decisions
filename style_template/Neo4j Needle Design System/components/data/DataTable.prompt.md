Use `DataTable` for query results and management lists. Set `isDense` for result grids, leave it off for admin lists.

```jsx
<DataTable isDense columns={[
  {key:'name',header:'Name'},
  {key:'id',header:'Element id',isCode:true},
  {key:'status',header:'Status',render:r=><Badge color="success" hasDot>{r.status}</Badge>},
]} rows={rows} />
```
