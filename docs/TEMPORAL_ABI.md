# Temporal ABI

Semantic contract between ChronOS and execution kernels.

This is a **semantic** ABI first. No binary layout is defined yet.
The purpose is to keep future native/kernel implementations aligned
with ChronOS's conceptual model.

Executable identifiers live in `chronos.abi.TemporalOp`.

## Operations

| Operation | Meaning |
|-----------|---------|
| `BEGIN` | Open a temporal transaction / observation window |
| `OBSERVE` | Read current domain state without committing a domain mutation |
| `TRANSITION` | Apply a domain operation; produce a new temporal state |
| `COMMIT` | Finalize a pending transition into the timeline |
| `SNAPSHOT` | Create an explicit checkpoint of a committed state |
| `RESTORE` | Restore domain state from a snapshot / temporal state |
| `FORK` | Create a branch sharing immutable ancestry |
| `REPLAY` | Reconstruct states deterministically from events |
| `TRACE` | Return provenance / causal history |
| `INTEGRITY` | Return state identity and integrity metadata |

## Mapping to self-state-kernel

| Kernel surface | ChronOS |
|----------------|---------|
| `SELF.GET` / `GET` | `OBSERVE` |
| `SELF.SET` / `SET` | `TRANSITION` |
| `SELF.RUN` / `RUN` | `TRANSITION` (execution event) |
| `SELF.QUERY` / `QUERY` | `OBSERVE` / query event |
| `TRACE` | `TRACE` |
| `INTEGRITY` | `INTEGRITY` |
| `SNAPSHOT` | `SNAPSHOT` |

## Invariants

- Logical time is advanced only by ChronOS.
- Domain kernels never mutate committed temporal states.
- Nondeterministic inputs must appear in event payloads.
- Adapters remain thin; domain semantics stay in domain systems.
