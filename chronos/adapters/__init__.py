"""Thin adapters from ChronOS to external execution kernels."""

from .self_state import KernelProtocol, SelfStateAdapter

__all__ = ["KernelProtocol", "SelfStateAdapter"]
