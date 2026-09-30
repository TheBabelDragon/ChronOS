"""
Self-state-kernel adapter.

Depends only on the minimal public kernel contract discovered in the
live self-state-kernel repository:

    Kernel.GET(path, default=None)
    Kernel.SET(path, value)
    Kernel.integrity() -> str
    Kernel.state.snapshot() -> dict
    Kernel.trace_export() -> list   (optional)

ChronOS does not import private kernel modules and does not own
SELF command semantics, strict boolean policy, module dispatch,
CMD4, or domain-specific state meaning.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ..abi import TemporalOp, map_kernel_op
from ..event import TemporalEvent
from ..provenance import Provenance
from ..snapshot import Snapshot, create_snapshot, restore_snapshot
from ..state import TemporalState, canonicalize
from ..timeline import Timeline


@runtime_checkable
class KernelProtocol(Protocol):
    """
    Minimal public boundary of self-state-kernel used by ChronOS.

    Aligned with the live Kernel surface:
      - GET / SET for path-addressed domain state
      - integrity() for domain integrity hash
      - state.snapshot() for full domain capture
    """

    def GET(self, path: str, default: Any = None) -> Any: ...

    def SET(self, path: str, value: Any) -> Any: ...

    def integrity(self) -> str: ...

    @property
    def state(self) -> Any: ...


def _domain_snapshot(kernel: KernelProtocol) -> Dict[str, Any]:
    """Capture full domain state via the public snapshot surface."""
    st = getattr(kernel, "state", None)
    if st is not None and hasattr(st, "snapshot"):
        snap = st.snapshot()
        if isinstance(snap, dict):
            return canonicalize(snap)
    # Fallback: integrity-only observation
    return {"_integrity": kernel.integrity()}


def _restore_domain(kernel: KernelProtocol, domain: Dict[str, Any]) -> None:
    """
    Restore domain state through public SET paths.

    Replaces the entire values dict when KernelState.values is available;
    otherwise walks SET for each top-level key. Does not call private APIs.
    """
    st = getattr(kernel, "state", None)
    if st is not None and hasattr(st, "values") and isinstance(st.values, dict):
        # Public attribute on KernelState; replace contents in place.
        st.values.clear()
        st.values.update(canonicalize(domain))
        return
    # Path-wise SET fallback
    for key, value in domain.items():
        kernel.SET(str(key), value)


class SelfStateAdapter:
    """
    Thin Temporal ABI adapter for self-state-kernel.

    ChronOS owns time/history/causality.
    The kernel owns domain state and execution.
    """

    def __init__(
        self,
        timeline: Timeline,
        *,
        source: str = "self-state-kernel",
    ) -> None:
        self.timeline = timeline
        self.source = source

    # ---- OBSERVE --------------------------------------------------------

    def capture_state(
        self,
        kernel: KernelProtocol,
        *,
        event_type: str = TemporalOp.OBSERVE.value,
    ) -> TemporalState:
        """
        OBSERVE: read current domain state and commit a temporal state
        observation (does not change domain state).
        """
        domain = _domain_snapshot(kernel)
        prov = Provenance(
            source=self.source,
            operation=TemporalOp.OBSERVE.value,
            context={"kernel_integrity": kernel.integrity()},
        )
        # Observation is a transition of temporal history, not domain mutation.
        _event, state = self.timeline.transition(
            new_state_root=domain,
            event_type=event_type,
            source=self.source,
            payload={
                "op": TemporalOp.OBSERVE.value,
                "kernel_integrity": kernel.integrity(),
            },
            provenance=prov,
        )
        return state

    # ---- TRANSITION -----------------------------------------------------

    def apply_event(
        self,
        kernel: KernelProtocol,
        op: str,
        payload: Any = None,
        *,
        path: Optional[str] = None,
        value: Any = None,
    ) -> tuple[TemporalEvent, TemporalState]:
        """
        TRANSITION: apply a domain operation via the kernel, then record
        the resulting domain state as an immutable temporal transition.

        Supported op forms: SET, RUN, SELF.SET, SELF.RUN, or any string
        mappable via the Temporal ABI.
        """
        abi_op = map_kernel_op(op)
        if abi_op not in (TemporalOp.TRANSITION, TemporalOp.OBSERVE):
            pass

        op_upper = op.upper()
        if op_upper in ("SET", "SELF.SET") or (
            path is not None and value is not None
        ):
            if path is None:
                raise ValueError("SET requires path")
            kernel.SET(path, value if value is not None else payload)
            domain_payload = {"op": "SET", "path": path, "value": value if value is not None else payload}
        elif op_upper in ("RUN", "SELF.RUN"):
            run = getattr(kernel, "RUN", None)
            if run is None:
                raise AttributeError("Kernel does not expose RUN")
            result = run(payload)
            domain_payload = {"op": "RUN", "command": payload, "result": _safe(result)}
        elif op_upper in ("GET", "SELF.GET", "QUERY", "SELF.QUERY"):
            got = kernel.GET(path or "", payload)
            domain_payload = {"op": op_upper, "path": path, "result": _safe(got)}
        else:
            domain_payload = {"op": op, "payload": payload}

        domain = _domain_snapshot(kernel)
        prov = Provenance(
            source=self.source,
            operation=abi_op.value,
            context={"kernel_op": op, "kernel_integrity": kernel.integrity()},
        )
        return self.timeline.transition(
            new_state_root=domain,
            event_type=abi_op.value,
            source=self.source,
            payload=domain_payload,
            provenance=prov,
        )

    # ---- RESTORE --------------------------------------------------------

    def restore_state(
        self,
        kernel: KernelProtocol,
        state: TemporalState,
    ) -> None:
        """
        RESTORE: push a temporal state's domain root back into the kernel
        through the public state boundary. Does not mutate the temporal state.
        """
        if not isinstance(state.state_root, dict):
            raise TypeError(
                "restore_state expects state_root to be a dict domain snapshot"
            )
        _restore_domain(kernel, state.state_root)

    def restore_snapshot(
        self,
        kernel: KernelProtocol,
        snapshot: Snapshot,
    ) -> TemporalState:
        """Restore domain from a ChronOS snapshot via the store."""
        st = restore_snapshot(snapshot, self.timeline.store)
        self.restore_state(kernel, st)
        return st

    # ---- INTEGRITY / TRACE ----------------------------------------------

    def state_identity(self, kernel: KernelProtocol) -> str:
        """ChronOS identity of a fresh observation of the current domain."""
        domain = _domain_snapshot(kernel)
        temp = TemporalState(
            timeline_id=self.timeline.timeline_id,
            logical_time=self.timeline.clock.now(),
            state_root=domain,
            parent_state=self.timeline.head_state_id,
            provenance=Provenance(
                source=self.source,
                operation=TemporalOp.INTEGRITY.value,
            ),
        )
        return temp.state_id

    def integrity(self, kernel: KernelProtocol) -> dict:
        """Combined ChronOS + kernel integrity record."""
        head = self.timeline.head()
        return {
            "chronos": head.integrity_record(),
            "kernel_integrity": kernel.integrity(),
            "timeline": self.timeline.integrity(),
        }

    def trace(self, state_id: Optional[str] = None) -> List[dict]:
        """Temporal/causal history for a state (default: head)."""
        return self.timeline.trace(state_id)

    def kernel_trace(self, kernel: KernelProtocol) -> Any:
        """Optional kernel-side trace if exposed."""
        export = getattr(kernel, "trace_export", None)
        if callable(export):
            return export()
        return None

    def snapshot_head(self) -> Snapshot:
        return create_snapshot(self.timeline.head())


def _safe(value: Any) -> Any:
    """Best-effort JSON-safe view of a kernel result."""
    try:
        return canonicalize(value)
    except TypeError:
        return repr(value)
