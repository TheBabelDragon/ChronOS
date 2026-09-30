# Deterministic Replay

Replay reconstructs state transitions from events.

```python
states = replay(timeline, from_state=None, to_state=None, event_handler=None)
ids = assert_deterministic_replay(timeline)
```

## Requirements

- Every nondeterministic input (random values, sensors, network,
  user input, hardware observations, external timestamps) **must** be
  captured as event payload.
- Same inputs → same state identities.
- Replay does not mutate the original timeline.
- Missing `result_state_id` or missing committed states fail explicitly.

## Verification

`assert_deterministic_replay(timeline)` runs the segment twice and
compares state identity sequences. Divergence raises `AssertionError`.
