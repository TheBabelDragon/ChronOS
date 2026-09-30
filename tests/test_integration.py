"""
End-to-end integration:

    self-state-kernel (or double)
          |
    SelfStateAdapter
          |
       ChronOS timeline
          |
       event/state → snapshot → fork → replay

When the real kernel is importable it is used; otherwise the protocol
double exercises the same adapter boundary.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from chronos import (
    Timeline,
    create_snapshot,
    restore_snapshot,
    fork,
    replay,
    assert_deterministic_replay,
    CausalGraph,
)
from chronos.adapters.self_state import SelfStateAdapter


_KERNEL_PATH = Path(__file__).resolve().parents[2] / "self-state-kernel"
if _KERNEL_PATH.is_dir():
    sys.path.insert(0, str(_KERNEL_PATH))

try:
    from self_state_kernel import create_kernel  # type: ignore

    HAS_REAL_KERNEL = True
except Exception:
    HAS_REAL_KERNEL = False
    create_kernel = None  # type: ignore


def _make_kernel():
    if HAS_REAL_KERNEL:
        return create_kernel()
    from tests.test_adapter import FakeKernel

    return FakeKernel()


@pytest.mark.skipif(not HAS_REAL_KERNEL, reason="self-state-kernel not on path")
def test_real_kernel_e2e():
    kernel = create_kernel()
    tl = Timeline.create_root({})
    adapter = SelfStateAdapter(tl)

    s0 = adapter.capture_state(kernel)
    assert isinstance(s0.state_root, dict)

    event, s1 = adapter.apply_event(kernel, "SET", path="x", value=42)
    assert kernel.GET("x") == 42
    assert s1.state_root.get("x") == 42

    snap = create_snapshot(s1)
    restored = restore_snapshot(snap, tl.store)
    assert restored.state_id == s1.state_id

    branch = fork(tl, s1.state_id, name="alt")
    branch_adapter = SelfStateAdapter(branch)
    branch_adapter.apply_event(kernel, "SET", path="x", value=100)
    adapter.restore_state(kernel, s1)
    assert kernel.GET("x") == 42

    ids = assert_deterministic_replay(tl)
    assert s0.state_id in ids
    assert s1.state_id in ids

    g = CausalGraph.from_store(tl.store)
    assert len(g.nodes()) >= 1

    integ = adapter.integrity(kernel)
    assert integ["kernel_integrity"] == kernel.integrity()


def test_protocol_double_e2e():
    """Always-run integration with the protocol double."""
    kernel = _make_kernel()
    tl = Timeline.create_root({"seed": True})
    adapter = SelfStateAdapter(tl)

    adapter.capture_state(kernel)
    event, state = adapter.apply_event(kernel, "SET", path="flag", value=True)
    snap = adapter.snapshot_head()
    assert snap.state_id == state.state_id

    branch = tl.fork(state.state_id)
    assert branch.parent_timeline_id == tl.timeline_id

    states = replay(tl)
    assert states[-1].state_id == tl.head_state_id

    assert_deterministic_replay(tl)
