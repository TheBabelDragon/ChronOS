# Architecture & Future Progression

## Current phase

**Phase 1 — Temporal library** (this repository)

Stdlib-only Python package providing the temporal model, store,
timelines, branching, snapshots, replay, causality, provenance, and
thin adapters.

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
| 8 | self-state-kernel integration |
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
