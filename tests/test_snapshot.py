"""SNAPSHOT tests."""

from chronos import (
    Timeline,
    create_snapshot,
    restore_snapshot,
    compare_snapshots,
)


def test_create_and_identity():
    tl = Timeline.create_root({"x": 1})
    tl.transition({"x": 2})
    snap = create_snapshot(tl.head())
    assert snap.state_id == tl.head().state_id
    assert snap.timeline_id == tl.timeline_id
    assert snap.logical_time == tl.head().logical_time
    assert snap.snapshot_id


def test_restoration():
    tl = Timeline.create_root({"x": 1})
    _, s = tl.transition({"x": 2})
    snap = create_snapshot(s)
    restored = restore_snapshot(snap, tl.store)
    assert restored.state_id == s.state_id
    assert restored.state_root == {"x": 2}


def test_compare():
    tl = Timeline.create_root({"x": 1})
    a = create_snapshot(tl.head())
    tl.transition({"x": 2})
    b = create_snapshot(tl.head())
    diff = compare_snapshots(a, b)
    assert diff["same_snapshot"] is False
    assert diff["same_state"] is False
    same = compare_snapshots(a, a)
    assert same["same_snapshot"] is True


def test_serialization():
    tl = Timeline.create_root({})
    snap = create_snapshot(tl.head())
    d = snap.to_dict()
    from chronos.snapshot import Snapshot

    snap2 = Snapshot.from_dict(d)
    assert snap2.snapshot_id == snap.snapshot_id
