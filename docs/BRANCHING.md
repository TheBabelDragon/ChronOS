# Branching

## Semantics

```
                    S0
                    │
                    S1
                    │
                    S2
                  /    \
                S3      S3'
                │        │
                S4      S4'
```

`fork(timeline, state_id, name=None)` creates a new timeline whose
root is a re-addressed view of the fork state under a new
`timeline_id`. Immutable ancestry is shared via the store; history is
**never copied**.

## Branch metadata

- `branch_id` (timeline id)
- `parent_timeline`
- `fork_state`
- `creation logical time`
- optional name

Branches remain independently replayable.
