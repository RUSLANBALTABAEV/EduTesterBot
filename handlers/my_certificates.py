# handlers/my_certificates.py
"""
Обработчики для просмотра сертификатов пользователя.
"""
from aiogram import Router, types
from sqlalchemy import select

from db.models import Certificate, User
from db.session import async_session
from i18n.locales import get_text

my_certificates_router = Router()


async def get_user_language(user_id: int) -> str:
    """Получить язык пользователя."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user.language if user and user.language else "ru"


@my_certificates_router.message(
    F.text.in_(["Мои сертификаты", "My Certificates", "Mening sertifikatlarim"])
)
async def show_my_certificates(message: types.Message):
    """
    Показать сертификаты пользователя.
    
    Args:
        message: Входящее сообщение
    """
    lang = await get_user_language(message.from_user.id)
    
    async with async_session() as session:
        # Получаем пользователя
        user_result = await session.execute(
            select(User).where(User.user_id == message.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            await message.answer(get_text("not_registered", lang))
            return
        
        # Получаем сертификаты пользователя
        certs_result = await session.execute(
            select(Certificate).where(Certificate.user_id == user.id)
        )
        certificates = certs_result.scalars().all()
    
    if not certificates:
        await message.answer(get_text("no_my_certificates", lang))
        return
    
    for cert in certificates:
        text = (
            f"🏅 {cert.title}\n"
            f"📅 Выдан: {cert.issued_at.strftime('%d.%m.%Y')}"
        )
        
        if cert.file_id:
            try:
                await message.answer_document(
                    cert.file_id,
                    caption=text
                )
            except Exception:
                await message.answer(
                    f"{text}\n\n⚠️ Файл сертификата недоступен"
                )
        else:
            await message.answer(text)
