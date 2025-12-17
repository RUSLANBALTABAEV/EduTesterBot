"""Adapter: expose `tests_router` from `testing` module (courses removed)."""
from .testing import testing_router as tests_router

__all__ = ['tests_router']
