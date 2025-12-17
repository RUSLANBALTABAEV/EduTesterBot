"""Adapter: expose `my_tests_router` from `test_results` module (my_courses removed)."""
from .test_results import results_router as my_tests_router

__all__ = ['my_tests_router']
