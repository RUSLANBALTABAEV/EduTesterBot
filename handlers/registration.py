# handlers/registration.py
"""
Обработчики для регистрации пользователей.
"""
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from db.models import User
from db.session import async_session
from fsm.registration import Registration
from config.bot_config import ADMIN_ID
from i18n.locales import get_text
from keyboards.reply import main_menu  # Добавляем импорт

registration_router = Router()


async def get_user_language(user_id: int) -> str:
    """Получить язык пользователя."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user.language if user and user.language else "ru"


@registration_router.message(
    F.text.in_(["Регистрация", "Registration", "Ro'yxatdan o'tish"])
)
async def start_registration(message: types.Message, state: FSMContext) -> None:
    """
    Начать процесс регистрации.
    
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
        name = user.name or get_text("without_name", lang)
        phone = user.phone or get_text("not_specified", lang)
        await message.answer(
            get_text("already_registered", lang, name=name, phone=phone)
        )
    else:
        await message.answer(get_text("enter_name", lang))
        await state.set_state(Registration.name)


@registration_router.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext) -> None:
    """
    Обработать введённое имя.
    
    Args:
        message: Сообщение с именем
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)
    
    if len(message.text.strip()) < 2:
        await message.answer(get_text("enter_name", lang))
        return
        
    await state.update_data(name=message.text.strip())
    await state.set_state(Registration.age)
    await message.answer(get_text("enter_age", lang))


@registration_router.message(Registration.age, F.text.regexp(r"^\d+$"))
async def process_age(message: types.Message, state: FSMContext) -> None:
    """
    Обработать введённый возраст.
    
    Args:
        message: Сообщение с возрастом
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)
    age = int(message.text.strip())
    
    if not (1 <= age <= 120):
        await message.answer(get_text("invalid_age", lang))
        return
        
    await state.update_data(age=age)
    await state.set_state(Registration.phone)
    # Клавиатура с кнопкой отправки контакта и опцией ввода вручную
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=get_text("send_phone_btn", lang), request_contact=True)],
            [types.KeyboardButton(text=get_text("enter_manual_btn", lang))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(get_text("enter_phone", lang), reply_markup=keyboard)


@registration_router.message(Registration.phone, F.text.regexp(r"^\+?\d{10,15}$"))
async def process_phone(message: types.Message, state: FSMContext) -> None:
    """
    Обработать введённый номер телефона.
    
    Args:
        message: Сообщение с номером телефона
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.phone == message.text.strip())
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            await message.answer(get_text("phone_exists", lang))
            return
            
    await state.update_data(phone=message.text.strip())
    await state.set_state(Registration.photo)
    # Удаляем клавиатуру с кнопкой отправки контакта
    await message.answer(get_text("send_photo", lang), reply_markup=types.ReplyKeyboardRemove())


@registration_router.message(Registration.phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext) -> None:
    """Обработать контакт, отправленный через кнопку request_contact при регистрации."""
    lang = await get_user_language(message.from_user.id)

    if message.contact:
        phone = message.contact.phone_number

        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.phone == phone)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                await message.answer(get_text("phone_exists", lang), reply_markup=types.ReplyKeyboardRemove())
                return

        await state.update_data(phone=phone)
        await state.set_state(Registration.photo)
        await message.answer(get_text("send_photo", lang), reply_markup=types.ReplyKeyboardRemove())


@registration_router.message(Registration.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext) -> None:
    """
    Обработать отправленную фотографию.
    
    Args:
        message: Сообщение с фотографией
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)
    photo_id = message.photo[-1].file_id
    
    await state.update_data(photo=photo_id)
    await state.set_state(Registration.document)
    await message.answer(get_text("send_document", lang))


@registration_router.message(
    Registration.document,
    F.content_type.in_({"document"})
)
async def process_document(message: types.Message, state: FSMContext) -> None:
    """
    Обработать отправленный документ.
    
    Args:
        message: Сообщение с документом
        state: FSM контекст
    """
    lang = await get_user_language(message.from_user.id)
    
    # Проверяем тип документа
    allowed_types = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
    file_extension = message.document.file_name.split('.')[-1].lower()
    
    if file_extension not in allowed_types:
        await message.answer(get_text("invalid_document", lang))
        return
        
    document_id = message.document.file_id
    
    # Получаем все данные
    data = await state.get_data()
    
    # Получаем текущий язык пользователя
    async with async_session() as session:
        user_result = await session.execute(
            select(User).where(User.user_id == message.from_user.id)
        )
        existing_user = user_result.scalar_one_or_none()
        
        # Используем сохраненный язык или текущий
        user_lang = existing_user.language if existing_user and existing_user.language else lang
    
    # Создаём или обновляем пользователя (во избежание попытки вставить уже существующий user_id)
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == message.from_user.id)
        )
        db_user = result.scalar_one_or_none()

        if db_user:
            # Обновляем существующую запись
            db_user.name = data.get('name')
            db_user.age = data.get('age')
            db_user.phone = data.get('phone')
            db_user.photo = data.get('photo')
            db_user.document = document_id
            db_user.language = user_lang
            db_user.is_active = True
            session.add(db_user)
        else:
            # Создаём новую запись
            new_user = User(
                user_id=message.from_user.id,
                name=data.get('name'),
                age=data.get('age'),
                phone=data.get('phone'),
                photo=data.get('photo'),
                document=document_id,
                language=user_lang,  # Используем сохраненный язык
                is_active=True
            )
            session.add(new_user)

        await session.commit()
    
    await message.answer(get_text("registration_complete", user_lang))
    # Показываем главное меню после регистрации
    await message.answer(
        get_text("welcome", user_lang),
        reply_markup=main_menu(message.from_user.id, user_lang)
    )
    
    # Уведомляем администратора о новом пользователе
    try:
        await message.bot.send_message(
            ADMIN_ID,
            get_text(
                "new_user_notification", "ru",
                name=data.get('name'),
                phone=data.get('phone'),
                user_id=message.from_user.id
            )
        )
    except Exception:
        pass
        
    await state.clear()


@registration_router.message(Registration.age)
async def invalid_age(message: types.Message, state: FSMContext) -> None:
    """Обработать неверный формат возраста."""
    lang = await get_user_language(message.from_user.id)
    await message.answer(get_text("enter_age", lang))


@registration_router.message(Registration.phone)
async def invalid_phone(message: types.Message, state: FSMContext) -> None:
    """Обработать неверный формат телефона."""
    lang = await get_user_language(message.from_user.id)
    await message.answer(get_text("enter_phone", lang))


@registration_router.message(Registration.photo)
async def invalid_photo(message: types.Message, state: FSMContext) -> None:
    """Обработать неверный формат фото."""
    lang = await get_user_language(message.from_user.id)
    await message.answer(get_text("send_photo", lang))
