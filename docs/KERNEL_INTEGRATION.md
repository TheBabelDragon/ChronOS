# Kernel Integration

## Boundary

```
ChronOS  ←— Temporal ABI —→  self-state-kernel
```

ChronOS does **not** copy or re-implement self-state-kernel.

The public contract of
[self-state-kernel](https://github.com/TheBabelDragon/self-state-kernel)
is treated as an external dependency boundary.

## Discovered public surface (live)

From `self_state_kernel.Kernel` / `KernelState`:

| Surface | Role |
|---------|------|
| `Kernel.GET(path, default=None)` | Path-addressed read |
| `Kernel.SET(path, value)` | Path-addressed write |
| `Kernel.RUN(command)` | Command execution |
| `Kernel.QUERY(...)` | Query |
| `Kernel.integrity()` | Domain integrity hash (SHA-256) |
| `Kernel.trace_export()` | Kernel-side trace records |
| `Kernel.state.snapshot()` | Full domain state dict |
| `Kernel.state.get` / `set` / `values` | `KernelState` accessors |
| `create_kernel()` | Factory |

## Adapter

`chronos.adapters.self_state.SelfStateAdapter` provides:

| Method | Role |
|--------|------|
| `capture_state(kernel)` | OBSERVE → temporal state |
| `restore_state(kernel, state)` | RESTORE domain from temporal state |
| `apply_event(kernel, op, payload, …)` | TRANSITION for SELF.SET / RUN / … |
| `state_identity(kernel)` | ChronOS identity of current domain |
| `trace()` | Temporal/causal history |
| `integrity(kernel)` | State identity observation |
| `snapshot_head()` | ChronOS snapshot of timeline head |

The adapter speaks only the minimal `KernelProtocol`
(`GET` / `SET` / `integrity` / `state.snapshot`). It does not import
private kernel modules and does not own:

- SELF command semantics
- strict boolean policy
- module dispatch
- CMD4 semantics
- kernel error semantics
- domain-specific state meaning

## Protocol

```python
class KernelProtocol(Protocol):
    def GET(self, path: str, default: Any = None) -> Any: ...
    def SET(self, path: str, value: Any) -> Any: ...
    def integrity(self) -> str: ...
    @property
    def state(self) -> Any: ...  # exposes .snapshot() -> dict
```
