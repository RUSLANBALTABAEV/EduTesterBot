# handlers/testing.py
"""
Обработчики для системы тестирования.
"""
import asyncio
import json
import logging
from datetime import datetime
from aiogram import Router, F, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from db.models import User, Test, Question, Option, TestResult
from db.session import async_session
from fsm.test import Testing
from i18n.locales import get_text

testing_router = Router()

logger = logging.getLogger(__name__)


async def get_user_language(user_id: int) -> str:
    """Получить язык пользователя."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user.language if user and user.language else "ru"


@testing_router.callback_query(F.data.startswith("start_test_"))
async def start_test(callback: types.CallbackQuery, state: FSMContext):
    """
    Начать тестирование.
    
    Args:
        callback: Callback query
        state: FSM контекст
    """
    lang = await get_user_language(callback.from_user.id)
    parts = callback.data.split("_")
    test_id = int(parts[-1])
    
    async with async_session() as session:
        # Проверяем пользователя
        user_result = await session.execute(
            select(User).where(User.user_id == callback.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user or not user.is_active:
            await callback.answer(
                get_text("register_first", lang),
                show_alert=True
            )
            return
        
        # Проверяем тест
        test_result = await session.execute(
            select(Test).where(Test.id == test_id)
        )
        test = test_result.scalar_one_or_none()
        
        if not test or not test.is_active:
            await callback.answer(
                "Тест недоступен",
                show_alert=True
            )
            return
        
        # Проверяем время тестирования
        now = datetime.now()
        if test.scheduled_time and test.scheduled_time > now:
            time_left = test.scheduled_time - now
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
            await callback.answer(
                f"Тест начнется через {hours} ч {minutes} мин",
                show_alert=True
            )
            return
        
        # Проверяем, не завершил ли уже пользователь тест
        result_exists = await session.execute(
            select(TestResult).where(
                and_(
                    TestResult.user_id == user.id,
                    TestResult.test_id == test_id,
                    TestResult.completed_at.is_not(None)
                )
            )
        )
        existing_result = result_exists.scalar_one_or_none()
        
        if existing_result:
            await callback.answer(
                "Вы уже прошли этот тест",
                show_alert=True
            )
            return
        
        # Создаем или получаем существующий результат
        result_in_progress = await session.execute(
            select(TestResult).where(
                and_(
                    TestResult.user_id == user.id,
                    TestResult.test_id == test_id,
                    TestResult.completed_at.is_(None)
                )
            )
        )
        test_result_obj = result_in_progress.scalar_one_or_none()
        
        if not test_result_obj:
            test_result_obj = TestResult(
                user_id=user.id,
                test_id=test_id,
                max_score=test.max_score,
                started_at=now
            )
            session.add(test_result_obj)
            await session.commit()
            await session.refresh(test_result_obj)
        
        # Получаем вопросы теста
        questions_result = await session.execute(
            select(Question).where(
                Question.test_id == test_id
            ).order_by(Question.order_num)
        )
        questions = questions_result.scalars().all()
        
        if not questions:
            await callback.answer(
                "В тесте пока нет вопросов",
                show_alert=True
            )
            return
        
        # Сохраняем данные в state
        await state.update_data(
            test_id=test_id,
            test_result_id=test_result_obj.id,
            current_question=0,
            questions=[q.id for q in questions],
            answers={},
            start_time=now.isoformat(),
            time_limit=test.time_limit
        )
        
        # Запускаем таймер, если есть ограничение по времени
        if test.time_limit:
            asyncio.create_task(test_timer(callback.from_user.id, state, test.time_limit, callback.message.chat.id, callback.message.bot))
        
        await state.set_state(Testing.waiting_for_answer)
        await show_question(callback.message, state, lang)
    
    await callback.answer()


@testing_router.message(F.text.in_(["Тесты", "Tests", "Testlar"]))
async def list_available_tests(message: types.Message) -> None:
    """Показать список доступных тестов для пользователя."""
    lang = await get_user_language(message.from_user.id)

    if not lang:
        from keyboards.reply import language_keyboard
        await message.answer(get_text("choose_language", "ru"), reply_markup=language_keyboard())
        return

    async with async_session() as session:
        query = select(Test).where(Test.is_active == True)
        tests_result = await session.execute(query)
        tests = tests_result.scalars().all()

    if not tests:
        await message.answer(get_text("no_tests", lang))
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=test.title, callback_data=f"start_test_{test.id}")]
        for test in tests
    ])

    await message.answer(get_text("available_tests", lang), reply_markup=keyboard)


@testing_router.message(F.text.in_(["Мои тесты", "My Tests", "Mening testlarim"]))
async def list_my_tests(message: types.Message) -> None:
    """Показать список доступных (не пройденных) тестов для пользователя."""
    lang = await get_user_language(message.from_user.id)

    async with async_session() as session:
        user_result = await session.execute(
            select(User).where(User.user_id == message.from_user.id)
        )
        user = user_result.scalar_one_or_none()

        if not user or not user.is_active:
            await message.answer(get_text("not_registered", lang))
            return

        tests_result = await session.execute(select(Test).where(Test.is_active == True))
        tests = tests_result.scalars().all()

        avail = []
        for test in tests:
            res = await session.execute(
                select(TestResult).where(
                    and_(
                        TestResult.test_id == test.id, 
                        TestResult.user_id == user.id, 
                        TestResult.completed_at.is_not(None)
                    )
                )
            )
            finished = res.scalar_one_or_none()
            if not finished:
                avail.append(test)

    if not avail:
        await message.answer(get_text("no_my_tests", lang))
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t.title, callback_data=f"start_test_{t.id}")] for t in avail
    ])

    await message.answer(get_text("available_tests", lang), reply_markup=keyboard)


# Добавляем обработку кнопок "Назад" и "Вперёд"
@testing_router.callback_query(F.data.startswith("navigate_"))
async def navigate_question(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработать переход между вопросами.

    Args:
        callback: Callback-запрос
        state: FSM контекст
    """
    data = await state.get_data()
    current_idx = data.get('current_question', 0)
    questions = data.get('questions', [])

    if not questions:
        await callback.answer("Вопросы не найдены.", show_alert=True)
        return

    direction = callback.data.split("_")[-1]

    if direction == "next":
        current_idx = min(current_idx + 1, len(questions) - 1)
    elif direction == "prev":
        current_idx = max(current_idx - 1, 0)

    await state.update_data(current_question=current_idx)
    await show_question(callback.message, state)
    await callback.answer()


async def show_question(message: types.Message, state: FSMContext, lang: str = "ru"):
    """
    Показать текущий вопрос.
    
    Args:
        message: Сообщение
        state: FSM контекст
        lang: Язык интерфейса
    """
    if message is None:
        logger.error("Message is None in show_question")
        return
        
    data = await state.get_data()
    current_idx = data.get('current_question', 0)
    questions = data.get('questions', [])
    
    if current_idx >= len(questions):
        logger.error("Question index %s out of range %s", current_idx, len(questions))
        await complete_test(message, state, lang)
        return
        
    question_id = questions[current_idx]
    answers = data.get('answers', {})
    selected_for_q = answers.get(str(question_id), [])

    async with async_session() as session:
        try:
            question_result = await session.execute(
                select(Question)
                .options(selectinload(Question.options))
                .where(Question.id == question_id)
            )
            question = question_result.scalar_one_or_none()

            if not question:
                logger.error("Question %s not found", question_id)
                await message.answer("Ошибка: вопрос не найден.")
                return

            options = question.options

            if not options and question.question_type != 'text':
                logger.warning("Question %s has no options", question_id)

            keyboard = []
            
            if question.question_type == 'text':
                # Для текстовых вопросов
                text = f"❓ <b>Вопрос {current_idx + 1} из {len(questions)}</b>\n\n"
                text += f"{question.text}\n\n"
                text += "✍️ <i>Введите ваш ответ текстом</i>"
                
                keyboard.append([
                    InlineKeyboardButton(
                        text="⏭ Пропустить",
                        callback_data=f"skip_{question_id}"
                    )
                ])
            else:
                # Для вопросов с вариантами ответов
                for i, option in enumerate(options, 1):
                    prefix = "✅ " if option.id in selected_for_q else ""
                    keyboard.append([
                        InlineKeyboardButton(
                            text=f"{prefix}{i}. {option.text[:100]}",
                            callback_data=f"answer_{question_id}_{option.id}"
                        )
                    ])

                keyboard.append([
                    InlineKeyboardButton(
                        text="⏭ Пропустить",
                        callback_data=f"skip_{question_id}"
                    )
                ])

                if question.question_type == 'multiple':
                    keyboard.append([
                        InlineKeyboardButton(
                            text="✅ Готово",
                            callback_data=f"finish_{question_id}"
                        )
                    ])

                text = f"❓ <b>Вопрос {current_idx + 1} из {len(questions)}</b>\n\n"
                text += f"{question.text}\n\n"

                # Обновляем текстовые метки типов вопросов
                if question.question_type == 'single':
                    text += "📝 <i>(Несколько вариантов один ответ)</i>"
                elif question.question_type == 'multiple':
                    text += "📝 <i>(Несколько вариантов два ответа)</i>"

            # Добавляем кнопки "Назад" и "Вперёд"
            navigation_buttons = []
            if current_idx > 0:
                navigation_buttons.append(InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="navigate_prev"
                ))
            if current_idx < len(questions) - 1:
                navigation_buttons.append(InlineKeyboardButton(
                    text="Вперёд ➡️",
                    callback_data="navigate_next"
                ))
            if navigation_buttons:
                keyboard.append(navigation_buttons)

            try:
                await message.edit_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                    parse_mode="HTML"
                )
            except TelegramBadRequest as e:
                msg = str(e).lower()
                if 'message is not modified' in msg:
                    logger.debug('Edit skipped: message not modified for question %s', question_id)
                elif 'message to edit not found' in msg or 'message can\'t be edited' in msg:
                    await message.answer(
                        text,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                        parse_mode="HTML"
                    )
                else:
                    logger.exception('TelegramBadRequest while editing question %s', question_id)
            except OSError as e:
                logger.exception("OS error in show_question: %s", e)
                
        except NoResultFound:
            logger.error("Question with ID %s not found in the database.", question_id)
            await message.answer("Ошибка: вопрос не найден.")
        except Exception as e:
            logger.exception("Error in show_question: %s", e)
            await message.answer("Произошла ошибка при загрузке вопроса.")


@testing_router.message(Testing.waiting_for_answer, F.text)
async def process_text_answer(message: types.Message, state: FSMContext):
    """
    Обработать текстовый ответ пользователя.
    
    Args:
        message: Сообщение с текстом
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)
    
    data = await state.get_data()
    current_idx = data.get('current_question', 0)
    questions = data.get('questions', [])
    
    if current_idx >= len(questions):
        return
        
    question_id = questions[current_idx]
    
    async with async_session() as session:
        question_result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = question_result.scalar_one_or_none()
        
        if not question or question.question_type != 'text':
            return
        
        # Сохраняем текстовый ответ
        answers = data.get('answers', {})
        answers[str(question_id)] = [message.text.strip()]
        await state.update_data(answers=answers)
        
        # Переходим к следующему вопросу
        if current_idx + 1 < len(questions):
            await state.update_data(current_question=current_idx + 1)
            
            # Создаём временное сообщение для show_question
            temp_msg = await message.answer("⏳ Загрузка следующего вопроса...")
            await show_question(temp_msg, state, lang)
        else:
            temp_msg = await message.answer("⏳ Подсчёт результатов...")
            await complete_test(temp_msg, state, lang)


@testing_router.callback_query(F.data.startswith("answer_"), Testing.waiting_for_answer)
async def process_answer(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработать ответ пользователя.
    
    Args:
        callback: Callback query
        state: FSM контекст
    """
    lang = await get_user_language(callback.from_user.id)
    
    try:
        parts = callback.data.split("_")
        question_id = int(parts[1])
        option_id = int(parts[2])
    except (IndexError, ValueError) as e:
        logger.error("Invalid callback data format: %s, error: %s", callback.data, e)
        await callback.answer("Ошибка обработки ответа")
        return
    
    data = await state.get_data()
    current_idx = data.get('current_question', 0)
    
    answers = data.get('answers', {})
    question_key = str(question_id)
    
    if question_key not in answers:
        answers[question_key] = []
    
    async with async_session() as session:
        question_result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = question_result.scalar_one_or_none()
        
        if not question:
            await callback.answer("Ошибка: вопрос не найден")
            return
        
        if question.question_type == 'single':
            answers[question_key] = [option_id]
            await state.update_data(answers=answers)
            
            questions = data.get('questions', [])
            if current_idx + 1 < len(questions):
                await state.update_data(current_question=current_idx + 1)
                await show_question(callback.message, state, lang)
            else:
                await complete_test(callback.message, state, lang)
        else:
            if option_id in answers[question_key]:
                answers[question_key].remove(option_id)
            else:
                answers[question_key].append(option_id)
            
            await state.update_data(answers=answers)
            await show_question(callback.message, state, lang)
    
    await callback.answer()


@testing_router.callback_query(F.data.startswith("finish_"), Testing.waiting_for_answer)
async def finish_question(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработчик подтверждения ответа для multiple вопросов.
    """
    lang = await get_user_language(callback.from_user.id)
    
    data = await state.get_data()
    current_idx = data.get('current_question', 0)
    questions = data.get('questions', [])

    if current_idx + 1 < len(questions):
        await state.update_data(current_question=current_idx + 1)
        await show_question(callback.message, state, lang)
    else:
        await complete_test(callback.message, state, lang)

    await callback.answer()


@testing_router.callback_query(F.data.startswith("skip_"), Testing.waiting_for_answer)
async def skip_question(callback: types.CallbackQuery, state: FSMContext):
    """
    Пропустить вопрос.
    
    Args:
        callback: Callback query
        state: FSM контекст
    """
    lang = await get_user_language(callback.from_user.id)
    
    data = await state.get_data()
    current_idx = data.get('current_question', 0)
    questions = data.get('questions', [])
    
    if current_idx + 1 < len(questions):
        await state.update_data(current_question=current_idx + 1)
        await show_question(callback.message, state, lang)
    else:
        await complete_test(callback.message, state, lang)
    
    await callback.answer()


async def complete_test(message: types.Message, state: FSMContext, lang: str = "ru"):
    """
    Завершить тест и подсчитать результаты.
    
    Args:
        message: Сообщение
        state: FSM контекст
        lang: Язык интерфейса
    """
    if message is None:
        logger.error("Message is None in complete_test")
        return
        
    data = await state.get_data()
    answers = data.get('answers', {})
    test_result_id = data.get('test_result_id')
    
    if not test_result_id:
        logger.error("No test_result_id in state")
        await message.answer("Ошибка: данные теста не найдены")
        await state.clear()
        return
    
    total_score = 0.0
    max_possible_score = 0.0
    
    async with async_session() as session:
        for question_key, selected_options in answers.items():
            question_id = int(question_key)
            
            question_result = await session.execute(
                select(Question).where(Question.id == question_id)
            )
            question = question_result.scalar_one_or_none()
            
            if not question:
                logger.warning("Question %s not found during scoring", question_id)
                continue
            
            max_possible_score += float(question.points)
            
            if question.question_type == 'text':
                # Для текстовых вопросов - не оцениваем автоматически
                continue
            
            correct_options_result = await session.execute(
                select(Option.id).where(
                    and_(
                        Option.question_id == question_id,
                        Option.is_correct == True
                    )
                )
            )
            correct_options = {row[0] for row in correct_options_result.all()}
            
            if question.question_type == 'single':
                if selected_options and selected_options[0] in correct_options:
                    total_score += float(question.points)
            elif question.question_type == 'multiple':
                selected_set = set(selected_options)
                if selected_set == correct_options:
                    total_score += float(question.points)
                elif selected_set.issubset(correct_options) and selected_set:
                    total_score += float(question.points) * len(selected_set) / len(correct_options)
        
        test_result = await session.get(TestResult, test_result_id)
        if test_result:
            test_result.score = total_score
            test_result.completed_at = datetime.now()
            test_result.answers_data = json.dumps(answers)
            await session.commit()
        else:
            logger.error("TestResult %s not found", test_result_id)
        
        test_result_obj = await session.execute(
            select(Test).where(Test.id == data.get('test_id'))
        )
        test = test_result_obj.scalar_one_or_none()
        
        percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
        
        text = "🎉 <b>Тестирование завершено!</b>\n\n"
        text += "📊 <b>Результаты:</b>\n"
        text += f"• Набрано баллов: <b>{total_score:.1f}</b> из {max_possible_score:.1f}\n"
        text += f"• Процент выполнения: <b>{percentage:.1f}%</b>\n"
        text += f"• Оценка: <b>{get_grade(percentage)}</b>\n\n"
        
        if test:
            text += f"📝 Тест: <i>{test.title}</i>\n\n"
        
        text += "✨ Спасибо за участие!"
        
        try:
            await message.edit_text(text, parse_mode="HTML")
        except TelegramBadRequest as e:
            logger.debug("Could not edit message: %s", e)
            await message.answer(text, parse_mode="HTML")
    
    await state.clear()


def get_grade(percentage: float) -> str:
    """Получить оценку по проценту."""
    if percentage >= 90:
        return "5 (Отлично)"
    elif percentage >= 75:
        return "4 (Хорошо)"
    elif percentage >= 60:
        return "3 (Удовлетворительно)"
    elif percentage >= 50:
        return "2 (Неудовлетворительно)"
    else:
        return "1 (Плохо)"


async def test_timer(user_id: int, state: FSMContext, minutes: int, chat_id: int, bot):
    """
    Таймер для теста.
    
    Args:
        user_id: ID пользователя
        state: FSM контекст
        minutes: Время в минутах
        chat_id: ID чата
        bot: Экземпляр бота
    """
    await asyncio.sleep(minutes * 60)
    
    try:
        current_state = await state.get_state()
        if current_state == Testing.waiting_for_answer.state:
            lang = await get_user_language(user_id)
            
            # Создаём временное сообщение
            temp_msg = await bot.send_message(chat_id, "⏰ Время вышло! Подсчёт результатов...")
            await complete_test(temp_msg, state, lang)
            await bot.send_message(chat_id, "⏰ Тест автоматически завершен по истечении времени.")
    except Exception as e:
        logger.exception("Error in test_timer: %s", e)
