# handlers/testing.py
"""
Обработчики для системы тестирования.
"""
import json
import asyncio
import logging
try:
    from aiogram.exceptions import TelegramBadRequest
except Exception:
    # Fallback for older/newer aiogram packaging
    try:
        from aiogram.utils.exceptions import TelegramBadRequest
    except Exception:
        TelegramBadRequest = Exception
from datetime import datetime, timedelta
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from db.models import User, Test, Question, Option, TestResult
from db.session import async_session
from fsm.test import Testing
from i18n.locales import get_text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

testing_router = Router()

logger = logging.getLogger(__name__)


async def get_user_language(user_id: int) -> str:
    """Получить язык пользователя."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user.language if user and user.language else None


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
            start_time=now,
            time_limit=test.time_limit
        )
        
        # Запускаем таймер, если есть ограничение по времени
        if test.time_limit:
            asyncio.create_task(test_timer(callback, state, test.time_limit))
        
        await state.set_state(Testing.waiting_for_answer)
        await show_question(callback.message, state)
    
    await callback.answer()


@testing_router.message(F.text.in_(["Тесты", "Tests", "Testlar"]))
async def list_available_tests(message: types.Message) -> None:
    """Показать список доступных тестов для пользователя."""
    lang = await get_user_language(message.from_user.id)

    # Если язык не выбран — попросим выбрать
    if not lang:
        from keyboards.reply import language_keyboard
        await message.answer(get_text("choose_language", "ru"), reply_markup=language_keyboard())
        return

    async with async_session() as session:
        now = datetime.now()
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
        # Проверяем пользователя
        user_result = await session.execute(
            select(User).where(User.user_id == message.from_user.id)
        )
        user = user_result.scalar_one_or_none()

        if not user or not user.is_active:
            await message.answer(get_text("not_registered", lang))
            return

        # Получаем все активные тесты
        tests_result = await session.execute(select(Test).where(Test.is_active == True))
        tests = tests_result.scalars().all()

        avail = []
        for test in tests:
            # Проверяем, завершал ли пользователь тест
            res = await session.execute(
                select(TestResult).where(
                    and_(TestResult.test_id == test.id, TestResult.user_id == user.id, TestResult.completed_at.is_not(None))
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


async def show_question(message: types.Message, state: FSMContext):
    """
    Показать текущий вопрос.
    
    Args:
        message: Сообщение
        state: FSM контекст
    """
    data = await state.get_data()
    current_idx = data['current_question']
    question_id = data['questions'][current_idx]
    answers = data.get('answers', {})
    selected_for_q = answers.get(question_id, [])

    async with async_session() as session:
        try:
            # Получаем вопрос
            question_result = await session.execute(
                select(Question).options(selectinload(Question.options)).where(Question.id == question_id)
            )
            question = question_result.scalar_one()

            # Проверяем, что вопрос найден
            if not question:
                await message.answer("Ошибка: вопрос не найден.")
                return

            # Получаем варианты ответов
            options = question.options

            # Создаем клавиатуру с вариантами
            keyboard = []
            for i, option in enumerate(options, 1):
                prefix = "✅ " if option.id in selected_for_q else ""
                keyboard.append([
                    InlineKeyboardButton(
                        text=f"{prefix}{i}. {option.text[:100]}",
                        callback_data=f"answer_{question_id}_{option.id}"
                    )
                ])

            # Добавляем кнопку пропуска
            keyboard.append([
                InlineKeyboardButton(
                    text="⏭ Пропустить",
                    callback_data=f"skip_{question_id}"
                )
            ])

            # Для multiple вопросов добавляем кнопку подтверждения выбора
            if question.question_type == 'multiple':
                keyboard.append([
                    InlineKeyboardButton(
                        text="✅ Готово",
                        callback_data=f"finish_{question_id}"
                    )
                ])

            # Отправляем вопрос
            text = f"Вопрос {current_idx + 1} из {len(data['questions'])}\n\n"
            text += f"{question.text}\n\n"

            if question.question_type == 'multiple':
                text += "(Выберите все правильные ответы)"

            try:
                if message is None:
                    return
                await message.edit_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                )
            except TelegramBadRequest as e:
                # Игнорируем ошибку, когда контент не изменился
                # и логируем прочие ошибки
                msg = str(e)
                if 'message is not modified' in msg:
                    logger.debug('Edit skipped: message not modified for question %s', question_id)
                else:
                    logger.exception('TelegramBadRequest while editing question %s: %s', question_id, e)
        except NoResultFound:
            logger.error("Question with ID %s not found in the database.", question_id)
            await message.answer("Ошибка: вопрос не найден.")
        except AttributeError as e:
            logger.error("Attribute error: %s", e)
            await message.answer("Ошибка: некорректные данные.")


@testing_router.callback_query(F.data.startswith("answer_"))
async def process_answer(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработать ответ пользователя.
    
    Args:
        callback: Callback query
        state: FSM контекст
    """
    _, question_id, option_id = callback.data.split("_")
    question_id = int(question_id)
    option_id = int(option_id)
    
    data = await state.get_data()
    current_idx = data['current_question']
    
    # Сохраняем ответ
    answers = data.get('answers', {})
    if question_id not in answers:
        answers[question_id] = []
    
    # Для одиночного выбора очищаем предыдущие ответы
    async with async_session() as session:
        question_result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = question_result.scalar_one_or_none()
        
        if question.question_type == 'single':
            answers[question_id] = [option_id]
        else:
            if option_id in answers[question_id]:
                answers[question_id].remove(option_id)
            else:
                answers[question_id].append(option_id)
    
    await state.update_data(answers=answers)
    
    # Для одиночного выбора сразу переходим к следующему вопросу,
    # для множественного — оставляем пользователя выбирать несколько и
    # ждём нажатия кнопки подтверждения.
    if question.question_type == 'single':
        if current_idx + 1 < len(data['questions']):
            await state.update_data(current_question=current_idx + 1)
            await show_question(callback.message, state)
        else:
            await complete_test(callback.message, state)
    else:
        # Обновляем отображение текущего вопроса (чтобы можно было увидеть изменения)
        await show_question(callback.message, state)
    
    await callback.answer()


@testing_router.callback_query(F.data.startswith("finish_"))
async def finish_question(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработчик подтверждения ответа для multiple вопросов.
    """
    parts = callback.data.split("_")
    question_id = int(parts[-1])

    data = await state.get_data()
    current_idx = data['current_question']

    if current_idx + 1 < len(data['questions']):
        await state.update_data(current_question=current_idx + 1)
        await show_question(callback.message, state)
    else:
        await complete_test(callback.message, state)

    await callback.answer()


@testing_router.callback_query(F.data.startswith("skip_"))
async def skip_question(callback: types.CallbackQuery, state: FSMContext):
    """
    Пропустить вопрос.
    
    Args:
        callback: Callback query
        state: FSM контекст
    """
    data = await state.get_data()
    current_idx = data['current_question']
    
    if current_idx + 1 < len(data['questions']):
        await state.update_data(current_question=current_idx + 1)
        await show_question(callback.message, state)
    else:
        await complete_test(callback.message, state)
    
    await callback.answer()


async def complete_test(message: types.Message, state: FSMContext):
    """
    Завершить тест и подсчитать результаты.
    
    Args:
        message: Сообщение
        state: FSM контекст
    """
    data = await state.get_data()
    answers = data.get('answers', {})
    
    total_score = 0
    max_possible_score = 0
    
    async with async_session() as session:
        # Подсчитываем результаты
        for question_id, selected_options in answers.items():
            question_result = await session.execute(
                select(Question).where(Question.id == question_id)
            )
            question = question_result.scalar_one_or_none()
            
            if not question:
                continue
            
            max_possible_score += question.points
            
            # Получаем правильные ответы
            correct_options_result = await session.execute(
                select(Option.id).where(
                    and_(
                        Option.question_id == question_id,
                        Option.is_correct == True
                    )
                )
            )
            correct_options = {row[0] for row in correct_options_result.all()}
            
            # Подсчитываем баллы
            if question.question_type == 'single':
                if selected_options and selected_options[0] in correct_options:
                    total_score += question.points
            elif question.question_type == 'multiple':
                selected_set = set(selected_options)
                if selected_set == correct_options:
                    total_score += question.points
                elif selected_set.issubset(correct_options) and selected_set:
                    # Частичный балл за частично правильный ответ
                    total_score += question.points * len(selected_set) / len(correct_options)
        
        # Обновляем результат теста
        test_result = await session.get(TestResult, data['test_result_id'])
        if test_result:
            test_result.score = total_score
            test_result.completed_at = datetime.now()
            test_result.answers_data = json.dumps(answers)
            await session.commit()
        
        # Получаем информацию о тесте
        test_result_obj = await session.execute(
            select(Test).where(Test.id == data['test_id'])
        )
        test = test_result_obj.scalar_one_or_none()
        
        # Формируем сообщение с результатами
        percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
        
        text = (
            f"🎉 Тестирование завершено!\n\n"
            f"📊 Результаты:\n"
            f"• Набрано баллов: {total_score:.1f} из {max_possible_score:.1f}\n"
            f"• Процент выполнения: {percentage:.1f}%\n"
            f"• Оценка: {get_grade(percentage)}\n\n"
        )
        
        if test:
            text += f"Тест: {test.title}\n"
        
        text += "Спасибо за участие!"
        
        await message.edit_text(text)
    
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


async def test_timer(callback: types.CallbackQuery, state: FSMContext, minutes: int):
    """
    Таймер для теста.
    
    Args:
        callback: Callback query
        state: FSM контекст
        minutes: Время в минутах
    """
    await asyncio.sleep(minutes * 60)
    
    # Проверяем, не завершен ли уже тест
    current_state = await state.get_state()
    if current_state == Testing.waiting_for_answer:
        await complete_test(callback.message, state)
        await callback.message.answer("⏰ Время вышло! Тест автоматически завершен.")
