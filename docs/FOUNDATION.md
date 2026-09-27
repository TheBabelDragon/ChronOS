# ChronOS Foundation

## Time as a first-class primitive

ChronOS treats time not as a side-effect of logging but as the substrate
on which state evolves.

```
Event
  ↓
State transition
  ↓
new immutable State
  ↓
Timeline
  ↓
Snapshot / branch / replay / causal traversal
```

## Authoritative clock

- **Logical time** is authoritative.
- **Wall-clock time** may appear as metadata only.
- The clock is monotonic, deterministic, serializable, and independent
  of the host system clock.

## Immutability

Once a state is committed it cannot be mutated. A transition always
produces a *new* state. Events are append-only.

## Graph, not list

A timeline is a DAG of states linked by events. Branches share
immutable ancestry; history is never copied.

## Explicit causality

An event occurring after another does not imply causation.
Causal edges must be declared. ChronOS distinguishes temporal order
from causal relationship.

## Provenance

Provenance is retained for every meaningful transition and is never
silently discarded.

## Domain boundary

ChronOS owns temporal semantics. Domain systems (self-state-kernel,
field-os, MetaField, MultiFlow, …) own domain semantics. Adapters are
thin translation layers.
