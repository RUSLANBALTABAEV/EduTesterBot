# handlers/start.py
"""
Обработчики команды /start и выбора языка.
"""
from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy import select

from keyboards.reply import main_menu, language_keyboard
from db.models import User
from db.session import async_session
from i18n.locales import get_text

start_router = Router()


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


@start_router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    """
    Обработчик команды /start.
    
    Args:
        message: Входящее сообщение от пользователя
    """
    lang = await get_user_language(message.from_user.id)
    await message.answer(
        get_text("welcome", lang),
        reply_markup=main_menu(message.from_user.id, lang)
    )


@start_router.message(F.text.in_(["Старт", "Start", "Boshlash"]))
async def start_button_handler(message: types.Message) -> None:
    """
    Обработчик кнопки 'Старт' на разных языках.
    
    Args:
        message: Входящее сообщение от пользователя
    """
    lang = await get_user_language(message.from_user.id)
    await message.answer(
        get_text("welcome", lang),
        reply_markup=main_menu(message.from_user.id, lang)
    )


@start_router.message(F.text.in_(["🌐 Язык", "🌐 Language", "🌐 Til"]))
async def language_menu(message: types.Message) -> None:
    """
    Обработчик выбора языка.
    
    Args:
        message: Входящее сообщение от пользователя
    """
    lang = await get_user_language(message.from_user.id)
    await message.answer(
        get_text("choose_language", lang),
        reply_markup=language_keyboard()
    )


@start_router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: types.CallbackQuery) -> None:
    """
    Установить язык пользователя.
    
    Args:
        callback: Callback query с выбранным языком
    """
    new_lang = callback.data.split(":")[1]
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.language = new_lang
            await session.commit()
        else:
            # Создаем временного пользователя только для языка
            temp_user = User(
                user_id=callback.from_user.id,
                language=new_lang,
                is_active=False
            )
            session.add(temp_user)
            await session.commit()
    
    await callback.message.edit_text(get_text("language_changed", new_lang))
    await callback.message.answer(
        get_text("welcome", new_lang),
        reply_markup=main_menu(callback.from_user.id, new_lang)
    )
    await callback.answer()
