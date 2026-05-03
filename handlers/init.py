# handlers/__init__.py
"""
Инициализация обработчиков бота.
"""
from .start import start_router
from .auth import auth_router
from .registration import registration_router
from .tests import tests_router
from .my_tests import my_tests_router  
from .testing import testing_router
from .admin import admin_router
from .admin_testing import admin_testing_router
from .test_results import results_router 

__all__ = [
    'start_router',
    'auth_router',
    'registration_router',
    'tests_router',  
    'my_tests_router',
    'testing_router',
    'admin_router',
    'admin_testing_router',
    'results_router',
]
