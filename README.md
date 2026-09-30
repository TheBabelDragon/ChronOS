# ChronOS

Deterministic temporal substrate for the TheBabelDragon stack.

ChronOS owns **time, history, causality, replay, snapshots, and branching**.  
Domain kernels (e.g. [self-state-kernel](https://github.com/TheBabelDragon/self-state-kernel)) own **state and execution**.

```
self-state-kernel
        ▲
        │
  Temporal ABI
        │
        ▼
     ChronOS
        │
   time / history
   causality
   replay
   snapshots
   branching
```

## Status

**Phase 1 — Temporal library** (this repository). Stdlib-only Python package.

## Install

```bash
pip install -e ".[dev]"
```

## Minimal example

```python
from chronos import Timeline, create_snapshot, fork, replay, assert_deterministic_replay
from chronos.adapters.self_state import SelfStateAdapter

tl = Timeline.create_root({"counter": 0})

# Domain-style transitions recorded as immutable history
tl.transition({"counter": 1}, payload={"op": "inc"})
tl.transition({"counter": 2}, payload={"op": "inc"})

snap = create_snapshot(tl.head())
branch = fork(tl, tl.head().parent_state, name="alt")
branch.transition({"counter": 99}, payload={"op": "set"})

assert_deterministic_replay(tl)
states = replay(tl)
print([s.state_id[:8] for s in states])
```

### With self-state-kernel adapter

```python
from chronos import Timeline
from chronos.adapters.self_state import SelfStateAdapter
from self_state_kernel import create_kernel

kernel = create_kernel()
tl = Timeline.create_root({})
adapter = SelfStateAdapter(tl)

adapter.capture_state(kernel)                           # OBSERVE
adapter.apply_event(kernel, "SET", path="x", value=42)  # TRANSITION
snap = adapter.snapshot_head()                          # SNAPSHOT
adapter.restore_state(kernel, tl.head())                # RESTORE
print(adapter.integrity(kernel))                        # INTEGRITY
print(adapter.trace())                                  # TRACE
```

## Public API

| Symbol | Role |
|--------|------|
| `LogicalClock` | Monotonic logical time |
| `TemporalEvent` | Immutable unit of change |
| `TemporalState` | Immutable domain + temporal metadata |
| `TemporalStore` | Append-only event/state store |
| `Timeline` | Head + graph of states/events |
| `fork` | Immutable temporal branch |
| `Snapshot` / `create_snapshot` / `restore_snapshot` / `compare_snapshots` | Checkpoints |
| `replay` / `assert_deterministic_replay` | Deterministic reconstruction |
| `CausalGraph` | Explicit causal traversal |
| `Provenance` | Source / operation / actor / context |
| `TemporalOp` | Semantic Temporal ABI operations |

## Invariants

- Committed states and events are immutable
- Events are append-only
- Logical time is authoritative; wall-clock is metadata only
- Branches share immutable ancestry (no history cloning)
- Causality is explicit (`causal_parents`), not inferred from time
- Replay is deterministic and does not mutate the original timeline
- Adapters stay thin; domain semantics stay in domain kernels

## Docs

- [FOUNDATION](docs/FOUNDATION.md)
- [MODEL](docs/MODEL.md)
- [ARCHITECTURE](docs/ARCHITECTURE.md)
- [TEMPORAL_ABI](docs/TEMPORAL_ABI.md)
- [KERNEL_INTEGRATION](docs/KERNEL_INTEGRATION.md)
- [BRANCHING](docs/BRANCHING.md)
- [SNAPSHOTS](docs/SNAPSHOTS.md)
- [REPLAY](docs/REPLAY.md)
- [CAUSALITY](docs/CAUSALITY.md)

## Roadmap

| Phase | Description |
|-------|-------------|
| 1 | Temporal library ← **current** |
| 2 | Temporal runtime |
| 3 | Process checkpoint/replay |
| 4 | Temporal filesystem |
| 5 | Temporal scheduler |
| 6 | Temporal IPC |
| 7 | Native Temporal ABI |
| 8 | self-state-kernel integration (adapter present in Phase 1) |
| 9 | Kernel-level implementation |
| 10 | ChronOS OS |

## License

MIT
