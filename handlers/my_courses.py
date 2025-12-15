# handlers/my_courses.py
"""
Обработчики для моих курсов.
"""
from datetime import datetime
from aiogram import Router, types
from sqlalchemy import select, and_

from db.models import User, Course, CourseEnrollment
from db.session import async_session
from keyboards.inline import my_courses_keyboard
from i18n.locales import get_text

my_courses_router = Router()


async def get_user_language(user_id: int) -> str:
    """Получить язык пользователя."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user.language if user and user.language else "ru"


@my_courses_router.message(
    F.text.in_(["Мои курсы", "My Courses", "Mening kurslarim"])
)
async def show_my_courses(message: types.Message) -> None:
    """
    Показать курсы пользователя.
    
    Args:
        message: Входящее сообщение
    """
    lang = await get_user_language(message.from_user.id)
    
    async with async_session() as session:
        # Проверяем пользователя
        user_result = await session.execute(
            select(User).where(User.user_id == message.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user or not user.is_active:
            await message.answer(get_text("not_registered", lang))
            return
            
        # Получаем курсы пользователя
        enrollments_result = await session.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.user_id == user.id
            )
        )
        enrollments = enrollments_result.scalars().all()
        
        if not enrollments:
            await message.answer(get_text("no_my_courses", lang))
            return
            
        # Получаем информацию о курсах
        courses = []
        for enrollment in enrollments:
            course_result = await session.execute(
                select(Course).where(Course.id == enrollment.course_id)
            )
            course = course_result.scalar_one_or_none()
            if course:
                courses.append(course)
        
        if not courses:
            await message.answer(get_text("no_my_courses", lang))
            return
            
        await message.answer(
            "📚 Ваши курсы:",
            reply_markup=my_courses_keyboard(courses, lang)
        )
