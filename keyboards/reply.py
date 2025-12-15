# keyboards/reply.py
"""
Модуль клавиатур для бота.
Содержит функции для создания reply и inline клавиатур.
"""
from aiogram.types import (
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config.bot_config import ADMIN_ID
from i18n.locales import get_text, AVAILABLE_LANGUAGES


def _is_admin(user_id: int) -> bool:
    """
    Проверить, является ли пользователь администратором.
    
    Args:
        user_id: Telegram ID пользователя
        
    Returns:
        True, если пользователь администратор, иначе False
    """
    try:
        if isinstance(ADMIN_ID, (list, tuple, set)):
            return int(user_id) in [int(x) for x in ADMIN_ID]
        return int(user_id) == int(ADMIN_ID)
    except (ValueError, TypeError):
        return False


def main_menu(user_id: int, lang: str = "ru") -> ReplyKeyboardMarkup:
    """
    Создать главное меню для пользователя.
    
    Меню отличается для администраторов и обычных пользователей.
    
    Args:
        user_id: Telegram ID пользователя
        lang: Код языка интерфейса
        
    Returns:
        ReplyKeyboardMarkup с кнопками главного меню
    """
    builder = ReplyKeyboardBuilder()

    # Добавляем кнопку "Старт" в начало
    builder.row(KeyboardButton(text=get_text("btn_start", lang)))

    # Основные кнопки для всех
    builder.row(KeyboardButton(text=get_text("btn_registration", lang)))
    builder.row(KeyboardButton(text=get_text("btn_auth", lang)))
    builder.row(KeyboardButton(text=get_text("btn_courses", lang)))

    if _is_admin(user_id):
        # Кнопки для администратора
        builder.row(
            KeyboardButton(text=get_text("btn_admin_certificates", lang))
        )
        builder.row(
            KeyboardButton(text=get_text("btn_admin_panel", lang))
        )
    else:
        # Кнопки для обычного пользователя
        builder.row(
            KeyboardButton(text=get_text("btn_my_courses", lang))
        )
        builder.row(
            KeyboardButton(text=get_text("btn_certificates", lang))
        )

    builder.row(KeyboardButton(text=get_text("btn_language", lang)))
    builder.row(KeyboardButton(text=get_text("btn_logout", lang)))
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def language_keyboard() -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для выбора языка.
    
    Returns:
        InlineKeyboardMarkup с кнопками выбора языка
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=name,
                    callback_data=f"lang:{code}"
                )
            ]
            for code, name in AVAILABLE_LANGUAGES.items()
        ]
    )
    return keyboard


def admin_main_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Создать главную клавиатуру администратора.
    
    Args:
        lang: Код языка интерфейса
        
    Returns:
        InlineKeyboardMarkup с кнопками администратора
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("btn_show_users", lang),
                    callback_data="show_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text("btn_manage_courses", lang),
                    callback_data="manage_courses"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text("btn_add_course", lang),
                    callback_data="add_course"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text("btn_add_certificate", lang),
                    callback_data="add_certificate"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text("btn_delete_all_users", lang),
                    callback_data="delete_all_users"
                )
            ],
        ]
    )


def admin_back_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Создать клавиатуру возврата в меню администратора.
    
    Args:
        lang: Код языка интерфейса
        
    Returns:
        InlineKeyboardMarkup с кнопкой возврата
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("btn_admin_back", lang),
                    callback_data="admin_menu"
                )
            ]
        ]
    )
