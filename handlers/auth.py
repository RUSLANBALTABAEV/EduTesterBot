# handlers/auth.py
"""
Обработчики для авторизации и выхода пользователя.
"""
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select

from db.models import User
from db.session import async_session
from fsm.auth import Auth
from i18n.locales import get_text
from keyboards.reply import main_menu

auth_router = Router()


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


@auth_router.message(Command("login"))
@auth_router.message(
    F.text.in_(["Авторизация", "Authorization", "Kirish"])
)
async def start_auth(message: types.Message, state: FSMContext) -> None:
    """
    Начать процесс авторизации.
    
    Args:
        message: Входящее сообщение
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

    if user and user.is_active:
        await message.answer(get_text("already_logged_in", lang))
        # Показываем главное меню
        await message.answer(
            get_text("welcome", lang),
            reply_markup=main_menu(message.from_user.id, lang)
        )
    else:
        # Создаем клавиатуру с кнопкой отправки номера телефона с локализацией
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=get_text("send_phone_btn", lang), request_contact=True)],
                [KeyboardButton(text=get_text("enter_manual_btn", lang))]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            get_text("auth_instruction", lang),
            reply_markup=keyboard
        )
        await state.set_state(Auth.phone)


@auth_router.message(Auth.phone, F.contact)
async def process_phone_contact(
    message: types.Message,
    state: FSMContext
) -> None:
    """
    Обработать отправленный контакт для авторизации.
    
    Args:
        message: Сообщение с контактом
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)
    
    if message.contact:
        phone = message.contact.phone_number
        await process_phone_number(message, state, phone, lang)


@auth_router.message(Auth.phone, F.text == "✏️ Ввести вручную")
@auth_router.message(Auth.phone, F.text == "✏️ Enter manually")
@auth_router.message(Auth.phone, F.text == "✏️ Qo'lda kiritish")
async def request_manual_phone(
    message: types.Message,
    state: FSMContext
) -> None:
    """
    Запросить ввод номера телефона вручную.
    
    Args:
        message: Входящее сообщение
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)
    await message.answer(
        get_text("enter_phone_manual", lang),
        reply_markup=types.ReplyKeyboardRemove()
    )


@auth_router.message(Auth.phone, F.text.regexp(r"^\+?\d{10,15}$"))
async def process_phone_text(
    message: types.Message,
    state: FSMContext
) -> None:
    """
    Обработать введённый номер телефона для авторизации.
    
    Args:
        message: Сообщение с номером телефона
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)
    await process_phone_number(message, state, message.text.strip(), lang)


async def process_phone_number(
    message: types.Message,
    state: FSMContext,
    phone: str,
    lang: str
) -> None:
    """
    Общая функция обработки номера телефона.
    
    Args:
        message: Сообщение
        state: FSM контекст
        phone: Номер телефона
        lang: Язык пользователя
    """
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.phone == phone)
        )
        user = result.scalar_one_or_none()

        if user:
            if user.user_id and user.is_active:
                await message.answer(
                    get_text("account_already_active", user.language),
                    reply_markup=types.ReplyKeyboardRemove()
                )
                # Показываем главное меню после сообщения
                await message.answer(
                    get_text("welcome", user.language),
                    reply_markup=main_menu(message.from_user.id, user.language)
                )
            else:
                user.user_id = message.from_user.id
                user.is_active = True
                session.add(user)
                await session.commit()
                
                # Используем язык из БД после обновления
                updated_lang = user.language if user.language else "ru"
                await message.answer(
                    get_text("login_success", updated_lang),
                    reply_markup=types.ReplyKeyboardRemove()
                )
                # Показываем главное меню после успешной авторизации
                await message.answer(
                    get_text("welcome", updated_lang),
                    reply_markup=main_menu(message.from_user.id, updated_lang)
                )
        else:
            await message.answer(
                get_text("user_not_found", lang),
                reply_markup=types.ReplyKeyboardRemove()
            )
            # Показываем главное меню после неудачной попытки
            await message.answer(
                get_text("welcome", lang),
                reply_markup=main_menu(message.from_user.id, lang)
            )

    await state.clear()


@auth_router.message(Command("logout"))
@auth_router.message(F.text.in_(["Выход", "Logout", "Chiqish"]))
async def logout(message: types.Message) -> None:
    """
    Выйти из системы (деактивировать пользователя).
    
    Args:
        message: Входящее сообщение
    """
    lang = await get_user_language(message.from_user.id)
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if user and user.is_active:
            user.is_active = False
            session.add(user)
            await session.commit()
            await message.answer(get_text("logout_success", user.language))
            # Показываем главное меню после выхода
            await message.answer(
                get_text("welcome", user.language),
                reply_markup=main_menu(message.from_user.id, user.language)
            )
        else:
            await message.answer(get_text("not_authorized", lang))
