# handlers/admin.py
"""
Обработчики административной панели бота.
Управление пользователями и тестами.
"""
from aiogram import Router, F
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message
)
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from db.models import User
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
        return user.language if user and user.language else None


# ============ Админ-меню ============
@admin_router.message(
    F.text.in_([
        "Управление тестами",
        "Manage Tests",
        "Testlarni boshqarish"
    ])
)
async def admin_main_menu(message: Message) -> None:
    """
    Показать главное меню администратора.

    Args:
        message: Входящее сообщение
    """
    lang = await get_user_language(message.from_user.id)

    if message.from_user.id != ADMIN_ID:
        await message.answer(get_text("no_access", lang))
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("btn_show_users", lang), callback_data="show_users")],
        [InlineKeyboardButton(text=get_text("btn_manage_tests", lang), callback_data="manage_tests")],
        [InlineKeyboardButton(text=get_text("btn_delete_all_users", lang), callback_data="delete_all_users")]
    ])

    await message.answer(
        get_text("admin_main_title", lang),
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

    lang = await get_user_language(callback.from_user.id)

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("btn_show_users", lang), callback_data="show_users")],
        [InlineKeyboardButton(text=get_text("btn_manage_tests", lang), callback_data="manage_tests")],
        [InlineKeyboardButton(text=get_text("btn_delete_all_users", lang), callback_data="delete_all_users")]
    ])

    try:
        await callback.message.edit_text(
            get_text("admin_main_title", lang),
            reply_markup=keyboard
        )
    except TelegramBadRequest:
        await callback.message.answer(
            get_text("admin_main_title", lang),
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
    lang = await get_user_language(callback.from_user.id)

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

    if not users:
        try:
            await callback.message.edit_text(
                get_text("users_empty", lang),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin_menu")]
                ])
            )
        except TelegramBadRequest:
            await callback.message.answer(
                get_text("users_empty", lang),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin_menu")]
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
        except TelegramBadRequest:
            error_text = text + "\n\n⚠️ Не удалось отправить фото."
            await callback.message.answer(
                error_text,
                reply_markup=keyboard
            )

    await callback.message.answer(
        get_text("btn_back", lang),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin_menu")]
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
    lang = await get_user_language(callback.from_user.id)

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            await callback.answer(get_text("test_not_found", lang), show_alert=True)
            return

        username = user.name or get_text("without_name", lang)
        telegram_id = user.user_id or get_text("unknown", lang)

        await session.delete(user)
        await session.commit()

    try:
        await callback.message.answer(
            get_text("user_deleted", lang, name=username),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin_menu")]
            ])
        )
        await callback.message.delete()
    except TelegramBadRequest:
        await callback.answer(get_text("user_deleted", lang, name=username), show_alert=True)

    await callback.answer()


@admin_router.callback_query(F.data == "delete_all_users")
async def delete_all_users(callback: CallbackQuery) -> None:
    """
    Удалить всех пользователей.

    Args:
        callback: Callback query
    """
    lang = await get_user_language(callback.from_user.id)

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(get_text("no_access", lang), show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        if not users:
            await callback.answer(get_text("users_empty", lang), show_alert=True)
            return

        for user in users:
            await session.delete(user)
        await session.commit()

    try:
        await callback.message.answer(
            get_text("all_users_deleted", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="admin_menu")]
            ])
        )
        await callback.message.delete()
    except TelegramBadRequest:
        await callback.answer(get_text("all_users_deleted", lang), show_alert=True)

    await callback.answer()
