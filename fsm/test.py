# fsm/test.py
"""
FSM состояния для тестирования.
"""
from aiogram.fsm.state import StatesGroup, State


class Testing(StatesGroup):
    """Состояния для процесса тестирования."""
    waiting_for_answer = State()
    completed = State()


class AdminTestCreation(StatesGroup):
    """Состояния для создания теста администратором."""
    select_course = State()
    title = State()
    description = State()
    total_questions = State()
    time_limit = State()
    scheduled_time = State()
    upload_file = State()
    confirm = State()


class AdminQuestionCreation(StatesGroup):
    """Состояния для создания вопросов администратором."""
    select_test = State()
    question_text = State()
    question_type = State()
    points = State()
    options = State()
    correct_option = State()
    add_more = State()


class AdminTestEdit(StatesGroup):
    """Состояния для редактирования теста администратором."""
    title = State()
    description = State()
