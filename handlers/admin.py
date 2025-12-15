# handlers/admin.py
"""
Обработчики административной панели бота.
Управление пользователями, курсами и сертификатами.
"""
from datetime import datetime

from aiogram import Router, F
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message
)
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select

from db.models import User, Course, Certificate
from db.session import async_session
from config.bot_config import ADMIN_ID
from keyboards.reply import admin_main_keyboard, admin_back_keyboard
from i18n.locales import get_text, MIN_CERTIFICATE_TITLE_LENGTH

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


class CertificateFSM(StatesGroup):
    """Состояния для выдачи сертификата."""

    user_selector = State()
    title = State()
    file = State()


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
    await message.answer(
        get_text("admin_main_menu", lang),
        reply_markup=admin_main_keyboard(lang)
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
        lang = await get_user_language(callback.from_user.id)
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    lang = await get_user_language(callback.from_user.id)

    try:
        await callback.message.edit_text(
            get_text("admin_main_menu", lang),
            reply_markup=admin_main_keyboard(lang)
        )
    except Exception:
        await callback.message.answer(
            get_text("admin_main_menu", lang),
            reply_markup=admin_main_keyboard(lang)
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
        lang = await get_user_language(callback.from_user.id)
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    lang = await get_user_language(callback.from_user.id)

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

    if not users:
        try:
            await callback.message.edit_text(
                get_text("no_users", lang),
                reply_markup=admin_back_keyboard(lang)
            )
        except Exception:
            await callback.message.answer(
                get_text("no_users", lang),
                reply_markup=admin_back_keyboard(lang)
            )
        await callback.answer()
        return

    for user in users:
        user_name = user.name or get_text("without_name", lang)
        phone = user.phone or get_text("not_specified", lang)
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
                        text=get_text("btn_delete", lang),
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
        get_text("btn_admin_back", lang),
        reply_markup=admin_back_keyboard(lang)
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
        lang = await get_user_language(callback.from_user.id)
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    lang = await get_user_language(callback.from_user.id)
    user_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            await callback.answer(
                get_text("user_not_found", lang),
                show_alert=True
            )
            return

        username = user.name or get_text("without_name", lang)
        telegram_id = user.user_id or get_text("unknown", lang)

        await session.delete(user)
        await session.commit()

    try:
        message_text = get_text(
            "user_deleted",
            lang,
            name=username,
            telegram_id=telegram_id
        )
        await callback.message.answer(
            message_text,
            reply_markup=admin_back_keyboard(lang)
        )
        await callback.message.delete()
    except Exception:
        message_text = get_text(
            "user_deleted",
            lang,
            name=username,
            telegram_id=telegram_id
        )
        await callback.answer(message_text, show_alert=True)

    await callback.answer()


@admin_router.callback_query(F.data == "delete_all_users")
async def delete_all_users(callback: CallbackQuery) -> None:
    """
    Удалить всех пользователей.

    Args:
        callback: Callback query
    """
    if callback.from_user.id != ADMIN_ID:
        lang = await get_user_language(callback.from_user.id)
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    lang = await get_user_language(callback.from_user.id)

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        if not users:
            await callback.answer(
                get_text("no_users_to_delete", lang),
                show_alert=True
            )
            return

        for user in users:
            await session.delete(user)
        await session.commit()

    try:
        await callback.message.answer(
            get_text("all_users_deleted", lang),
            reply_markup=admin_back_keyboard(lang)
        )
        await callback.message.delete()
    except Exception:
        await callback.answer(
            get_text("all_users_deleted", lang),
            show_alert=True
        )

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
        lang = await get_user_language(callback.from_user.id)
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    lang = await get_user_language(callback.from_user.id)

    async with async_session() as session:
        result = await session.execute(select(Course))
        courses = result.scalars().all()

    if not courses:
        try:
            await callback.message.edit_text(
                get_text("no_courses", lang),
                reply_markup=admin_back_keyboard(lang)
            )
        except Exception:
            await callback.message.answer(
                get_text("no_courses", lang),
                reply_markup=admin_back_keyboard(lang)
            )
        await callback.answer()
        return

    for course in courses:
        start_date = (
            course.start_date.strftime("%d.%m.%Y")
            if course.start_date
            else get_text("not_indicated", lang)
        )
        end_date = (
            course.end_date.strftime("%d.%m.%Y")
            if course.end_date
            else get_text("not_indicated", lang)
        )

        text = (
            f"📘 <b>{course.title}</b>\n\n"
            f"{course.description or get_text('no_description', lang)}\n\n"
            f"{get_text('price', lang, price=course.price)}\n"
            f"{get_text('dates', lang, start=start_date, end=end_date)}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=get_text("btn_edit", lang),
                        callback_data=f"edit_course:{course.id}"
                    ),
                    InlineKeyboardButton(
                        text=get_text("btn_delete", lang),
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
        get_text("btn_admin_back", lang),
        reply_markup=admin_back_keyboard(lang)
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
        lang = await get_user_language(callback.from_user.id)
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    lang = await get_user_language(callback.from_user.id)
    course_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        course = await session.get(Course, course_id)
        if not course:
            await callback.answer(
                get_text("course_not_found", lang),
                show_alert=True
            )
            return

        course_title = course.title
        await session.delete(course)
        await session.commit()

    try:
        await callback.message.answer(
            get_text("course_deleted", lang, title=course_title),
            reply_markup=admin_back_keyboard(lang)
        )
        await callback.message.delete()
    except Exception:
        await callback.answer(
            get_text("course_deleted", lang, title=course_title),
            show_alert=True
        )

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
        lang = await get_user_language(callback.from_user.id)
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    lang = await get_user_language(callback.from_user.id)

    await state.set_state(AddCourseFSM.title)

    try:
        await callback.message.edit_text(
            get_text("enter_course_title", lang)
        )
    except Exception:
        await callback.message.answer(
            get_text("enter_course_title", lang)
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

    lang = await get_user_language(message.from_user.id)

    # Проверяем уникальность названия
    async with async_session() as session:
        result = await session.execute(
            select(Course).where(Course.title == message.text.strip())
        )
        existing = result.scalar_one_or_none()

        if existing:
            await message.answer(get_text("course_title_exists", lang))
            return

    await state.update_data(title=message.text.strip())
    await state.set_state(AddCourseFSM.description)
    await message.answer(get_text("enter_course_description", lang))


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

    lang = await get_user_language(message.from_user.id)
    await state.update_data(description=message.text.strip())
    await state.set_state(AddCourseFSM.price)
    await message.answer(get_text("enter_course_price", lang))


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

    lang = await get_user_language(message.from_user.id)
    await state.update_data(price=int(message.text.strip()))
    await state.set_state(AddCourseFSM.start_date)
    await message.answer(get_text("enter_start_date", lang))


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

    lang = await get_user_language(message.from_user.id)

    try:
        start_date = datetime.strptime(
            message.text.strip(),
            "%d.%m.%Y"
        ).date()
    except ValueError:
        await message.answer(get_text("invalid_date_format", lang))
        return

    await state.update_data(start_date=start_date)
    await state.set_state(AddCourseFSM.end_date)
    await message.answer(get_text("enter_end_date", lang))


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

    lang = await get_user_language(message.from_user.id)
    data = await state.get_data()

    try:
        end_date = datetime.strptime(
            message.text.strip(),
            "%d.%m.%Y"
        ).date()
    except ValueError:
        await message.answer(get_text("invalid_date_format", lang))
        return

    if end_date < data["start_date"]:
        await message.answer(get_text("end_date_before_start", lang))
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
        get_text("course_added", lang, title=data["title"]),
        reply_markup=admin_back_keyboard(lang)
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
        lang = await get_user_language(callback.from_user.id)
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    lang = await get_user_language(callback.from_user.id)
    course_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        course = await session.get(Course, course_id)
        if not course:
            await callback.answer(
                get_text("course_not_found", lang),
                show_alert=True
            )
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

    lang = await get_user_language(message.from_user.id)

    try:
        start_date = datetime.strptime(
            message.text.strip(),
            "%d.%m.%Y"
        ).date()
    except ValueError:
        await message.answer(get_text("invalid_date_format", lang))
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

    lang = await get_user_language(message.from_user.id)
    data = await state.get_data()

    try:
        end_date = datetime.strptime(
            message.text.strip(),
            "%d.%m.%Y"
        ).date()
    except ValueError:
        await message.answer(get_text("invalid_date_format", lang))
        return

    if end_date < data["new_start_date"]:
        await message.answer(get_text("end_date_before_start", lang))
        return

    # Обновляем курс в базе данных
    course_id = data["course_id"]
    async with async_session() as session:
        course = await session.get(Course, course_id)
        if not course:
            await message.answer(get_text("course_not_found", lang))
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
            await message.answer(get_text("course_title_exists", lang))
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
        reply_markup=admin_back_keyboard(lang)
    )
    await state.clear()


# ============ Выдача сертификатов ============
@admin_router.callback_query(F.data == "add_certificate")
async def add_certificate_start(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """
    Начать процесс выдачи сертификата.

    Args:
        callback: Callback query
        state: FSM контекст
    """
    if callback.from_user.id != ADMIN_ID:
        lang = await get_user_language(callback.from_user.id)
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    lang = await get_user_language(callback.from_user.id)

    # Получаем список всех пользователей
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

    if not users:
        await callback.answer(
            get_text("no_users", lang),
            show_alert=True
        )
        return

    # Создаем клавиатуру с пользователями
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(
                        f"{user.name or 'ID: ' + str(user.id)} "
                        f"({user.phone or 'без телефона'})"
                    ),
                    callback_data=f"cert_user:{user.id}"
                )
            ]
            for user in users
        ] + [
            [
                InlineKeyboardButton(
                    text=get_text("btn_back", lang),
                    callback_data="admin_menu"
                )
            ]
        ]
    )

    try:
        await callback.message.edit_text(
            "👥 Выберите пользователя для выдачи сертификата:",
            reply_markup=keyboard
        )
    except Exception:
        await callback.message.answer(
            "👥 Выберите пользователя для выдачи сертификата:",
            reply_markup=keyboard
        )

    await state.set_state(CertificateFSM.user_selector)
    await callback.answer()


@admin_router.callback_query(
    F.data.startswith("cert_user:"),
    CertificateFSM.user_selector
)
async def certificate_user_selected(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """
    Обработать выбор пользователя для сертификата.

    Args:
        callback: Callback query с ID пользователя
        state: FSM контекст
    """
    if callback.from_user.id != ADMIN_ID:
        return

    user_id = int(callback.data.split(":")[1])

    # Сохраняем ID пользователя
    await state.update_data(selected_user_id=user_id)
    await state.set_state(CertificateFSM.title)

    try:
        await callback.message.edit_text(
            "📝 Введите название сертификата:"
        )
    except Exception:
        await callback.message.answer(
            "📝 Введите название сертификата:"
        )

    await callback.answer()


@admin_router.message(CertificateFSM.title)
async def certificate_title_entered(
    message: Message,
    state: FSMContext
) -> None:
    """
    Обработать название сертификата.

    Args:
        message: Сообщение с названием
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    title = message.text.strip()

    if len(title) < MIN_CERTIFICATE_TITLE_LENGTH:
        await message.answer(
            "⚠️ Название сертификата должно содержать минимум 3 символа."
        )
        return

    await state.update_data(certificate_title=title)
    await state.set_state(CertificateFSM.file)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Без файла",
                    callback_data="cert_no_file"
                )
            ]
        ]
    )

    await message.answer(
        "📄 Отправьте файл сертификата (документ) "
        "или нажмите 'Без файла' чтобы создать сертификат без файла:",
        reply_markup=keyboard
    )


@admin_router.callback_query(F.data == "cert_no_file", CertificateFSM.file)
async def certificate_no_file(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """
    Создать сертификат без файла.

    Args:
        callback: Callback query
        state: FSM контекст
    """
    if callback.from_user.id != ADMIN_ID:
        return

    await create_certificate(callback.message, state, file_id=None)
    await callback.answer()


@admin_router.message(
    CertificateFSM.file,
    F.content_type == ContentType.DOCUMENT
)
async def certificate_file_received(
    message: Message,
    state: FSMContext
) -> None:
    """
    Обработать файл сертификата.

    Args:
        message: Сообщение с документом
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    await create_certificate(
        message,
        state,
        file_id=message.document.file_id
    )


async def create_certificate(
    message: Message,
    state: FSMContext,
    file_id: str = None
) -> None:
    """
    Создать сертификат и отправить уведомление пользователю.

    Args:
        message: Сообщение для ответа
        state: FSM контекст
        file_id: File ID документа сертификата (опционально)
    """
    lang = await get_user_language(message.from_user.id)
    data = await state.get_data()

    user_id = data.get("selected_user_id")
    title = data.get("certificate_title")

    if not user_id or not title:
        await message.answer(
            "⚠️ Ошибка: данные не найдены. Попробуйте снова."
        )
        await state.clear()
        return

    async with async_session() as session:
        # Проверяем, существует ли пользователь
        user = await session.get(User, user_id)
        if not user:
            await message.answer("⚠️ Пользователь не найден.")
            await state.clear()
            return

        # Создаем сертификат
        certificate = Certificate(
            user_id=user_id,
            title=title,
            file_id=file_id
        )

        session.add(certificate)
        await session.commit()

        # Уведомляем пользователя
        if user.user_id:
            try:
                notification_text = (
                    f"🏅 Поздравляем! Вам выдан сертификат:\n\n"
                    f"<b>{title}</b>"
                )

                await message.bot.send_message(
                    user.user_id,
                    notification_text,
                    parse_mode="HTML"
                )

                # Если есть файл, отправляем его
                if file_id:
                    try:
                        await message.bot.send_document(
                            user.user_id,
                            file_id,
                            caption="📄 Ваш сертификат"
                        )
                    except Exception as e:
                        print(
                            f"Ошибка при отправке файла сертификата: {e}"
                        )

            except Exception as e:
                print(f"Ошибка при уведомлении пользователя: {e}")

    # Подтверждение админу
    confirmation_text = (
        f"✅ Сертификат «{title}» выдан пользователю "
        f"{user.name or 'ID: ' + str(user.id)}"
    )
    if file_id:
        confirmation_text += " с файлом"

    await message.answer(
        confirmation_text,
        reply_markup=admin_back_keyboard(lang)
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


@admin_router.message(CertificateFSM.file)
async def invalid_certificate_file(
    message: Message,
    state: FSMContext
) -> None:
    """
    Обработать неправильный формат файла сертификата.

    Args:
        message: Входящее сообщение
        state: FSM контекст
    """
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "⚠️ Отправьте файл как документ или нажмите 'Без файла'"
    )
