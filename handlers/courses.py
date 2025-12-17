# handlers/courses.py
"""
Обработчики для работы с курсами.
"""
from datetime import datetime
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, and_

from db.models import User, Course, CourseEnrollment
from db.session import async_session
from keyboards.reply import main_menu
from keyboards.inline import (
    course_keyboard,
    enrollment_keyboard,
    back_to_courses_keyboard
)
from i18n.locales import get_text

courses_router = Router()


async def get_user_language(user_id: int) -> str:
    """Получить язык пользователя."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user.language if user and user.language else None


@courses_router.message(F.text.in_(["Курсы", "Courses", "Kurslar"]))
async def show_courses(message: types.Message) -> None:
    """
    Показать список доступных курсов.
    
    Args:
        message: Входящее сообщение
    """
    lang = await get_user_language(message.from_user.id)
    
    async with async_session() as session:
        result = await session.execute(select(Course))
        courses = result.scalars().all()

    if not courses:
        await message.answer(get_text("no_courses", lang))
        return

    await message.answer(
        get_text("available_courses", lang),
        reply_markup=course_keyboard(courses, lang)
    )


@courses_router.callback_query(F.data.startswith("course_"))
async def show_course_detail(callback: types.CallbackQuery) -> None:
    """
    Показать детали курса.
    
    Args:
        callback: Callback query
    """
    lang = await get_user_language(callback.from_user.id)
    course_id = int(callback.data.split("_")[1])
    
    async with async_session() as session:
        # Проверяем, зарегистрирован ли пользователь
        user_result = await session.execute(
            select(User).where(User.user_id == callback.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user or not user.is_active:
            await callback.answer(
                get_text("register_first", lang),
                show_alert=True
            )
            return
            
        # Получаем курс
        course_result = await session.execute(
            select(Course).where(Course.id == course_id)
        )
        course = course_result.scalar_one_or_none()
        
        if not course:
            await callback.answer(
                get_text("course_not_found", lang),
                show_alert=True
            )
            return
            
        # Проверяем, записан ли пользователь на курс
        enrollment_result = await session.execute(
            select(CourseEnrollment).where(
                and_(
                    CourseEnrollment.user_id == user.id,
                    CourseEnrollment.course_id == course_id
                )
            )
        )
        enrollment = enrollment_result.scalar_one_or_none()
        
        # Форматируем даты
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
        
        # Формируем текст
        text = (
            f"📘 <b>{course.title}</b>\n\n"
            f"{course.description or get_text('no_description', lang)}\n\n"
            f"{get_text('price', lang, price=course.price)}\n"
            f"{get_text('dates', lang, start=start_date, end=end_date)}"
        )
        
        # Проверяем статус курса
        now = datetime.now()
        if course.end_date and course.end_date < now:
            status = get_text("status_completed", lang)
        elif course.start_date and course.start_date > now:
            status = get_text(
                "status_until",
                lang,
                date=course.start_date.strftime("%d.%m.%Y")
            )
        else:
            status = get_text("status", lang, status="✅ Активен")
            
        text += f"\n\n{status}"
        
        # Отправляем сообщение
        await callback.message.edit_text(
            text,
            reply_markup=enrollment_keyboard(
                course_id,
                bool(enrollment),
                lang
            ),
            parse_mode="HTML"
        )
    
    await callback.answer()


@courses_router.callback_query(F.data.startswith("enroll_"))
async def enroll_in_course(callback: types.CallbackQuery) -> None:
    """
    Записаться на курс.
    
    Args:
        callback: Callback query
    """
    lang = await get_user_language(callback.from_user.id)
    course_id = int(callback.data.split("_")[1])
    
    async with async_session() as session:
        # Проверяем пользователя
        user_result = await session.execute(
            select(User).where(User.user_id == callback.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user or not user.is_active:
            await callback.answer(
                get_text("register_first", lang),
                show_alert=True
            )
            return
            
        # Проверяем курс
        course_result = await session.execute(
            select(Course).where(Course.id == course_id)
        )
        course = course_result.scalar_one_or_none()
        
        if not course:
            await callback.answer(
                get_text("course_not_found", lang),
                show_alert=True
            )
            return
            
        # Проверяем, не записан ли уже
        enrollment_result = await session.execute(
            select(CourseEnrollment).where(
                and_(
                    CourseEnrollment.user_id == user.id,
                    CourseEnrollment.course_id == course_id
                )
            )
        )
        existing_enrollment = enrollment_result.scalar_one_or_none()
        
        if existing_enrollment:
            await callback.answer(
                get_text("already_enrolled", lang),
                show_alert=True
            )
            return
            
        # Записываем на курс
        enrollment = CourseEnrollment(
            user_id=user.id,
            course_id=course_id
        )
        session.add(enrollment)
        await session.commit()
        
        await callback.answer(
            get_text("enrolled_success", lang, title=course.title),
            show_alert=True
        )
        
        # Обновляем клавиатуру
        await callback.message.edit_reply_markup(
            reply_markup=enrollment_keyboard(course_id, True, lang)
        )


@courses_router.callback_query(F.data.startswith("unenroll_"))
async def unenroll_from_course(callback: types.CallbackQuery) -> None:
    """
    Отписаться от курса.
    
    Args:
        callback: Callback query
    """
    lang = await get_user_language(callback.from_user.id)
    course_id = int(callback.data.split("_")[1])
    
    async with async_session() as session:
        # Проверяем пользователя
        user_result = await session.execute(
            select(User).where(User.user_id == callback.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            await callback.answer(
                get_text("not_registered", lang),
                show_alert=True
            )
            return
            
        # Находим запись
        enrollment_result = await session.execute(
            select(CourseEnrollment).where(
                and_(
                    CourseEnrollment.user_id == user.id,
                    CourseEnrollment.course_id == course_id
                )
            )
        )
        enrollment = enrollment_result.scalar_one_or_none()
        
        if not enrollment:
            await callback.answer(
                get_text("not_enrolled", lang),
                show_alert=True
            )
            return
            
        # Удаляем запись
        await session.delete(enrollment)
        await session.commit()
        
        await callback.answer(
            get_text("unenrolled_success", lang),
            show_alert=True
        )
        
        # Обновляем клавиатуру
        await callback.message.edit_reply_markup(
            reply_markup=enrollment_keyboard(course_id, False, lang)
        )


@courses_router.callback_query(F.data == "back_to_courses")
async def back_to_courses(callback: types.CallbackQuery) -> None:
    """
    Вернуться к списку курсов.
    
    Args:
        callback: Callback query
    """
    lang = await get_user_language(callback.from_user.id)
    
    async with async_session() as session:
        result = await session.execute(select(Course))
        courses = result.scalars().all()

    if not courses:
        await callback.message.edit_text(get_text("no_courses", lang))
    else:
        await callback.message.edit_text(
            get_text("available_courses", lang),
            reply_markup=course_keyboard(courses, lang)
        )
    
    await callback.answer()
