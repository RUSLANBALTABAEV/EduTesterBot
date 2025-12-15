# fsm/registration.py
"""
FSM состояния для регистрации пользователя.
"""
from aiogram.fsm.state import StatesGroup, State


class Registration(StatesGroup):
    """Состояния для процесса регистрации."""
    name = State()
    age = State()
    phone = State()
    photo = State()
    document = State()
