Use `TextInput` for single-line entry. Error text names what is wrong and how to fix it.

```jsx
<TextInput label="Instance name" value={name} onChange={setName} helpText="Lowercase letters, numbers and hyphens." />
<TextInput label="Password" type="password" errorText="Must be at least 8 characters." />
```
