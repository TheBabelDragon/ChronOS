"""
ChronOS — deterministic temporal substrate.

Provides immutable state, append-only events, logical time,
snapshots, branching, deterministic replay, provenance, and
causal traversal for the TheBabelDragon stack.
"""

from .clock import LogicalClock
from .event import TemporalEvent
from .state import TemporalState
from .store import TemporalStore
from .timeline import Timeline
from .branch import fork
from .snapshot import Snapshot, create_snapshot, restore_snapshot, compare_snapshots
from .replay import replay
from .causality import CausalGraph
from .provenance import Provenance

__all__ = [
    "LogicalClock",
    "TemporalEvent",
    "TemporalState",
    "TemporalStore",
    "Timeline",
    "fork",
    "Snapshot",
    "create_snapshot",
    "restore_snapshot",
    "compare_snapshots",
    "replay",
    "CausalGraph",
    "Provenance",
]

__version__ = "0.1.0"
