# handlers/init.py
"""
Инициализация обработчиков бота.
"""
from .start import start_router
from .auth import auth_router
from .registration import registration_router
from .courses import courses_router
from .my_courses import my_courses_router
from .testing import testing_router
from .admin import admin_router
from .admin_testing import admin_testing_router

__all__ = [
    'start_router',
    'auth_router',
    'registration_router',
    'courses_router',
    'my_courses_router',
    'testing_router',
    'admin_router',
    'admin_testing_router',
]
