# Kernel Integration

## Boundary

```
ChronOS  ←—— Temporal ABI ——→  self-state-kernel
```

ChronOS does **not** copy or re-implement self-state-kernel.

The public contract of
[self-state-kernel](https://github.com/TheBabelDragon/self-state-kernel)
is treated as an external dependency boundary.

## Adapter

`chronos.adapters.self_state.SelfStateAdapter` provides:

| Method | Role |
|--------|------|
| `capture_state(kernel)` | OBSERVE → temporal state |
| `restore_state(kernel, state)` | RESTORE domain from temporal state |
| `apply_event(kernel, op, payload)` | TRANSITION for SELF.SET / RUN / … |
| `state_identity(kernel)` | ChronOS identity of current domain |
| `trace()` | Temporal/causal history |
| `integrity(kernel)` | State identity observation |

The adapter speaks only the minimal `KernelProtocol`
(`get_state` / `set_state`). It does not import private kernel modules
and does not own:

- SELF command semantics
- strict boolean policy
- module dispatch
- CMD4 semantics
- kernel error semantics
- domain-specific state meaning
