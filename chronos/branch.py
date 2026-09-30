"""
Immutable temporal forks.

Branches share immutable ancestry via the store; history is never copied.
"""

from __future__ import annotations

import uuid
from typing import Optional

from .clock import LogicalClock
from .provenance import Provenance
from .state import TemporalState
from .timeline import Timeline


def _new_timeline_id(prefix: str = "br") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def fork(
    timeline: Timeline,
    state_id: Optional[str] = None,
    *,
    name: Optional[str] = None,
    timeline_id: Optional[str] = None,
) -> Timeline:
    """
    Create a new timeline whose starting point is the selected ancestor.

    The fork state is re-addressed under a new timeline_id so that
    subsequent transitions on the branch produce states belonging to
    the branch while the original timeline and its states remain
    untouched. Ancestry is preserved through parent_state / causal
    links and the shared store — historical objects are not cloned.
    """
    fork_from_id = state_id or timeline.head_state_id
    ancestor = timeline.store.get_state(fork_from_id)
    if ancestor is None:
        raise ValueError(f"Unknown fork state: {fork_from_id}")

    new_tid = timeline_id or _new_timeline_id()
    # Branch clock continues from the ancestor's logical time so that
    # subsequent ticks remain monotonic relative to shared history.
    clock = LogicalClock(_time=ancestor.logical_time, _origin=0)

    # Re-address the fork point under the new timeline identity.
    # parent_state still points at the shared ancestor so causal
    # and temporal ancestry remain explicit and traversable.
    branch_root = TemporalState(
        timeline_id=new_tid,
        logical_time=ancestor.logical_time,
        state_root=ancestor.state_root,
        parent_state=ancestor.state_id,  # shared ancestry
        causal_parents=ancestor.causal_parents,
        provenance=Provenance(
            source="chronos",
            operation="FORK",
            context={
                "parent_timeline": timeline.timeline_id,
                "fork_state": ancestor.state_id,
                "name": name,
            },
            parent_events=ancestor.causal_parents,
        ),
    )
    timeline.store.put_state(branch_root)

    return Timeline(
        store=timeline.store,
        timeline_id=new_tid,
        clock=clock,
        root_state_id=branch_root.state_id,
        head_state_id=branch_root.state_id,
        parent_timeline_id=timeline.timeline_id,
        fork_state_id=ancestor.state_id,
        name=name,
    )
