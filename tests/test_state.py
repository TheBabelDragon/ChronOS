"""STATE tests."""

import pytest

from chronos import TemporalState, Provenance
from chronos.state import canonicalize


def test_deterministic_identity():
    s1 = TemporalState(
        timeline_id="tl1",
        logical_time=0,
        state_root={"a": 1, "b": [2, 3]},
    )
    s2 = TemporalState(
        timeline_id="tl1",
        logical_time=0,
        state_root={"b": [2, 3], "a": 1},
    )
    assert s1.state_id == s2.state_id


def test_canonicalization():
    assert canonicalize({"z": 1, "a": 2}) == {"a": 2, "z": 1}
    assert canonicalize((1, 2)) == [1, 2]


def test_unsupported_value_fails():
    class Weird:
        pass

    with pytest.raises(TypeError):
        TemporalState(
            timeline_id="tl",
            logical_time=0,
            state_root={"x": Weird()},
        )


def test_immutability():
    s = TemporalState(timeline_id="tl", logical_time=0, state_root={})
    try:
        s.timeline_id = "other"  # type: ignore[misc]
        raised = False
    except Exception:
        raised = True
    assert raised


def test_serialization_roundtrip():
    s = TemporalState(
        timeline_id="tl",
        logical_time=2,
        state_root={"k": True},
        parent_state="parent",
        causal_parents=("e1",),
        provenance=Provenance(source="t", operation="T"),
    )
    d = s.to_dict()
    s2 = TemporalState.from_dict(d)
    assert s2.state_id == s.state_id
    assert s2.to_dict() == d


def test_integrity_record():
    s = TemporalState(timeline_id="tl", logical_time=1, state_root={})
    rec = s.integrity_record()
    assert rec["state_id"] == s.state_id
    assert "wall_clock" not in rec
