"""SELF-STATE-KERNEL ADAPTER unit tests (protocol double)."""

from typing import Any, Dict

import pytest

from chronos import Timeline, TemporalOp
from chronos.adapters.self_state import SelfStateAdapter, KernelProtocol


class FakeKernelState:
    def __init__(self) -> None:
        self.values: Dict[str, Any] = {"counter": 0}

    def get(self, path: str, default: Any = None) -> Any:
        return self.values.get(path, default)

    def set(self, path: str, value: Any) -> None:
        self.values[path] = value

    def snapshot(self) -> Dict[str, Any]:
        return dict(self.values)


class FakeKernel:
    """Protocol-compatible test double — not the real kernel."""

    def __init__(self) -> None:
        self.state = FakeKernelState()
        self._integrity_n = 0

    def GET(self, path: str, default: Any = None) -> Any:
        return self.state.get(path, default)

    def SET(self, path: str, value: Any) -> Any:
        self.state.set(path, value)
        self._integrity_n += 1
        return value

    def integrity(self) -> str:
        import hashlib, json

        return hashlib.sha256(
            json.dumps(self.state.values, sort_keys=True).encode()
        ).hexdigest()


def test_protocol_satisfied():
    k = FakeKernel()
    assert isinstance(k, KernelProtocol)


def test_observe_and_transition():
    tl = Timeline.create_root({})
    adapter = SelfStateAdapter(tl)
    k = FakeKernel()

    observed = adapter.capture_state(k)
    assert observed.state_root["counter"] == 0

    event, state = adapter.apply_event(k, "SET", path="counter", value=5)
    assert event.event_type == TemporalOp.TRANSITION.value
    assert state.state_root["counter"] == 5
    assert k.GET("counter") == 5


def test_restore():
    tl = Timeline.create_root({})
    adapter = SelfStateAdapter(tl)
    k = FakeKernel()
    adapter.apply_event(k, "SET", path="counter", value=10)
    captured = adapter.capture_state(k)

    k.SET("counter", 999)
    adapter.restore_state(k, captured)
    assert k.GET("counter") == 10


def test_integrity_and_trace():
    tl = Timeline.create_root({})
    adapter = SelfStateAdapter(tl)
    k = FakeKernel()
    adapter.apply_event(k, "SET", path="counter", value=1)
    integ = adapter.integrity(k)
    assert "chronos" in integ
    assert "kernel_integrity" in integ
    assert len(adapter.trace()) >= 1


def test_kernel_failure_propagation():
    class BrokenKernel(FakeKernel):
        def SET(self, path: str, value: Any) -> Any:
            raise RuntimeError("domain failure")

    tl = Timeline.create_root({})
    adapter = SelfStateAdapter(tl)
    k = BrokenKernel()
    with pytest.raises(RuntimeError, match="domain failure"):
        adapter.apply_event(k, "SET", path="x", value=1)
