# Temporal Model

## Entities

| Entity | Role |
|--------|------|
| `LogicalClock` | Monotonic logical time |
| `TemporalEvent` | Immutable unit of change |
| `TemporalState` | Immutable snapshot of domain state + temporal metadata |
| `TemporalStore` | Append-only store of events and states |
| `Timeline` | Graph of states/events with head and root |
| `Snapshot` | Explicit checkpoint referencing a state |
| `CausalGraph` | Explicit causal edges |
| `Provenance` | Source / operation / actor / context |

## State identity

State identity is a SHA-256 over a canonical serialization of:

- timeline_id
- logical_time
- parent_state
- causal_parents
- state_root (canonicalized)
- provenance

Canonicalization supports dict, list, tuple, str, int, float, bool, null
and nested structures. Unsupported objects require an explicit serializer.

## Event identity

Event identity is a SHA-256 over a canonical serialization of event
fields (excluding the computed `event_id` itself).

## Transition

```
parent_state ──event──► new_state
```

The parent remains unchanged. The new state records `parent_state` and
`logical_time`.
