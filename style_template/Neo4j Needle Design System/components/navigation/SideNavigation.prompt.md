Use `SideNavigation` as the fixed left rail on product screens. It is always fixed; the canvas scrolls beneath it.

```jsx
<SideNavigation value={page} onChange={setPage} header={<img src="assets/logo-lockup-horizontal.svg" width="132" />}
  items={[{value:'instances',label:'Instances',icon:<Database size={20}/>},{isSection:true,label:'Tools'},{value:'query',label:'Query',icon:<Terminal size={20}/>}]} />
```
