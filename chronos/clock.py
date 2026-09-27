"""
Logical clock for ChronOS.

Authoritative time is logical and deterministic.
Wall-clock timestamps may exist only as optional metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LogicalClock:
    """
    Monotonic, deterministic logical clock.

    - Independent of system wall clock
    - Explicit advancement via tick()
    - observe() advances to at least the given value (Lamport-style)
    - Serializable via to_dict / from_dict
    """

    _time: int = field(default=0, repr=False)
    _origin: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        if self._time < 0 or self._origin < 0:
            raise ValueError("Logical time must be non-negative")
        if self._time < self._origin:
            raise ValueError("Current time cannot be less than origin")

    def now(self) -> int:
        """Return the current logical time without advancing."""
        return self._time

    def tick(self, amount: int = 1) -> int:
        """
        Advance the clock by `amount` (default 1) and return the new time.

        Raises ValueError if amount < 1.
        """
        if amount < 1:
            raise ValueError("tick amount must be >= 1")
        self._time += amount
        return self._time

    def observe(self, value: int) -> int:
        """
        Observe an external logical time and advance this clock if needed.

        After observe(v), now() >= v. Returns the new current time.
        """
        if value < 0:
            raise ValueError("Observed logical time must be non-negative")
        if value > self._time:
            self._time = value
        return self._time

    def to_dict(self) -> dict:
        """Serialize clock state."""
        return {
            "time": self._time,
            "origin": self._origin,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LogicalClock":
        """Deserialize clock state."""
        return cls(_time=int(data["time"]), _origin=int(data.get("origin", 0)))

    def __repr__(self) -> str:
        return f"LogicalClock(time={self._time})"
