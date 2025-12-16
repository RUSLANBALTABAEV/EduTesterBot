# handlers/tests.py
"""Обёртка: `tests` — совместимость с переименованием `courses`."""
from .courses import courses_router as tests_router

__all__ = ['tests_router']
