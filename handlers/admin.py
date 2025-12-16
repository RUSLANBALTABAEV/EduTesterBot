# handlers/admin.py
"""
Обработчики административной панели бота.
Управление пользователями, курсами.
"""
from datetime import datetime

from aiogram import Router, F
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select

from db.models import User, Course
from db.session import async_session
from config.bot_config import ADMIN_ID
from i18n.locales import get_text

admin_router = Router()


async def get_user_language(user_id: int) -> str:
    """
    Получить язык пользователя из БД.

    Args:
        user_id: Telegram ID пользователя

    Returns:
        Код языка (ru/en/uz), по умолчанию 'ru'
    """
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user.language if user and user.language else "ru"


# ============ FSM классы ============
class AddCourseFSM(StatesGroup):
    """Состояния для добавления курса."""

    title = State()
    description = State()
    price = State()
    start_date = State()
    end_date = State()


class EditCourseFSM(StatesGroup):
    """Состояния для редактирования курса."""

    course_id = State()
    title = State()
    description = State()
    price = State()
    start_date = State()
    end_date = State()


# ============ Админ-меню ============
@admin_router.message(
    F.text.in_([
        "Управление курсами и пользователями",
        "Manage Courses and Users",
        "Kurs va foydalanuvchilarni boshqarish"
    ])
)
async def admin_main_menu(message: Message) -> None:
    """
    Показать главное меню администратора.

    Args:
        message: Входящее сообщение
    """
    if message.from_user.id != ADMIN_ID:
        lang = await get_user_language(message.from_user.id)
        await message.answer(get_text("no_access", lang))
        return

    lang = await get_user_language(message.from_user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Список пользователей", callback_data="show_users")],
        [InlineKeyboardButton(text="📚 Управление курсами", callback_data="manage_courses")],
        [InlineKeyboardButton(text="➕ Добавить курс", callback_data="add_course")],
        [InlineKeyboardButton(text="🗑 Удалить всех пользователей", callback_data="delete_all_users")],
        [InlineKeyboardButton(text="📋 Управление тестами", callback_data="manage_tests")]
    ])
    
    await message.answer(
        "👤 Главное меню администратора:",
        reply_markup=keyboard
    )


@admin_router.callback_query(F.data == "admin_menu")
async def back_to_admin_menu(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """
    Вернуться в главное меню администратора.

    Args:
        callback: Callback query
        state: FSM контекст
    """
    await state.clear()

    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Список пользователей", callback_data="show_users")],
        [InlineKeyboardButton(text="📚 Управление курсами", callback_data="manage_courses")],
        [InlineKeyboardButton(text="➕ Добавить курс", callback_data="add_course")],
        [InlineKeyboardButton(text="🗑 Удалить всех пользователей", callback_data="delete_all_users")],
        [InlineKeyboardButton(text="📋 Управление тестами", callback_data="manage_tests")]
    ])

    try:
        await callback.message.edit_text(
            "👤 Главное меню администратора:",
            reply_markup=keyboard
        )
    except Exception:
        await callback.message.answer(
            "👤 Главное меню администратора:",
            reply_markup=keyboard
        )

    await callback.answer()


# ============ Управление пользователями ============
@admin_router.callback_query(F.data == "show_users")
async def show_users(callback: CallbackQuery) -> None:
    """
    Показать список всех пользователей.

    Args:
        callback: Callback query
    """
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

    if not users:
        try:
            await callback.message.edit_text(
                "📭 Пользователей пока нет.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
                ])
            )
        except Exception:
            await callback.message.answer(
                "📭 Пользователей пока нет.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
                ])
            )
        await callback.answer()
        return

    for user in users:
        user_name = user.name or "Без имени"
        phone = user.phone or "не указан"
        text = (
            f"👤 {user_name}\n"
            f"🆔 Telegram ID: {user.user_id}\n"
            f"🗄 DB ID: {user.id}\n"
            f"📱 {phone}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗑 Удалить",
                        callback_data=f"delete_user:{user.id}"
                    )
                ]
            ]
        )

        try:
            if user.photo:
                await callback.message.answer_photo(
                    photo=user.photo,
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await callback.message.answer(text, reply_markup=keyboard)
        except Exception:
            error_text = text + "\n\n⚠️ Не удалось отправить фото."
            await callback.message.answer(
                error_text,
                reply_markup=keyboard
            )

    await callback.message.answer(
        "🔙 Назад",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ])
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("delete_user:"))
async def delete_user(callback: CallbackQuery) -> None:
    """
    Удалить пользователя.

    Args:
        callback: Callback query с ID пользователя
    """
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            await callback.answer("⚠️ Пользователь не найден", show_alert=True)
            return

        username = user.name or "Без имени"
        telegram_id = user.user_id or "неизвестный"

        await session.delete(user)
        await session.commit()

    try:
        await callback.message.answer(
            f"🗑 Пользователь «{username}» (TG ID: {telegram_id}) удалён.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
            ])
        )
        await callback.message.delete()
    except Exception:
        await callback.answer(f"🗑 Пользователь «{username}» удалён.", show_alert=True)

    await callback.answer()


@admin_router.callback_query(F.data == "delete_all_users")
async def delete_all_users(callback: CallbackQuery) -> None:
    """
    Удалить всех пользователей.

    Args:
        callback: Callback query
    """
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        if not users:
            await callback.answer("⚠️ Пользователей нет.", show_alert=True)
            return

        for user in users:
            await session.delete(user)
        await session.commit()

    try:
        await callback.message.answer(
            "🗑 Все пользователи удалены.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
            ])
        )
        await callback.message.delete()
    except Exception:
        await callback.answer("🗑 Все пользователи удалены.", show_alert=True)

    await callback.answer()


# ============ Управление курсами ============
@admin_router.callback_query(F.data == "manage_courses")
async def manage_courses(callback: CallbackQuery) -> None:
    """
    Показать список всех курсов для управления.

    Args:
        callback: Callback query
    """
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(Course))
        courses = result.scalars().all()

    if not courses:
        try:
            await callback.message.edit_text(
                "📭 Курсов пока нет.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
                ])
            )
        except Exception:
            await callback.message.answer(
                "📭 Курсов пока нет.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
                ])
            )
        await callback.answer()
        return

    for course in courses:
        start_date = (
            course.start_date.strftime("%d.%m.%Y")
            if course.start_date
            else "не указана"
        )
        end_date = (
            course.end_date.strftime("%d.%m.%Y")
            if course.end_date
            else "не указана"
        )

        text = (
            f"📘 <b>{course.title}</b>\n\n"
            f"{course.description or 'Без описания'}\n\n"
            f"💰 Цена: {course.price} сум.\n"
            f"📅 Даты: {start_date} — {end_date}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ Редактировать",
                        callback_data=f"edit_course:{course.id}"
                    ),
                    InlineKeyboardButton(
                        text="🗑 Удалить",
                        callback_data=f"delete_course:{course.id}"
                    )
                ]
            ]
        )

        await callback.message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    await callback.message.answer(
        "🔙 Назад",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ])
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("delete_course:"))
async def delete_course(callback: CallbackQuery) -> None:
    """
    Удалить курс.

    Args:
        callback: Callback query с ID курса
    """
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    course_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        course = await session.get(Course, course_id)
        if not course:
            await callback.answer("⚠️ Курс не найден", show_alert=True)
            return

        course_title = course.title
        await session.delete(course)
        await session.commit()

    try:
        await callback.message.answer(
            f"🗑 Курс «{course_title}» удалён.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
            ])
        )
        await callback.message.delete()
    except Exception:
        await callback.answer(f"🗑 Курс «{course_title}» удалён.", show_alert=True)

    await callback.answer()


# ============ Добавление курса ============
@admin_router.callback_query(F.data == "add_course")
async def add_course_start(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """
    Начать процесс добавления курса.

    Args:
        callback: Callback query
        state: FSM контекст
    """
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    await state.set_state(AddCourseFSM.title)

    try:
        await callback.message.edit_text(
            "➕ Введите название нового курса:"
        )
    except Exception:
        await callback.message.answer(
            "➕ Введите название нового курса:"
        )

    await callback.answer()


@admin_router.message(AddCourseFSM.title)
async def add_course_title(message: Message, state: FSMContext) -> None:
    """
    Обработать название нового курса.

    Args:
        message: Сообщение с названием
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    # Проверяем уникальность названия
    async with async_session() as session:
        result = await session.execute(
            select(Course).where(Course.title == message.text.strip())
        )
        existing = result.scalar_one_or_none()

        if existing:
            await message.answer("⚠️ Курс с таким названием уже существует!")
            return

    await state.update_data(title=message.text.strip())
    await state.set_state(AddCourseFSM.description)
    await message.answer("Введите описание курса:")


@admin_router.message(AddCourseFSM.description)
async def add_course_description(
    message: Message,
    state: FSMContext
) -> None:
    """
    Обработать описание нового курса.

    Args:
        message: Сообщение с описанием
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(description=message.text.strip())
    await state.set_state(AddCourseFSM.price)
    await message.answer("Введите цену курса (число):")


@admin_router.message(AddCourseFSM.price, F.text.regexp(r"^\d+$"))
async def add_course_price(message: Message, state: FSMContext) -> None:
    """
    Обработать цену нового курса.

    Args:
        message: Сообщение с ценой
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(price=int(message.text.strip()))
    await state.set_state(AddCourseFSM.start_date)
    await message.answer("Введите дату начала курса (ДД.ММ.ГГГГ):")


@admin_router.message(AddCourseFSM.start_date)
async def add_course_start_date(
    message: Message,
    state: FSMContext
) -> None:
    """
    Обработать дату начала нового курса.

    Args:
        message: Сообщение с датой
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    try:
        start_date = datetime.strptime(
            message.text.strip(),
            "%d.%m.%Y"
        )
    except ValueError:
        await message.answer("⚠️ Неверный формат даты. Введите снова (ДД.ММ.ГГГГ):")
        return

    await state.update_data(start_date=start_date)
    await state.set_state(AddCourseFSM.end_date)
    await message.answer("Введите дату окончания курса (ДД.ММ.ГГГГ):")


@admin_router.message(AddCourseFSM.end_date)
async def add_course_end_date(
    message: Message,
    state: FSMContext
) -> None:
    """
    Обработать дату окончания и завершить добавление курса.

    Args:
        message: Сообщение с датой
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()

    try:
        end_date = datetime.strptime(
            message.text.strip(),
            "%d.%m.%Y"
        )
    except ValueError:
        await message.answer("⚠️ Неверный формат даты. Введите снова (ДД.ММ.ГГГГ):")
        return

    if end_date < data["start_date"]:
        await message.answer("⚠️ Дата окончания не может быть раньше даты начала.")
        return

    # Создаем новый курс
    async with async_session() as session:
        new_course = Course(
            title=data["title"],
            description=data["description"],
            price=data["price"],
            start_date=data["start_date"],
            end_date=end_date
        )
        session.add(new_course)
        await session.commit()

    await message.answer(
        f"✅ Курс «{data['title']}» добавлен!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ])
    )
    await state.clear()


# ============ Редактирование курса ============
@admin_router.callback_query(F.data.startswith("edit_course:"))
async def edit_course_start(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """
    Начать процесс редактирования курса.

    Args:
        callback: Callback query с ID курса
        state: FSM контекст
    """
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    course_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        course = await session.get(Course, course_id)
        if not course:
            await callback.answer("⚠️ Курс не найден", show_alert=True)
            return

    await state.update_data(course_id=course_id)
    await state.set_state(EditCourseFSM.title)

    edit_text = (
        f"✏️ Редактирование курса «{course.title}»\n\n"
        f"Введите новое название курса (текущее: {course.title}):"
    )

    try:
        await callback.message.edit_text(edit_text)
    except Exception:
        await callback.message.answer(edit_text)

    await callback.answer()


@admin_router.message(EditCourseFSM.title)
async def edit_course_title(message: Message, state: FSMContext) -> None:
    """
    Обработать новое название курса.

    Args:
        message: Сообщение с названием
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(new_title=message.text.strip())
    await state.set_state(EditCourseFSM.description)
    await message.answer("Введите новое описание курса:")


@admin_router.message(EditCourseFSM.description)
async def edit_course_description(
    message: Message,
    state: FSMContext
) -> None:
    """
    Обработать новое описание курса.

    Args:
        message: Сообщение с описанием
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(new_description=message.text.strip())
    await state.set_state(EditCourseFSM.price)
    await message.answer("Введите новую цену курса:")


@admin_router.message(EditCourseFSM.price, F.text.regexp(r"^\d+$"))
async def edit_course_price(message: Message, state: FSMContext) -> None:
    """
    Обработать новую цену курса.

    Args:
        message: Сообщение с ценой
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(new_price=int(message.text.strip()))
    await state.set_state(EditCourseFSM.start_date)
    await message.answer(
        "Введите новую дату начала курса (ДД.ММ.ГГГГ):"
    )


@admin_router.message(EditCourseFSM.start_date)
async def edit_course_start_date(
    message: Message,
    state: FSMContext
) -> None:
    """
    Обработать новую дату начала курса.

    Args:
        message: Сообщение с датой
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    try:
        start_date = datetime.strptime(
            message.text.strip(),
            "%d.%m.%Y"
        )
    except ValueError:
        await message.answer("⚠️ Неверный формат даты. Введите снова (ДД.ММ.ГГГГ):")
        return

    await state.update_data(new_start_date=start_date)
    await state.set_state(EditCourseFSM.end_date)
    await message.answer(
        "Введите новую дату окончания курса (ДД.ММ.ГГГГ):"
    )


@admin_router.message(EditCourseFSM.end_date)
async def edit_course_end_date(
    message: Message,
    state: FSMContext
) -> None:
    """
    Обработать новую дату окончания и завершить редактирование.

    Args:
        message: Сообщение с датой
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()

    try:
        end_date = datetime.strptime(
            message.text.strip(),
            "%d.%m.%Y"
        )
    except ValueError:
        await message.answer("⚠️ Неверный формат даты. Введите снова (ДД.ММ.ГГГГ):")
        return

    if end_date < data["new_start_date"]:
        await message.answer("⚠️ Дата окончания не может быть раньше даты начала.")
        return

    # Обновляем курс в базе данных
    course_id = data["course_id"]
    async with async_session() as session:
        course = await session.get(Course, course_id)
        if not course:
            await message.answer("⚠️ Курс не найден")
            await state.clear()
            return

        # Проверяем, не существует ли курса с таким названием
        result = await session.execute(
            select(Course).where(
                Course.title == data["new_title"],
                Course.id != course_id
            )
        )
        existing_course = result.scalar_one_or_none()

        if existing_course:
            await message.answer("⚠️ Курс с таким названием уже существует!")
            await state.clear()
            return

        # Обновляем данные курса
        course.title = data["new_title"]
        course.description = data["new_description"]
        course.price = data["new_price"]
        course.start_date = data["new_start_date"]
        course.end_date = end_date

        await session.commit()

    await message.answer(
        f"✅ Курс «{data['new_title']}» успешно обновлён!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ])
    )
    await state.clear()


# ============ Обработка неправильных состояний ============
@admin_router.message(AddCourseFSM.price)
async def invalid_add_price(message: Message, state: FSMContext) -> None:
    """
    Обработать неправильный формат цены при добавлении курса.

    Args:
        message: Входящее сообщение
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("⚠️ Введите корректную цену (только цифры):")


@admin_router.message(EditCourseFSM.price)
async def invalid_edit_price(message: Message, state: FSMContext) -> None:
    """
    Обработать неправильный формат цены при редактировании курса.

    Args:
        message: Входящее сообщение
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("⚠️ Введите корректную цену (только цифры):")
