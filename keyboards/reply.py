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

    if _is_admin(user_id):
        # Кнопки для администратора
        builder.row(
            KeyboardButton(text=get_text("btn_admin_panel", lang))
        )
    else:
        # Кнопки для обычного пользователя: доступ к тестированию
        builder.row(KeyboardButton(text=get_text("btn_tests", lang)))
        builder.row(KeyboardButton(text=get_text("btn_my_tests", lang)))
        builder.row(KeyboardButton(text=get_text("btn_my_results", lang)))

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
