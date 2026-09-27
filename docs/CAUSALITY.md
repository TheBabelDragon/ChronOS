# Causality

## Temporal order ≠ causal relationship

An event occurring after another does **not** automatically mean it was
caused by it. ChronOS requires explicit causal edges.

## Representation

- `TemporalEvent.causal_parents` — tuple of parent event IDs
- `CausalGraph` — directed edges parent → child

## Queries

| Query | Meaning |
|-------|---------|
| `parents(node)` | Direct causal parents |
| `children(node)` | Direct causal children |
| `lineage(node)` / `why(node)` | Full ancestor chain (roots first) |
| `causal_path(src, dst)` | Shortest causal path, or None |

## Example

```
e1 (INC) ──causes──► e2 (INC) ──causes──► e3 (INC)
e4 (NOTE)   ← temporally after e3, but no causal edge
```

`why(e3)` returns the INC chain. `causal_path(e1, e4)` returns None.
