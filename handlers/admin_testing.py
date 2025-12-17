# handlers/admin_testing.py
"""
Обработчики для администрирования тестирования.
"""
import io
import json
from datetime import datetime
from aiogram import Router, F, types
import logging
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
import pandas as pd
from sqlalchemy import select

from db.models import Test, Question, Option, TestResult, User
from db.session import async_session
from fsm.test import AdminTestCreation, AdminQuestionCreation, AdminTestEdit
from config.bot_config import ADMIN_ID
from i18n.locales import get_text
from keyboards.reply import main_menu

admin_testing_router = Router()

logger = logging.getLogger(__name__)


async def safe_edit(message: types.Message | None, text: str, **kwargs):
    """Try to edit message text; ignore 'message is not modified' errors."""
    if message is None:
        return
    try:
        await message.edit_text(text, **kwargs)
    except TelegramBadRequest as e:
        msg = str(e)
        if 'message is not modified' in msg:
            logger.debug('Edit skipped (not modified) for message id %s', getattr(message, 'message_id', None))
            return
        logger.exception('TelegramBadRequest on edit_text: %s', e)


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
        [InlineKeyboardButton(text=get_text("btn_create_test", lang), callback_data="create_test")],
        [InlineKeyboardButton(text="📋 Список тестов", callback_data="list_all_tests")],
        [InlineKeyboardButton(text=get_text("btn_upload_excel", lang) if "btn_upload_excel" in [] else "📤 Загрузить тест из Excel", callback_data="upload_excel_test")],
        [InlineKeyboardButton(text=get_text("btn_download_template", lang) if "btn_download_template" in [] else "📥 Скачать шаблон Excel", callback_data="download_excel_template")],
        [InlineKeyboardButton(text=get_text("btn_add_questions", lang), callback_data="add_questions")],
        [InlineKeyboardButton(text=get_text("btn_test_results", lang), callback_data="test_results")],
        [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin_menu")]
    ])

    await safe_edit(callback.message, get_text("manage_testing_title", lang), reply_markup=keyboard)
    await callback.answer()


@admin_testing_router.callback_query(F.data == "add_questions")
async def add_questions_start(callback: types.CallbackQuery):
    """Начать добавление вопросов: показать список тестов."""
    lang = await get_user_language(callback.from_user.id)

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(Test))
        tests = result.scalars().all()

    if not tests:
        await callback.answer(get_text("no_tests", lang), show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=test.title, callback_data=f"add_to_test_{test.id}")]
        for test in tests
    ] + [[InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="manage_tests")]])

    await safe_edit(callback.message, get_text("choose_test_for_results", lang), reply_markup=keyboard)
    await callback.answer()


@admin_testing_router.callback_query(F.data.startswith("add_to_test_"))
async def add_to_test_select(callback: types.CallbackQuery, state: FSMContext):
    """Выбран тест — запросить текст вопроса."""
    lang = await get_user_language(callback.from_user.id)

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    parts = callback.data.split("_")
    test_id = int(parts[-1])
    await state.update_data(test_id=test_id)
    await state.set_state(AdminQuestionCreation.question_text)

    await safe_edit(callback.message, get_text("enter_question_text", lang) if "enter_question_text" in [] else "Отправьте текст вопроса:")
    await callback.answer()


@admin_testing_router.message(AdminQuestionCreation.question_text)
async def admin_question_text(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(question_text=message.text.strip())
    # Спрашиваем тип вопроса
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ Один правильный ответ", callback_data="qtype_single")],
        [InlineKeyboardButton(text="📝 Несколько правильных ответов", callback_data="qtype_multiple")],
        [InlineKeyboardButton(text="✍️ Текстовый ответ", callback_data="qtype_text")]
    ])
    await state.set_state(AdminQuestionCreation.question_type)
    await message.answer("Выберите тип вопроса:", reply_markup=keyboard)


@admin_testing_router.callback_query(F.data.startswith("qtype_"), AdminQuestionCreation.question_type)
async def admin_question_type(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return

    qtype = callback.data.split("_")[1]
    await state.update_data(question_type=qtype)
    await state.set_state(AdminQuestionCreation.points)
    await safe_edit(callback.message, "Укажите количество баллов за вопрос (например, 1):")
    await callback.answer()


@admin_testing_router.message(AdminQuestionCreation.points)
async def admin_question_points(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        pts = float(message.text.strip())
    except ValueError:
        pts = 1.0

    await state.update_data(points=pts)
    
    # Получаем тип вопроса
    data = await state.get_data()
    question_type = data.get('question_type', 'single')
    
    if question_type == 'text':
        # Для текстового вопроса сразу переходим к сохранению
        await save_question_without_options(message, state)
    else:
        # Начинаем пошаговый ввод вариантов
        await state.update_data(
            options_list=[],
            current_option_index=0
        )
        await state.set_state(AdminQuestionCreation.enter_option_text)
        await message.answer(
            "Начнём вводить варианты ответа.\n\n"
            "Введите текст первого варианта ответа:"
        )


@admin_testing_router.message(AdminQuestionCreation.enter_option_text)
async def admin_enter_option_text(message: types.Message, state: FSMContext):
    """Ввод текста варианта ответа."""
    if message.from_user.id != ADMIN_ID:
        return

    option_text = message.text.strip()
    
    # Сохраняем текущий вариант
    await state.update_data(current_option_text=option_text)
    
    # Спрашиваем, правильный ли этот вариант
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, правильный")],
            [KeyboardButton(text="❌ Нет, неправильный")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        f"Вариант: {option_text}\n\n"
        "Это правильный вариант ответа?",
        reply_markup=keyboard
    )
    await state.set_state(AdminQuestionCreation.mark_option_correct)


@admin_testing_router.message(AdminQuestionCreation.mark_option_correct)
async def admin_mark_option_correct(message: types.Message, state: FSMContext):
    """Отметка правильности варианта."""
    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()
    option_text = data.get('current_option_text')
    options_list = data.get('options_list', [])
    question_type = data.get('question_type', 'single')
    
    # Определяем, правильный ли вариант
    is_correct = message.text.startswith("✅")
    
    # Добавляем вариант в список
    options_list.append({
        'text': option_text,
        'is_correct': is_correct
    })
    
    # Проверяем ограничения для single-вопросов
    if question_type == 'single':
        correct_count = sum(1 for opt in options_list if opt['is_correct'])
        if correct_count > 1:
            await message.answer(
                "⚠️ Для вопроса с одним правильным ответом можно отметить только один вариант как правильный!\n"
                "Последний вариант будет помечен как неправильный.",
                reply_markup=ReplyKeyboardRemove()
            )
            # Помечаем все варианты как неправильные, кроме первого правильного
            first_correct_found = False
            for opt in options_list:
                if opt['is_correct'] and not first_correct_found:
                    first_correct_found = True
                else:
                    opt['is_correct'] = False
    
    await state.update_data(options_list=options_list)
    
    # Показываем текущий список вариантов
    options_text = "📋 Текущие варианты:\n\n"
    for i, opt in enumerate(options_list, 1):
        prefix = "✅ " if opt['is_correct'] else "❌ "
        options_text += f"{i}. {prefix}{opt['text']}\n"
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить ещё вариант")],
            [KeyboardButton(text="👁 Предпросмотр и редактирование")],
            [KeyboardButton(text="💾 Сохранить и продолжить")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        f"{options_text}\n"
        "Выберите действие:",
        reply_markup=keyboard
    )
    await state.set_state(AdminQuestionCreation.add_more_options)


@admin_testing_router.message(AdminQuestionCreation.add_more_options)
async def admin_add_more_options(message: types.Message, state: FSMContext):
    """Обработка выбора действия после добавления варианта."""
    if message.from_user.id != ADMIN_ID:
        return

    if message.text == "➕ Добавить ещё вариант":
        await state.set_state(AdminQuestionCreation.enter_option_text)
        await message.answer(
            "Введите текст следующего варианта ответа:",
            reply_markup=ReplyKeyboardRemove()
        )
    
    elif message.text == "👁 Предпросмотр и редактирование":
        await show_options_preview(message, state)
    
    elif message.text == "💾 Сохранить и продолжить":
        await save_question_with_options(message, state)


async def show_options_preview(message: types.Message, state: FSMContext):
    """Показать предпросмотр вариантов с возможностью редактирования."""
    data = await state.get_data()
    options_list = data.get('options_list', [])
    question_type = data.get('question_type', 'single')
    
    if not options_list:
        await message.answer("Варианты еще не добавлены.", reply_markup=ReplyKeyboardRemove())
        await state.set_state(AdminQuestionCreation.enter_option_text)
        await message.answer("Введите текст первого варианта:")
        return
    
    # Формируем текст с предпросмотром
    preview_text = "👁 **Предпросмотр вариантов:**\n\n"
    for i, opt in enumerate(options_list, 1):
        prefix = "✅ " if opt['is_correct'] else "❌ "
        preview_text += f"{i}. {prefix}{opt['text']}\n"
    
    preview_text += f"\nТип вопроса: {'❓ Один правильный ответ' if question_type == 'single' else '📝 Несколько правильных ответов'}"
    
    # Клавиатура для редактирования
    keyboard_buttons = []
    for i in range(1, len(options_list) + 1):
        keyboard_buttons.append(
            [InlineKeyboardButton(text=f"✏️ Редактировать вариант {i}", 
                                callback_data=f"edit_option_{i}")]
        )
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="➕ Добавить новый вариант", callback_data="add_new_option"),
        InlineKeyboardButton(text="🗑 Удалить все варианты", callback_data="delete_all_options")
    ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="👌 Сохранить как есть", callback_data="save_options_as_is"),
        InlineKeyboardButton(text="🔙 Назад к добавлению", callback_data="back_to_adding")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(preview_text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminQuestionCreation.preview_options)


@admin_testing_router.callback_query(F.data.startswith("edit_option_"), AdminQuestionCreation.preview_options)
async def edit_option(callback: types.CallbackQuery, state: FSMContext):
    """Редактировать конкретный вариант."""
    option_num = int(callback.data.split("_")[-1]) - 1  # 0-based index
    
    data = await state.get_data()
    options_list = data.get('options_list', [])
    
    if option_num < 0 or option_num >= len(options_list):
        await callback.answer("Неверный номер варианта", show_alert=True)
        return
    
    # Сохраняем индекс редактируемого варианта
    await state.update_data(editing_option_index=option_num)
    
    # Удаляем вариант из списка и переходим к его повторному вводу
    edited_option = options_list.pop(option_num)
    await state.update_data(options_list=options_list)
    
    # Устанавливаем текст варианта для редактирования
    await state.update_data(current_option_text=edited_option['text'])
    
    # Переходим к отметке правильности (как при обычном добавлении)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, правильный")],
            [KeyboardButton(text="❌ Нет, неправильный")]
        ],
        resize_keyboard=True
    )
    
    await callback.message.answer(
        f"Редактирование варианта {option_num + 1}:\n"
        f"Текущий текст: {edited_option['text']}\n\n"
        f"Введите новый текст варианта:",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Сначала запросим новый текст, затем правильность
    await state.set_state(AdminQuestionCreation.enter_option_text)
    await callback.answer()


@admin_testing_router.callback_query(F.data == "add_new_option", AdminQuestionCreation.preview_options)
async def add_new_option_from_preview(callback: types.CallbackQuery, state: FSMContext):
    """Добавить новый вариант из режима предпросмотра."""
    await state.set_state(AdminQuestionCreation.enter_option_text)
    await callback.message.answer(
        "Введите текст нового варианта ответа:",
        reply_markup=ReplyKeyboardRemove()
    )
    await callback.answer()


@admin_testing_router.callback_query(F.data == "delete_all_options", AdminQuestionCreation.preview_options)
async def delete_all_options(callback: types.CallbackQuery, state: FSMContext):
    """Удалить все варианты."""
    await state.update_data(options_list=[])
    await callback.message.answer(
        "Все варианты удалены. Начнем заново.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AdminQuestionCreation.enter_option_text)
    await callback.message.answer("Введите текст первого варианта ответа:")
    await callback.answer()


@admin_testing_router.callback_query(F.data == "save_options_as_is", AdminQuestionCreation.preview_options)
async def save_options_from_preview(callback: types.CallbackQuery, state: FSMContext):
    """Сохранить варианты из режима предпросмотра."""
    data = await state.get_data()
    options_list = data.get('options_list', [])
    
    if not options_list:
        await callback.answer("Добавьте хотя бы один вариант!", show_alert=True)
        return
    
    # Проверяем, есть ли правильные варианты
    has_correct = any(opt['is_correct'] for opt in options_list)
    if not has_correct:
        await callback.answer(
            "⚠️ Ни один вариант не отмечен как правильный!\n"
            "Хотя бы один вариант должен быть правильным.",
            show_alert=True
        )
        return
    
    await save_question_with_options(callback.message, state)
    await callback.answer()


@admin_testing_router.callback_query(F.data == "back_to_adding", AdminQuestionCreation.preview_options)
async def back_to_adding_from_preview(callback: types.CallbackQuery, state: FSMContext):
    """Вернуться к добавлению вариантов."""
    data = await state.get_data()
    options_list = data.get('options_list', [])
    
    options_text = "📋 Текущие варианты:\n\n"
    for i, opt in enumerate(options_list, 1):
        prefix = "✅ " if opt['is_correct'] else "❌ "
        options_text += f"{i}. {prefix}{opt['text']}\n"
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить ещё вариант")],
            [KeyboardButton(text="👁 Предпросмотр и редактирование")],
            [KeyboardButton(text="💾 Сохранить и продолжить")]
        ],
        resize_keyboard=True
    )
    
    await callback.message.answer(
        f"{options_text}\n"
        "Выберите действие:",
        reply_markup=keyboard
    )
    await state.set_state(AdminQuestionCreation.add_more_options)
    await callback.answer()


async def save_question_with_options(message: types.Message, state: FSMContext):
    """Сохранить вопрос с вариантами."""
    data = await state.get_data()
    test_id = data.get('test_id')
    q_text = data.get('question_text') or ''
    q_type = data.get('question_type') or 'single'
    points = data.get('points') or 1.0
    options_list = data.get('options_list', [])
    
    if not test_id:
        await message.answer("Ошибка: тест не выбран.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    
    if not options_list:
        await message.answer("Ошибка: варианты ответа не добавлены.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    
    # Проверяем, есть ли правильные варианты
    has_correct = any(opt['is_correct'] for opt in options_list)
    if not has_correct:
        await message.answer(
            "⚠️ Ни один вариант не отмечен как правильный!\n"
            "Добавьте хотя бы один правильный вариант.",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    try:
        async with async_session() as session:
            question = Question(
                test_id=test_id,
                text=q_text,
                question_type=q_type,
                points=points,
                order_num=0
            )
            session.add(question)
            await session.flush()

            for opt in options_list:
                option = Option(
                    question_id=question.id,
                    text=opt['text'],
                    is_correct=opt['is_correct']
                )
                session.add(option)

            await session.commit()

        # Показываем итоговую информацию
        result_text = f"✅ Вопрос сохранён!\n\n📝 Текст вопроса:\n{q_text}\n\n📋 Варианты ответа:\n"
        
        for i, opt in enumerate(options_list, 1):
            prefix = "✅ " if opt['is_correct'] else "❌ "
            result_text += f"{i}. {prefix}{opt['text']}\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить ещё вопрос", callback_data="add_more_yes")],
            [InlineKeyboardButton(text="🏁 Завершить добавление", callback_data="add_more_no")]
        ])
        
        await message.answer(result_text, reply_markup=keyboard)
        await state.set_state(AdminQuestionCreation.add_more)
        
    except Exception as e:
        await message.answer(f"Ошибка при сохранении вопроса: {e}", reply_markup=ReplyKeyboardRemove())
        await state.clear()


async def save_question_without_options(message: types.Message, state: FSMContext):
    """Сохранить текстовый вопрос без вариантов."""
    data = await state.get_data()
    test_id = data.get('test_id')
    q_text = data.get('question_text') or ''
    q_type = 'text'
    points = data.get('points') or 1.0

    if not test_id:
        await message.answer("Ошибка: тест не выбран.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    try:
        async with async_session() as session:
            question = Question(
                test_id=test_id,
                text=q_text,
                question_type=q_type,
                points=points,
                order_num=0
            )
            session.add(question)
            await session.commit()

        # Показываем итоговую информацию
        result_text = f"✅ Текстовый вопрос сохранён!\n\n📝 Текст вопроса:\n{q_text}\n\nℹ️ Для этого вопроса пользователь должен будет ввести текстовый ответ."
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить ещё вопрос", callback_data="add_more_yes")],
            [InlineKeyboardButton(text="🏁 Завершить добавление", callback_data="add_more_no")]
        ])
        
        await message.answer(result_text, reply_markup=keyboard)
        await state.set_state(AdminQuestionCreation.add_more)
        
    except Exception as e:
        await message.answer(f"Ошибка при сохранении вопроса: {e}", reply_markup=ReplyKeyboardRemove())
        await state.clear()


@admin_testing_router.callback_query(F.data == "add_more_yes", AdminQuestionCreation.add_more)
async def admin_add_more_yes(callback: types.CallbackQuery, state: FSMContext):
    lang = await get_user_language(callback.from_user.id)
    await state.set_state(AdminQuestionCreation.question_text)
    await safe_edit(callback.message, "Отправьте текст следующего вопроса:")
    await callback.answer()


@admin_testing_router.callback_query(F.data == "add_more_no", AdminQuestionCreation.add_more)
async def admin_add_more_no(callback: types.CallbackQuery, state: FSMContext):
    lang = await get_user_language(callback.from_user.id)
    await state.clear()
    await callback.message.answer("✅ Добавление вопросов завершено.")
    # Показываем главное меню администратора
    await callback.message.answer(
        "👤 Главное меню администратора:",
        reply_markup=main_menu(callback.from_user.id, lang)
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
    lang = await get_user_language(callback.from_user.id)

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return
    
    # Создаём тест без выбора курса (course_id = None)
    await state.update_data(course_id=None)
    await state.set_state(AdminTestCreation.title)
    await safe_edit(callback.message, get_text("enter_test_title", lang))
    await callback.answer()


@admin_testing_router.callback_query(F.data == "upload_excel_test")
async def upload_excel_start(callback: types.CallbackQuery):
    """Начать загрузку теста из Excel: выбрать курс."""
    lang = await get_user_language(callback.from_user.id)

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    # Переходим к загрузке Excel без привязки к курсу
    # Тест будет создан с course_id = None
    await safe_edit(callback.message, get_text("enter_test_title", lang))
    await callback.answer()


@admin_testing_router.message(AdminTestCreation.title)
async def set_test_title(message: types.Message, state: FSMContext):
    """
    Установить название теста.
    
    Args:
        message: Сообщение
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)

    if message.from_user.id != ADMIN_ID:
        return
    
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminTestCreation.description)
    await message.answer(get_text("enter_test_description", lang))


@admin_testing_router.message(AdminTestCreation.description)
async def set_test_description(message: types.Message, state: FSMContext):
    """
    Установить описание теста.
    
    Args:
        message: Сообщение
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)

    if message.from_user.id != ADMIN_ID:
        return
    
    description = message.text.strip() if message.text.strip() != "-" else None
    await state.update_data(description=description)
    await state.set_state(AdminTestCreation.total_questions)
    await message.answer(get_text("enter_total_questions", lang))


@admin_testing_router.message(AdminTestCreation.total_questions)
async def set_total_questions(message: types.Message, state: FSMContext):
    """
    Установить количество вопросов.
    
    Args:
        message: Сообщение
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)

    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        total_questions = int(message.text.strip()) if message.text.strip() else 50
    except ValueError:
        total_questions = 50
    
    await state.update_data(total_questions=total_questions)
    await state.set_state(AdminTestCreation.time_limit)
    await message.answer(get_text("enter_time_limit", lang))


@admin_testing_router.message(AdminTestCreation.time_limit)
async def set_time_limit(message: types.Message, state: FSMContext):
    """
    Установить лимит времени.
    
    Args:
        message: Сообщение
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)

    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        time_limit = int(message.text.strip()) if message.text.strip() else 0
    except ValueError:
        time_limit = 0
    
    await state.update_data(time_limit=time_limit)
    await state.set_state(AdminTestCreation.scheduled_time)
    await message.answer(get_text("enter_scheduled_time", lang))


@admin_testing_router.message(AdminTestCreation.scheduled_time)
async def set_scheduled_time(message: types.Message, state: FSMContext):
    """
    Установить время начала теста.
    
    Args:
        message: Сообщение
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)

    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.strip()
    scheduled_time = None
    
    if text != "-":
        try:
            scheduled_time = datetime.strptime(text, "%d.%m.%Y %H:%M")
        except ValueError:
            await message.answer(get_text("invalid_format_datetime", lang))
            return
    
    await state.update_data(scheduled_time=scheduled_time)
    
    # Показываем подтверждение
    data = await state.get_data()
    
    text = (
        f"📋 Подтверждение создания теста:\n\n"
        f"• Название: {data['title']}\n"
        f"• Описание: {data['description'] or 'нет'}\n"
        f"• Вопросов: {data['total_questions']}\n"
        f"• Лимит времени: {data['time_limit']} мин\n"
        f"• Время начала: {data['scheduled_time'] or 'немедленно'}\n\n"
        f"Создать тест?"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("yes", lang), callback_data="confirm_test")],
        [InlineKeyboardButton(text=get_text("no", lang), callback_data="cancel_test")]
    ])

    await message.answer(text, reply_markup=keyboard)
    await state.set_state(AdminTestCreation.confirm)


@admin_testing_router.message(AdminTestCreation.upload_file, F.content_type.in_({"document"}))
async def handle_upload_file(message: types.Message, state: FSMContext):
    """Обработать загруженный Excel-файл и создать вопросы."""
    lang = await get_user_language(message.from_user.id)

    data = await state.get_data()
    created_test_id = data.get('created_test_id')
    if not created_test_id:
        await message.answer(get_text("upload_failed", lang, error="test id missing in state"))
        await state.clear()
        # Показываем главное меню администратора
        await message.answer(
            "👤 Главное меню администратора:",
            reply_markup=main_menu(message.from_user.id, lang)
        )
        return

    # Скачать файл в память
    bio = io.BytesIO()
    try:
        await message.document.download(destination=bio)
        bio.seek(0)
        # Попробуем читать лист 'Questions', иначе первый лист
        try:
            df = pd.read_excel(bio, sheet_name='Questions')
        except (KeyError, ValueError):
            bio.seek(0)
            df = pd.read_excel(bio)
    except (ValueError, OSError) as e:
        await message.answer(get_text("upload_failed", lang, error=str(e)))
        await state.clear()
        # Показываем главное меню администратора
        await message.answer(
            "👤 Главное меню администратора:",
            reply_markup=main_menu(message.from_user.id, lang)
        )
        return

    # Ожидаемые колонки: question, type, points, options
    required = {'question'}
    if not required.issubset(set(df.columns.str.lower())):
        # попытка нормализовать: сколько есть
        pass

    try:
        async with async_session() as session:
            test = await session.get(Test, created_test_id)
            if not test:
                raise RuntimeError('test not found')

            for idx, row in df.iterrows():
                # нормализация колонок
                row_data = {c.lower(): row[c] for c in df.columns}
                q_text = str(row_data.get('question') or row_data.get('text') or '').strip()
                if not q_text:
                    continue
                q_type = str(row_data.get('type') or 'single')
                try:
                    points = float(row_data.get('points')) if row_data.get('points') not in (None, '') else 1.0
                except Exception:
                    points = 1.0

                question = Question(
                    test_id=test.id,
                    text=q_text,
                    question_type=q_type,
                    points=points,
                    order_num=idx + 1
                )
                session.add(question)
                await session.flush()

                options_raw = row_data.get('options') or ''
                for opt in str(options_raw).split('||'):
                    opt = opt.strip()
                    if not opt:
                        continue
                    is_correct = False
                    if opt.startswith('*'):
                        is_correct = True
                        opt_text = opt.lstrip('*').strip()
                    else:
                        opt_text = opt
                    option = Option(question_id=question.id, text=opt_text, is_correct=is_correct)
                    session.add(option)

            await session.commit()

        await message.answer(get_text("upload_success", lang))
    except (ValueError, KeyError, AttributeError) as e:
        await message.answer(get_text("upload_failed", lang, error=str(e)))
    finally:
        await state.clear()
        # Показываем главное меню администратора
        await message.answer(
            "👤 Главное меню администратора:",
            reply_markup=main_menu(message.from_user.id, lang)
        )


@admin_testing_router.callback_query(F.data == "download_excel_template")
async def download_excel_template(callback: types.CallbackQuery):
    """Отправить шаблон Excel для загрузки теста."""
    lang = await get_user_language(callback.from_user.id)

    # Создаём DataFrame шаблона
    df = pd.DataFrame([
        {
            'question': 'Пример вопроса',
            'type': 'single',
            'points': 1,
            'options': "*Правильный вариант||Неправильный вариант"
        }
    ])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Questions', index=False)
    output.seek(0)

    await callback.message.bot.send_document(
        chat_id=callback.from_user.id,
        document=types.BufferedInputFile(file=output.read(), filename='template_questions.xlsx'),
        caption=get_text('download_template', lang)
    )

    await callback.answer()


@admin_testing_router.callback_query(F.data == "confirm_test", AdminTestCreation.confirm)
async def confirm_test_creation(callback: types.CallbackQuery, state: FSMContext):
    """
    Подтвердить создание теста.
    
    Args:
        callback: Callback query
        state: FSM контекст
    """
    lang = await get_user_language(callback.from_user.id)

    if callback.from_user.id != ADMIN_ID:
        return
    
    data = await state.get_data()
    
    async with async_session() as session:
        test = Test(
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
        # refresh id
        await session.refresh(test)

    # Если был выбран режим загрузки из Excel — попросить файл
    if data.get('upload_mode'):
        # сохраняем id созданного теста в state
        await state.update_data(created_test_id=test.id)
        await safe_edit(callback.message, get_text("test_created", lang, title=data['title']) + "\n" + get_text("send_excel_file", lang))
        await state.set_state(AdminTestCreation.upload_file)
        await callback.answer()
        return

    await safe_edit(callback.message, get_text("test_created", lang, title=data['title']))
    await state.clear()
    # Показываем главное меню администратора
    await callback.message.answer(
        "👤 Главное меню администратора:",
        reply_markup=main_menu(callback.from_user.id, lang)
    )
    await callback.answer()


@admin_testing_router.callback_query(F.data == "cancel_test", AdminTestCreation.confirm)
async def cancel_test_creation(callback: types.CallbackQuery, state: FSMContext):
    """
    Отменить создание теста.
    
    Args:
        callback: Callback query
        state: FSM контекст
    """
    lang = await get_user_language(callback.from_user.id)
    await state.clear()
    await callback.message.answer("❌ Создание теста отменено.")
    # Показываем главное меню администратора
    await callback.message.answer(
        "👤 Главное меню администратора:",
        reply_markup=main_menu(callback.from_user.id, lang)
    )
    await callback.answer()


@admin_testing_router.callback_query(F.data == "test_results")
async def show_test_results(callback: types.CallbackQuery):
    """
    Показать результаты тестов.
    
    Args:
        callback: Callback query
    """
    lang = await get_user_language(callback.from_user.id)

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return
    
    async with async_session() as session:
        # Получаем все тесты
        tests_result = await session.execute(select(Test))
        tests = tests_result.scalars().all()
    
    if not tests:
        await callback.answer(get_text("no_tests", lang), show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{test.title}", callback_data=f"test_stats_{test.id}")]
        for test in tests
    ] + [[InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="manage_tests")]])

    await safe_edit(callback.message, get_text("choose_test_for_results", lang), reply_markup=keyboard)
    await callback.answer()


@admin_testing_router.callback_query(F.data == "list_all_tests")
async def list_all_tests(callback: types.CallbackQuery):
    """Показать список всех тестов с возможностью редактирования."""
    lang = await get_user_language(callback.from_user.id)

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    async with async_session() as session:
        tests_result = await session.execute(select(Test).order_by(Test.created_at.desc()))
        tests = tests_result.scalars().all()

    if not tests:
        await callback.answer(get_text("no_tests", lang), show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=test.title, callback_data=f"edit_test_{test.id}")]
        for test in tests
    ] + [[InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="manage_tests")]])

    await safe_edit(callback.message, "📋 Список тестов:", reply_markup=keyboard)
    await callback.answer()


@admin_testing_router.callback_query(F.data.startswith("edit_test_"))
async def edit_test_menu(callback: types.CallbackQuery):
    """Показать меню редактирования для выбранного теста."""
    lang = await get_user_language(callback.from_user.id)
    
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    parts = callback.data.split("_")
    test_id = int(parts[-1])

    async with async_session() as session:
        test = await session.get(Test, test_id)

    if not test:
        await callback.answer("Тест не найден", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать название", callback_data=f"edit_test_title_{test_id}")],
        [InlineKeyboardButton(text="✏️ Редактировать описание", callback_data=f"edit_test_description_{test_id}")],
        [InlineKeyboardButton(text="🔁 Включить/выключить", callback_data=f"toggle_test_active_{test_id}")],
        [InlineKeyboardButton(text="🗑 Удалить тест", callback_data=f"delete_test_{test_id}")],
        [InlineKeyboardButton(text="📝 Добавить вопросы", callback_data=f"add_to_test_{test_id}")],
        [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="list_all_tests")]
    ])

    text = (
        f"📋 <b>Редактирование теста:</b>\n\n"
        f"• Название: {test.title}\n"
        f"• Описание: {test.description or 'нет'}\n"
        f"• Вопросов (ожидается): {test.total_questions}\n"
        f"• Активен: {'Да' if test.is_active else 'Нет'}\n"
    )

    await safe_edit(callback.message, text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@admin_testing_router.callback_query(F.data.startswith("toggle_test_active_"))
async def toggle_test_active(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    test_id = int(callback.data.split("_")[-1])
    async with async_session() as session:
        test = await session.get(Test, test_id)
        if not test:
            await callback.answer("Тест не найден", show_alert=True)
            return
        test.is_active = not bool(test.is_active)
        session.add(test)
        await session.commit()

    await callback.answer("Статус изменён")
    await safe_edit(callback.message, f"Статус теста обновлён. Активен: {'Да' if test.is_active else 'Нет'}")


@admin_testing_router.callback_query(F.data.startswith("delete_test_"))
async def delete_test(callback: types.CallbackQuery):
    lang = await get_user_language(callback.from_user.id)
    
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    test_id = int(callback.data.split("_")[-1])
    async with async_session() as session:
        test = await session.get(Test, test_id)
        if not test:
            await callback.answer("Тест не найден", show_alert=True)
            return

        # Удаляем вопросы, варианты и результаты вручную
        questions_result = await session.execute(select(Question).where(Question.test_id == test_id))
        questions = questions_result.scalars().all()
        for q in questions:
            opts_result = await session.execute(select(Option).where(Option.question_id == q.id))
            opts = opts_result.scalars().all()
            for o in opts:
                await session.delete(o)
            await session.delete(q)

        results_result = await session.execute(select(TestResult).where(TestResult.test_id == test_id))
        results = results_result.scalars().all()
        for r in results:
            await session.delete(r)

        await session.delete(test)
        await session.commit()

    await safe_edit(callback.message, "🗑 Тест удалён")
    # Показываем главное меню администратора
    await callback.message.answer(
        "👤 Главное меню администратора:",
        reply_markup=main_menu(callback.from_user.id, lang)
    )
    await callback.answer()


@admin_testing_router.callback_query(F.data.startswith("edit_test_title_"))
async def edit_test_title_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    test_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_test_id=test_id)
    await state.set_state(AdminTestEdit.title)
    await safe_edit(callback.message, "Введите новое название теста:")
    await callback.answer()


@admin_testing_router.message(AdminTestEdit.title)
async def handle_edit_title(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    test_id = data.get('edit_test_id')
    if not test_id:
        await message.answer("ID теста не указан")
        await state.clear()
        return

    new_title = message.text.strip()
    lang = await get_user_language(message.from_user.id)
    
    async with async_session() as session:
        test = await session.get(Test, test_id)
        if not test:
            await message.answer("Тест не найден")
            await state.clear()
            return
        test.title = new_title
        session.add(test)
        await session.commit()

    await message.answer(f"✅ Название теста обновлено: {new_title}")
    await state.clear()
    # Показываем главное меню администратора
    await message.answer(
        "👤 Главное меню администратора:",
        reply_markup=main_menu(message.from_user.id, lang)
    )


@admin_testing_router.callback_query(F.data.startswith("edit_test_description_"))
async def edit_test_description_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    test_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_test_id=test_id)
    await state.set_state(AdminTestEdit.description)
    await safe_edit(callback.message, "Введите новое описание теста (или '-' для очистки):")
    await callback.answer()


@admin_testing_router.message(AdminTestEdit.description)
async def handle_edit_description(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    test_id = data.get('edit_test_id')
    if not test_id:
        await message.answer("ID теста не указан")
        await state.clear()
        return

    new_desc = None if message.text.strip() == '-' else message.text.strip()
    lang = await get_user_language(message.from_user.id)
    
    async with async_session() as session:
        test = await session.get(Test, test_id)
        if not test:
            await message.answer("Тест не найден")
            await state.clear()
            return
        test.description = new_desc
        session.add(test)
        await session.commit()

    await message.answer("✅ Описание обновлено.")
    await state.clear()
    # Показываем главное меню администратора
    await message.answer(
        "👤 Главное меню администратора:",
        reply_markup=main_menu(message.from_user.id, lang)
    )


@admin_testing_router.callback_query(F.data.startswith("test_stats_"))
async def show_test_statistics(callback: types.CallbackQuery):
    """
    Показать статистику теста.
    
    Args:
        callback: Callback query
    """
    lang = await get_user_language(callback.from_user.id)

    parts = callback.data.split("_")
    test_id = int(parts[-1])
    
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
            await callback.answer(get_text("no_results_for_test", lang), show_alert=True)
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
            [InlineKeyboardButton(text=get_text("export_to_excel", lang), callback_data=f"export_test_{test_id}")],
            [InlineKeyboardButton(text=get_text("list_results", lang), callback_data=f"list_results_{test_id}")],
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="test_results")]
        ])
    
    await safe_edit(callback.message, text, reply_markup=keyboard)
    await callback.answer()


@admin_testing_router.callback_query(F.data.startswith("export_test_"))
async def export_test_results(callback: types.CallbackQuery):
    """
    Экспортировать результаты теста в Excel.
    
    Args:
        callback: Callback query
    """
    lang = await get_user_language(callback.from_user.id)

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
            await callback.answer(get_text("no_data_export", lang), show_alert=True)
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
            caption=get_text("export_caption", lang, test_id=test_id)
        )
    
    await callback.answer()
