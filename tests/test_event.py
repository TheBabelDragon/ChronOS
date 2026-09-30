"""EVENT tests."""

from chronos import TemporalEvent, Provenance


def test_deterministic_identity():
    e1 = TemporalEvent(
        event_type="TRANSITION",
        logical_time=1,
        source="test",
        payload={"x": 1},
    )
    e2 = TemporalEvent(
        event_type="TRANSITION",
        logical_time=1,
        source="test",
        payload={"x": 1},
    )
    assert e1.event_id == e2.event_id
    assert e1.payload_hash == e2.payload_hash


def test_payload_hashing_differs():
    e1 = TemporalEvent(event_type="T", logical_time=0, source="s", payload={"a": 1})
    e2 = TemporalEvent(event_type="T", logical_time=0, source="s", payload={"a": 2})
    assert e1.payload_hash != e2.payload_hash
    assert e1.event_id != e2.event_id


def test_immutable_fields():
    e = TemporalEvent(event_type="T", logical_time=0, source="s")
    try:
        e.event_type = "X"  # type: ignore[misc]
        raised = False
    except Exception:
        raised = True
    assert raised


def test_serialization_roundtrip():
    e = TemporalEvent(
        event_type="TRANSITION",
        logical_time=3,
        source="adapter",
        input_state_id="abc",
        result_state_id="def",
        causal_parents=("p1",),
        payload={"op": "SET", "path": "x", "value": 1},
        provenance=Provenance(source="test", operation="SET"),
    )
    d = e.to_dict()
    e2 = TemporalEvent.from_dict(d)
    assert e2.event_id == e.event_id
    assert e2.to_dict() == d


def test_identity_method():
    e = TemporalEvent(event_type="T", logical_time=0, source="s")
    assert e.identity() == e.event_id
