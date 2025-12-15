# handlers/admin_testing.py
"""
Обработчики для администрирования тестирования.
"""
import io
import json
from datetime import datetime
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import pandas as pd
from sqlalchemy import select, and_

from db.models import Course, Test, Question, Option, TestResult, User
from db.session import async_session
from fsm.test import AdminTestCreation, AdminQuestionCreation
from config.bot_config import ADMIN_ID
from i18n.locales import get_text

admin_testing_router = Router()


async def get_user_language(user_id: int) -> str:
    """Получить язык пользователя."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user.language if user and user.language else "ru"


@admin_testing_router.callback_query(F.data == "manage_tests")
async def manage_tests(callback: types.CallbackQuery):
    """
    Управление тестами.
    
    Args:
        callback: Callback query
    """
    if callback.from_user.id != ADMIN_ID:
        lang = await get_user_language(callback.from_user.id)
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return
    
    lang = await get_user_language(callback.from_user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать тест", callback_data="create_test")],
        [InlineKeyboardButton(text="📝 Добавить вопросы", callback_data="add_questions")],
        [InlineKeyboardButton(text="📊 Результаты тестов", callback_data="test_results")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])
    
    await callback.message.edit_text(
        "📋 Управление тестированием:",
        reply_markup=keyboard
    )
    await callback.answer()


@admin_testing_router.callback_query(F.data == "create_test")
async def create_test_start(callback: types.CallbackQuery, state: FSMContext):
    """
    Начать создание теста.
    
    Args:
        callback: Callback query
        state: FSM контекст
    """
    if callback.from_user.id != ADMIN_ID:
        return
    
    async with async_session() as session:
        result = await session.execute(select(Course))
        courses = result.scalars().all()
    
    if not courses:
        await callback.answer("Нет доступных курсов", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=course.title, callback_data=f"select_course_{course.id}")]
        for course in courses
    ] + [[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]])
    
    await callback.message.edit_text(
        "Выберите курс для теста:",
        reply_markup=keyboard
    )
    await state.set_state(AdminTestCreation.select_course)
    await callback.answer()


@admin_testing_router.callback_query(
    F.data.startswith("select_course_"),
    AdminTestCreation.select_course
)
async def select_course_for_test(callback: types.CallbackQuery, state: FSMContext):
    """
    Выбрать курс для теста.
    
    Args:
        callback: Callback query
        state: FSM контекст
    """
    course_id = int(callback.data.split("_")[2])
    await state.update_data(course_id=course_id)
    await state.set_state(AdminTestCreation.title)
    
    await callback.message.edit_text("Введите название теста:")
    await callback.answer()


@admin_testing_router.message(AdminTestCreation.title)
async def set_test_title(message: types.Message, state: FSMContext):
    """
    Установить название теста.
    
    Args:
        message: Сообщение
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminTestCreation.description)
    await message.answer("Введите описание теста (или отправьте '-' для пропуска):")


@admin_testing_router.message(AdminTestCreation.description)
async def set_test_description(message: types.Message, state: FSMContext):
    """
    Установить описание теста.
    
    Args:
        message: Сообщение
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return
    
    description = message.text.strip() if message.text.strip() != "-" else None
    await state.update_data(description=description)
    await state.set_state(AdminTestCreation.total_questions)
    await message.answer("Введите количество вопросов (по умолчанию 50):")


@admin_testing_router.message(AdminTestCreation.total_questions)
async def set_total_questions(message: types.Message, state: FSMContext):
    """
    Установить количество вопросов.
    
    Args:
        message: Сообщение
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        total_questions = int(message.text.strip()) if message.text.strip() else 50
    except ValueError:
        total_questions = 50
    
    await state.update_data(total_questions=total_questions)
    await state.set_state(AdminTestCreation.time_limit)
    await message.answer("Введите лимит времени в минутах (0 - без ограничения):")


@admin_testing_router.message(AdminTestCreation.time_limit)
async def set_time_limit(message: types.Message, state: FSMContext):
    """
    Установить лимит времени.
    
    Args:
        message: Сообщение
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        time_limit = int(message.text.strip()) if message.text.strip() else 0
    except ValueError:
        time_limit = 0
    
    await state.update_data(time_limit=time_limit)
    await state.set_state(AdminTestCreation.scheduled_time)
    await message.answer("Введите дату и время начала теста (ДД.ММ.ГГГГ ЧЧ:ММ или '-' для немедленного):")


@admin_testing_router.message(AdminTestCreation.scheduled_time)
async def set_scheduled_time(message: types.Message, state: FSMContext):
    """
    Установить время начала теста.
    
    Args:
        message: Сообщение
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.strip()
    scheduled_time = None
    
    if text != "-":
        try:
            scheduled_time = datetime.strptime(text, "%d.%m.%Y %H:%M")
        except ValueError:
            await message.answer("Неверный формат. Используйте ДД.ММ.ГГГГ ЧЧ:ММ или '-'")
            return
    
    await state.update_data(scheduled_time=scheduled_time)
    
    # Показываем подтверждение
    data = await state.get_data()
    
    text = (
        f"📋 Подтверждение создания теста:\n\n"
        f"• Курс ID: {data['course_id']}\n"
        f"• Название: {data['title']}\n"
        f"• Описание: {data['description'] or 'нет'}\n"
        f"• Вопросов: {data['total_questions']}\n"
        f"• Лимит времени: {data['time_limit']} мин\n"
        f"• Время начала: {data['scheduled_time'] or 'немедленно'}\n\n"
        f"Создать тест?"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="confirm_test")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="cancel_test")]
    ])
    
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(AdminTestCreation.confirm)


@admin_testing_router.callback_query(F.data == "confirm_test", AdminTestCreation.confirm)
async def confirm_test_creation(callback: types.CallbackQuery, state: FSMContext):
    """
    Подтвердить создание теста.
    
    Args:
        callback: Callback query
        state: FSM контекст
    """
    if callback.from_user.id != ADMIN_ID:
        return
    
    data = await state.get_data()
    
    async with async_session() as session:
        test = Test(
            course_id=data['course_id'],
            title=data['title'],
            description=data['description'],
            total_questions=data['total_questions'],
            max_score=100,
            time_limit=data['time_limit'] or None,
            scheduled_time=data['scheduled_time'],
            is_active=True
        )
        session.add(test)
        await session.commit()
    
    await callback.message.edit_text(f"✅ Тест '{data['title']}' создан!")
    await state.clear()
    await callback.answer()


@admin_testing_router.callback_query(F.data == "test_results")
async def show_test_results(callback: types.CallbackQuery):
    """
    Показать результаты тестов.
    
    Args:
        callback: Callback query
    """
    if callback.from_user.id != ADMIN_ID:
        lang = await get_user_language(callback.from_user.id)
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return
    
    async with async_session() as session:
        # Получаем все тесты
        tests_result = await session.execute(select(Test))
        tests = tests_result.scalars().all()
    
    if not tests:
        await callback.answer("Нет тестов", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{test.title}", callback_data=f"test_stats_{test.id}")]
        for test in tests
    ] + [[InlineKeyboardButton(text="🔙 Назад", callback_data="manage_tests")]])
    
    await callback.message.edit_text(
        "Выберите тест для просмотра результатов:",
        reply_markup=keyboard
    )
    await callback.answer()


@admin_testing_router.callback_query(F.data.startswith("test_stats_"))
async def show_test_statistics(callback: types.CallbackQuery):
    """
    Показать статистику теста.
    
    Args:
        callback: Callback query
    """
    test_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Получаем результаты теста
        results_result = await session.execute(
            select(TestResult).where(TestResult.test_id == test_id)
        )
        results = results_result.scalars().all()
        
        # Получаем информацию о тесте
        test_result = await session.execute(
            select(Test).where(Test.id == test_id)
        )
        test = test_result.scalar_one_or_none()
        
        if not results:
            await callback.answer("Нет результатов для этого теста", show_alert=True)
            return
        
        # Статистика
        completed = [r for r in results if r.completed_at]
        avg_score = sum(r.score for r in completed) / len(completed) if completed else 0
        
        text = (
            f"📊 Статистика теста: {test.title}\n\n"
            f"• Всего попыток: {len(results)}\n"
            f"• Завершено: {len(completed)}\n"
            f"• Средний балл: {avg_score:.1f}\n\n"
            f"Действия:"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 Выгрузить в Excel", callback_data=f"export_test_{test_id}")],
            [InlineKeyboardButton(text="👥 Список результатов", callback_data=f"list_results_{test_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="test_results")]
        ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@admin_testing_router.callback_query(F.data.startswith("export_test_"))
async def export_test_results(callback: types.CallbackQuery):
    """
    Экспортировать результаты теста в Excel.
    
    Args:
        callback: Callback query
    """
    test_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Получаем результаты с информацией о пользователях
        query = select(
            TestResult,
            User.name,
            User.phone
        ).join(
            User, TestResult.user_id == User.id
        ).where(
            TestResult.test_id == test_id
        )
        
        results = await session.execute(query)
        rows = results.all()
        
        if not rows:
            await callback.answer("Нет данных для экспорта", show_alert=True)
            return
        
        # Создаем DataFrame
        data = []
        for result, name, phone in rows:
            data.append({
                'ID': result.id,
                'ФИО': name,
                'Телефон': phone,
                'Баллы': result.score,
                'Макс. балл': result.max_score,
                'Процент': (result.score / result.max_score * 100) if result.max_score > 0 else 0,
                'Начало': result.started_at.strftime("%d.%m.%Y %H:%M") if result.started_at else '',
                'Завершение': result.completed_at.strftime("%d.%m.%Y %H:%M") if result.completed_at else '',
                'Статус': 'Завершено' if result.completed_at else 'В процессе'
            })
        
        df = pd.DataFrame(data)
        
        # Создаем Excel файл в памяти
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Результаты', index=False)
        
        output.seek(0)
        
        # Отправляем файл
        await callback.message.bot.send_document(
            chat_id=callback.from_user.id,
            document=types.BufferedInputFile(
                file=output.read(),
                filename=f"results_test_{test_id}.xlsx"
            ),
            caption=f"Результаты теста ID: {test_id}"
        )
    
    await callback.answer()
