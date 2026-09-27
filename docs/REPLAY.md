# Deterministic Replay

Replay reconstructs state transitions from events.

```python
states = replay(timeline, from_state=None, to_state=None, event_handler=None)
```

## Requirements

- Every nondeterministic input (random values, sensors, network,
  user input, hardware observations, external timestamps) **must** be
  captured as event payload.
- Same inputs → same state identities.
- Replay does not mutate the original timeline.

## Verification

`assert_deterministic_replay(timeline)` runs the segment twice and
compares state identity sequences.
