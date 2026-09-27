"""
Provenance for ChronOS events and states.

Provenance is never silently discarded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class Provenance:
    """
    Extensible provenance record.

    Minimum fields:
    - source
    - operation
    - actor
    - input_refs
    - context (hardware/software)
    - parent_events
    """

    source: str = ""
    operation: str = ""
    actor: str = ""
    input_refs: Tuple[str, ...] = field(default_factory=tuple)
    context: Dict[str, Any] = field(default_factory=dict)
    parent_events: Tuple[str, ...] = field(default_factory=tuple)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "operation": self.operation,
            "actor": self.actor,
            "input_refs": list(self.input_refs),
            "context": dict(self.context),
            "parent_events": list(self.parent_events),
            "extra": dict(self.extra),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Provenance":
        if not data:
            return cls()
        return cls(
            source=data.get("source", ""),
            operation=data.get("operation", ""),
            actor=data.get("actor", ""),
            input_refs=tuple(data.get("input_refs") or ()),
            context=dict(data.get("context") or {}),
            parent_events=tuple(data.get("parent_events") or ()),
            extra=dict(data.get("extra") or {}),
        )
