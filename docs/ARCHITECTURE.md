# Architecture & Future Progression

## Current phase

**Phase 1 — Temporal library** (this repository)

Stdlib-only Python package providing the temporal model, store,
timelines, branching, snapshots, replay, causality, provenance, and
thin adapters.

The `SelfStateAdapter` implements the Temporal ABI mapping against the
public surface of [self-state-kernel](https://github.com/TheBabelDragon/self-state-kernel).
This is library-level integration (Phase 1), not the full Phase 8–9
kernel-level / native work.

## Roadmap

| Phase | Description |
|-------|-------------|
| 1 | Temporal library ← **current** |
| 2 | Temporal runtime |
| 3 | Process checkpoint/replay |
| 4 | Temporal filesystem model |
| 5 | Temporal scheduler |
| 6 | Temporal IPC |
| 7 | Temporal ABI (native) |
| 8 | self-state-kernel integration (deep / runtime) |
| 9 | Kernel-level implementation |
| 10 | ChronOS operating system |

Phase 10 must emerge from the temporal model. It is not a conventional
OS with a “time travel” feature bolted on, and it is **not claimed**
to exist today.

## Stack position

```
                       CHRONOS
             TIME / HISTORY / CAUSALITY
                         │
                  TEMPORAL ABI
                         │
                         ▼
                 SELF-STATE-KERNEL
                STATE / EXECUTION / TRACE
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           MetaField  MultiFlow   field-os
              │          │          │
           WaveBridge   Aurora    hardware
```

## Ownership

| Concern | Owner |
|---------|-------|
| Logical time, events, states, timelines | ChronOS |
| Branching, snapshots, replay, causality | ChronOS |
| Domain state values and execution | self-state-kernel (or other domain kernels) |
| SELF commands, CMD4, strict bool, modules | self-state-kernel |
| Thin translation (GET/SET → OBSERVE/TRANSITION) | `SelfStateAdapter` |
