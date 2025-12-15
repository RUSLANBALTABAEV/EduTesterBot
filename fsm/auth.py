# fsm/auth.py
"""
FSM состояния для авторизации пользователя.
"""
from aiogram.fsm.state import StatesGroup, State


class Auth(StatesGroup):
    """Состояния для процесса авторизации."""
    phone = State()
