"""
Temporal ABI — semantic operation identifiers.

This is a semantic contract, not a binary ABI. Future native or
kernel-level implementations can implement the same operations without
changing ChronOS semantics.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict


class TemporalOp(str, Enum):
    """Stable semantic operation identifiers."""

    BEGIN = "BEGIN"
    OBSERVE = "OBSERVE"
    TRANSITION = "TRANSITION"
    COMMIT = "COMMIT"
    SNAPSHOT = "SNAPSHOT"
    RESTORE = "RESTORE"
    FORK = "FORK"
    REPLAY = "REPLAY"
    TRACE = "TRACE"
    INTEGRITY = "INTEGRITY"


# Mapping from self-state-kernel public surface → Temporal ABI
KERNEL_TO_ABI: Dict[str, TemporalOp] = {
    "SELF.GET": TemporalOp.OBSERVE,
    "SELF.SET": TemporalOp.TRANSITION,
    "SELF.RUN": TemporalOp.TRANSITION,
    "SELF.QUERY": TemporalOp.OBSERVE,
    "GET": TemporalOp.OBSERVE,
    "SET": TemporalOp.TRANSITION,
    "RUN": TemporalOp.TRANSITION,
    "QUERY": TemporalOp.OBSERVE,
    "TRACE": TemporalOp.TRACE,
    "INTEGRITY": TemporalOp.INTEGRITY,
    "SNAPSHOT": TemporalOp.SNAPSHOT,
}


def map_kernel_op(name: str) -> TemporalOp:
    """Map a kernel surface name to a Temporal ABI operation."""
    key = name.upper() if name else ""
    if key in KERNEL_TO_ABI:
        return KERNEL_TO_ABI[key]
    # dotted forms
    if key.startswith("SELF."):
        return KERNEL_TO_ABI.get(key, TemporalOp.TRANSITION)
    raise KeyError(f"No Temporal ABI mapping for kernel operation {name!r}")


ALL_OPS = tuple(TemporalOp)
