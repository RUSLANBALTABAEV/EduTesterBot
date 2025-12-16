"""Инициализация обработчиков бота."""
from .start import start_router
from .auth import auth_router
from .registration import registration_router
from .tests import tests_router  # НОВОЕ: заменяет courses
from .my_tests import my_tests_router  # НОВОЕ: заменяет my_courses
from .testing import testing_router
from .admin import admin_router
from .admin_testing import admin_testing_router
from .test_results import results_router  # НОВОЕ

__all__ = [
    'start_router',
    'auth_router',
    'registration_router',
    'tests_router',  # ИЗМЕНЕНО
    'my_tests_router',  # ИЗМЕНЕНО
    'testing_router',
    'admin_router',
    'admin_testing_router',
    'results_router',  # НОВОЕ
]
