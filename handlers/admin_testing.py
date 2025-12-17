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
        return user.language if user and user.language else None


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
        [InlineKeyboardButton(text=get_text("btn_upload_excel", lang) if "btn_upload_excel" in [] else "📤 Загрузить тест из Excel", callback_data="upload_excel_test")],
        [InlineKeyboardButton(text=get_text("btn_download_template", lang) if "btn_download_template" in [] else "📥 Скачать шаблон Excel", callback_data="download_excel_template")],
        [InlineKeyboardButton(text=get_text("btn_add_questions", lang), callback_data="add_questions")],
        [InlineKeyboardButton(text=get_text("btn_test_results", lang), callback_data="test_results")],
        [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin_menu")]
    ])

    await callback.message.edit_text(
        get_text("manage_testing_title", lang),
        reply_markup=keyboard
    )
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

    await callback.message.edit_text(get_text("choose_test_for_results", lang), reply_markup=keyboard)
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

    await callback.message.edit_text(get_text("enter_question_text", lang) if "enter_question_text" in [] else "Отправьте текст вопроса:")
    await callback.answer()


@admin_testing_router.message(AdminQuestionCreation.question_text)
async def admin_question_text(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(question_text=message.text.strip())
    # Спрашиваем тип вопроса
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Одиночный (single)", callback_data="qtype_single")],
        [InlineKeyboardButton(text="Множественный (multiple)", callback_data="qtype_multiple")],
        [InlineKeyboardButton(text="Текстовый (text)", callback_data="qtype_text")]
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
    await callback.message.edit_text("Укажите количество баллов за вопрос (например, 1):")
    await callback.answer()


@admin_testing_router.message(AdminQuestionCreation.points)
async def admin_question_points(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        pts = float(message.text.strip())
    except Exception:
        pts = 1.0

    await state.update_data(points=pts)
    await state.set_state(AdminQuestionCreation.options)
    await message.answer("Отправьте варианты ответа через '||'. Отметьте правильный вариант(ы) префиксом '*', или отправьте '-' для текстового ответа:")


@admin_testing_router.message(AdminQuestionCreation.options)
async def admin_question_options(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()
    test_id = data.get('test_id')
    if not test_id:
        await message.answer("Ошибка: тест не выбран.")
        await state.clear()
        return

    q_text = data.get('question_text') or ''
    q_type = data.get('question_type') or 'single'
    points = data.get('points') or 1.0

    opts_raw = message.text.strip()

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

            if opts_raw != '-' and q_type != 'text':
                for opt in str(opts_raw).split('||'):
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

        # спросить добавить ещё
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Добавить ещё вопрос", callback_data="add_more_yes")],
            [InlineKeyboardButton(text="Готово", callback_data="add_more_no")]
        ])
        await message.answer("Вопрос сохранён.", reply_markup=keyboard)
        await state.set_state(AdminQuestionCreation.add_more)
    except Exception as e:
        await message.answer(f"Ошибка при сохранении вопроса: {e}")
        await state.clear()


@admin_testing_router.callback_query(F.data == "add_more_yes", AdminQuestionCreation.add_more)
async def admin_add_more_yes(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminQuestionCreation.question_text)
    await callback.message.edit_text("Отправьте текст следующего вопроса:")
    await callback.answer()


@admin_testing_router.callback_query(F.data == "add_more_no", AdminQuestionCreation.add_more)
async def admin_add_more_no(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Добавление вопросов завершено.")
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
    
    async with async_session() as session:
        result = await session.execute(select(Course))
        courses = result.scalars().all()

    # Показываем список курсов и кнопку "без курса"
    keyboard_rows = [[InlineKeyboardButton(text=course.title, callback_data=f"select_course_{course.id}")] for course in courses]
    keyboard_rows.append([InlineKeyboardButton(text=get_text("btn_no_course", lang), callback_data="select_course_none")])
    keyboard_rows.append([InlineKeyboardButton(text=get_text("cancel", lang), callback_data="admin_menu")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(
        get_text("choose_course_for_test", lang),
        reply_markup=keyboard
    )
    await state.set_state(AdminTestCreation.select_course)
    await callback.answer()



@admin_testing_router.callback_query(F.data == "upload_excel_test")
async def upload_excel_start(callback: types.CallbackQuery):
    """Начать загрузку теста из Excel: выбрать курс."""
    lang = await get_user_language(callback.from_user.id)

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(Course))
        courses = result.scalars().all()

    keyboard_rows = [[InlineKeyboardButton(text=course.title, callback_data=f"upload_course_{course.id}")] for course in courses]
    keyboard_rows.append([InlineKeyboardButton(text=get_text("btn_no_course", lang), callback_data="upload_course_none")])
    keyboard_rows.append([InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin_menu")])

    await callback.message.edit_text(get_text("choose_course_for_test", lang), reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows))
    await callback.answer()


@admin_testing_router.callback_query(F.data.startswith("upload_course_"))
async def upload_course_select(callback: types.CallbackQuery, state: FSMContext):
    """Выбран курс для загрузки из Excel — запрашиваем название теста."""
    lang = await get_user_language(callback.from_user.id)
    data_parts = callback.data.split("_")
    if data_parts[-1] == 'none':
        course_id = None
    else:
        course_id = int(data_parts[2])

    await state.update_data(course_id=course_id, upload_mode=True)
    await state.set_state(AdminTestCreation.title)

    await callback.message.edit_text(get_text("enter_test_title", lang))
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
    lang = await get_user_language(callback.from_user.id)

    data_parts = callback.data.split("_")
    if data_parts[-1] == 'none':
        course_id = None
    else:
        course_id = int(data_parts[2])

    await state.update_data(course_id=course_id)
    await state.set_state(AdminTestCreation.title)

    await callback.message.edit_text(get_text("enter_test_title", lang))
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
    
    # Показать название курса или метку "без курса"
    course_label = get_text("no_course_selected", lang)
    if data.get('course_id'):
        try:
            async with async_session() as session:
                course_obj = await session.get(Course, data.get('course_id'))
                if course_obj:
                    course_label = course_obj.title
        except Exception:
            pass

    text = (
        f"📋 Подтверждение создания теста:\n\n"
        f"• Курс: {course_label}\n"
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
        return

    # Скачать файл в память
    bio = io.BytesIO()
    try:
        await message.document.download(destination=bio)
        bio.seek(0)
        # Попробуем читать лист 'Questions', иначе первый лист
        try:
            df = pd.read_excel(bio, sheet_name='Questions')
        except Exception:
            bio.seek(0)
            df = pd.read_excel(bio)
    except Exception as e:
        await message.answer(get_text("upload_failed", lang, error=str(e)))
        await state.clear()
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
    except Exception as e:
        await message.answer(get_text("upload_failed", lang, error=str(e)))
    finally:
        await state.clear()


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
            course_id=data.get('course_id'),
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
        await callback.message.edit_text(get_text("test_created", lang, title=data['title']) + "\n" + get_text("send_excel_file", lang))
        await state.set_state(AdminTestCreation.upload_file)
        await callback.answer()
        return

    await callback.message.edit_text(get_text("test_created", lang, title=data['title']))
    await state.clear()
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

    await callback.message.edit_text(
        get_text("choose_test_for_results", lang),
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
    
    await callback.message.edit_text(text, reply_markup=keyboard)
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
