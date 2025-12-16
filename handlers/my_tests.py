# handlers/my_tests.py
"""Обёртка: `my_tests` — совместимость с переименованием `my_courses`."""
from .my_courses import my_courses_router as my_tests_router

__all__ = ['my_tests_router']
