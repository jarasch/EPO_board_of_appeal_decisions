Use `CodeBlock` for any Cypher or driver code shown to the user. Show the real query, never a paraphrase.

```jsx
<CodeBlock showLineNumbers onCopy={copy} code={`MATCH (p:Person)-[:WORKS_AT]->(c:Company)
WHERE c.name = 'Neo4j'
RETURN p.name LIMIT 25`} />
```
