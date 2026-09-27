# Snapshots

A snapshot is an explicit checkpoint: a reference to an immutable
`TemporalState` plus enough metadata to restore it.

## Fields

- `snapshot_id` — deterministic identity
- `state_id` — referenced state
- `timeline_id`
- `logical_time`
- `state_root`
- `created_from`
- `provenance`

## Operations

```python
snap = create_snapshot(state)
restored = restore_snapshot(snap, store)
diff = compare_snapshots(a, b)
```

Snapshots are not mutable containers. They do not own a separate copy
of history; they point at committed states already present in the store.
