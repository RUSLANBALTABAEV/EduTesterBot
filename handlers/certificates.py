# handlers/certificates.py
"""
Обработчики для работы с сертификатами (администратор).
"""
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from db.models import Certificate, User
from db.session import async_session
from keyboards.reply import admin_back_keyboard
from i18n.locales import get_text

certificates_router = Router()


async def get_user_language(user_id: int) -> str:
    """Получить язык пользователя."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user.language if user and user.language else "ru"


@certificates_router.message(
    F.text.in_(["Сертификаты", "Certificates", "Sertifikatlar"])
)
async def show_certificates(message: types.Message):
    """
    Показать сертификаты (для администратора).
    
    Args:
        message: Входящее сообщение
    """
    lang = await get_user_language(message.from_user.id)
    
    async with async_session() as session:
        result = await session.execute(select(Certificate))
        certificates = result.scalars().all()
    
    if not certificates:
        await message.answer(get_text("no_certificates", lang))
        return
    
    for cert in certificates:
        user_result = await async_session().execute(
            select(User).where(User.id == cert.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        user_name = user.name if user else "Неизвестный"
        text = (
            f"🏅 Сертификат: {cert.title}\n"
            f"👤 Пользователь: {user_name}\n"
            f"📅 Выдан: {cert.issued_at.strftime('%d.%m.%Y')}"
        )
        
        await message.answer(text)
