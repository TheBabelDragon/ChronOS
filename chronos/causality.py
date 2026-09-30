"""
Explicit causal graph.

Temporal order is not causal order. Edges come only from
TemporalEvent.causal_parents (and TemporalState.causal_parents).
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .event import TemporalEvent
from .store import TemporalStore


class CausalGraph:
    """
    Directed causal graph over event IDs.

    Edges: parent → child (parent causes child).
    """

    def __init__(self) -> None:
        self._children: Dict[str, Set[str]] = defaultdict(set)
        self._parents: Dict[str, Set[str]] = defaultdict(set)
        self._nodes: Set[str] = set()

    def add_edge(self, parent: str, child: str) -> None:
        if not parent or not child:
            raise ValueError("Causal edge endpoints must be non-empty")
        self._nodes.add(parent)
        self._nodes.add(child)
        self._children[parent].add(child)
        self._parents[child].add(parent)

    def add_event(self, event: TemporalEvent) -> None:
        """Register an event and its explicit causal parents."""
        self._nodes.add(event.event_id)
        for p in event.causal_parents:
            self.add_edge(p, event.event_id)

    @classmethod
    def from_store(cls, store: TemporalStore) -> "CausalGraph":
        g = cls()
        for event in store.events():
            g.add_event(event)
        return g

    @classmethod
    def from_events(cls, events: Iterable[TemporalEvent]) -> "CausalGraph":
        g = cls()
        for event in events:
            g.add_event(event)
        return g

    def parents(self, node: str) -> List[str]:
        return sorted(self._parents.get(node, ()))

    def children(self, node: str) -> List[str]:
        return sorted(self._children.get(node, ()))

    def ancestors(self, node: str) -> List[str]:
        """All transitive causal ancestors (roots first, topological)."""
        if node not in self._nodes and node not in self._parents:
            return []
        result: List[str] = []
        seen: Set[str] = set()
        stack = list(self._parents.get(node, ()))
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            result.append(n)
            stack.extend(self._parents.get(n, ()))
        result.reverse()
        ordered: List[str] = []
        seen2: Set[str] = set()
        for n in result:
            if n not in seen2:
                seen2.add(n)
                ordered.append(n)
        return ordered

    def descendants(self, node: str) -> List[str]:
        """All transitive causal descendants (BFS order)."""
        result: List[str] = []
        seen: Set[str] = set()
        q: deque[str] = deque(self._children.get(node, ()))
        while q:
            n = q.popleft()
            if n in seen:
                continue
            seen.add(n)
            result.append(n)
            q.extend(self._children.get(n, ()))
        return result

    def lineage(self, node: str) -> List[str]:
        """Ancestor chain including the node itself (roots first)."""
        return self.ancestors(node) + [node]

    def why(self, node: str) -> List[str]:
        """Alias for lineage — full causal ancestor chain including node."""
        return self.lineage(node)

    def causal_path(self, src: str, dst: str) -> Optional[List[str]]:
        """Shortest causal path from src to dst, or None."""
        if src == dst:
            return [src]
        q: deque[Tuple[str, List[str]]] = deque([(src, [src])])
        seen: Set[str] = {src}
        while q:
            node, path = q.popleft()
            for child in self._children.get(node, ()):
                if child in seen:
                    continue
                new_path = path + [child]
                if child == dst:
                    return new_path
                seen.add(child)
                q.append((child, new_path))
        return None

    def nodes(self) -> List[str]:
        return sorted(self._nodes)
