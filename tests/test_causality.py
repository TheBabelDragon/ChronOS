"""CAUSALITY tests."""

from chronos import Timeline, CausalGraph, TemporalEvent


def test_explicit_parents():
    tl = Timeline.create_root({})
    e1, _ = tl.transition({"n": 1}, causal_parents=())
    e2, _ = tl.transition({"n": 2}, causal_parents=(e1.event_id,))
    e3, _ = tl.transition({"n": 3}, causal_parents=(e2.event_id,))
    e4, _ = tl.transition({"note": True}, causal_parents=())

    g = CausalGraph.from_store(tl.store)
    assert g.parents(e2.event_id) == [e1.event_id]
    assert g.children(e1.event_id) == [e2.event_id]
    assert e1.event_id in g.ancestors(e3.event_id)
    assert e3.event_id in g.descendants(e1.event_id)


def test_causal_path():
    tl = Timeline.create_root({})
    e1, _ = tl.transition({"n": 1}, causal_parents=())
    e2, _ = tl.transition({"n": 2}, causal_parents=(e1.event_id,))
    e3, _ = tl.transition({"n": 3}, causal_parents=(e2.event_id,))
    e4, _ = tl.transition({"note": True}, causal_parents=())

    g = CausalGraph.from_events(tl.events())
    path = g.causal_path(e1.event_id, e3.event_id)
    assert path == [e1.event_id, e2.event_id, e3.event_id]
    assert g.causal_path(e1.event_id, e4.event_id) is None


def test_temporal_vs_causal():
    """Later logical time does not imply causation."""
    e_early = TemporalEvent(
        event_type="T", logical_time=1, source="s", causal_parents=()
    )
    e_late = TemporalEvent(
        event_type="T", logical_time=99, source="s", causal_parents=()
    )
    g = CausalGraph.from_events([e_early, e_late])
    assert g.causal_path(e_early.event_id, e_late.event_id) is None
    assert g.parents(e_late.event_id) == []


def test_why_lineage():
    tl = Timeline.create_root({})
    e1, _ = tl.transition({"n": 1}, causal_parents=())
    e2, _ = tl.transition({"n": 2}, causal_parents=(e1.event_id,))
    g = CausalGraph.from_store(tl.store)
    lineage = g.why(e2.event_id)
    assert lineage[-1] == e2.event_id
    assert e1.event_id in lineage
