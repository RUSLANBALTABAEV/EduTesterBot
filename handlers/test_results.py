# handlers/test_results.py
"""
Обработчики для просмотра результатов тестирования пользователем.
"""
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select, and_
from datetime import timedelta

from db.models import User, TestResult, Test
from db.session import async_session
from i18n.locales import get_text

results_router = Router()


async def get_user_language(user_id: int) -> str:
    """Получить язык пользователя."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user.language if user and user.language else None


@results_router.message(
    F.text.in_(["📊 Мои результаты", "📊 My Results", "📊 Mening natijalarim"])
)
async def show_my_results(message: types.Message) -> None:
    """
    Показать результаты тестирования пользователя.
    
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
        
        # Получаем результаты пользователя
        results_query = await session.execute(
            select(TestResult)
            .where(
                and_(
                    TestResult.user_id == user.id,
                    TestResult.completed_at.is_not(None)
                )
            )
            .order_by(TestResult.completed_at.desc())
        )
        results = results_query.scalars().all()
        
        if not results:
            await message.answer("📭 У вас пока нет завершенных тестов.")
            return
        
        # Формируем список результатов
        keyboard = []
        for result in results:
            # Получаем информацию о тесте
            test_query = await session.execute(
                select(Test).where(Test.id == result.test_id)
            )
            test = test_query.scalar_one_or_none()
            
            if test:
                percentage = (result.score / result.max_score * 100) if result.max_score > 0 else 0
                date_str = result.completed_at.strftime("%d.%m.%Y")
                
                button_text = f"{test.title} - {percentage:.0f}% ({date_str})"
                keyboard.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"view_result_{result.id}"
                    )
                ])
        
        await message.answer(
            "📊 Ваши результаты тестирования:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )


@results_router.callback_query(F.data.startswith("view_result_"))
async def view_result_detail(callback: types.CallbackQuery) -> None:
    """
    Показать детальную информацию о результате теста.
    
    Args:
        callback: Callback query
    """
    parts = callback.data.split("_")
    result_id = int(parts[-1])
    lang = await get_user_language(callback.from_user.id)
    
    async with async_session() as session:
        # Получаем результат
        result_query = await session.execute(
            select(TestResult).where(TestResult.id == result_id)
        )
        result = result_query.scalar_one_or_none()
        
        if not result:
            await callback.answer("❌ Результат не найден", show_alert=True)
            return
        
        # Получаем информацию о тесте
        test_query = await session.execute(
            select(Test).where(Test.id == result.test_id)
        )
        test = test_query.scalar_one_or_none()
        
        # Информация о курсе удалена из проекта — не отображаем её.
        
        # Формируем детальную информацию
        percentage = (result.score / result.max_score * 100) if result.max_score > 0 else 0
        grade = get_grade(percentage)
        
        text = "📊 <b>Детали результата</b>\n\n"
        
        
        if test:
            text += f"📝 <b>Тест:</b> {test.title}\n"
        
        text += "\n📈 <b>Результаты:</b>\n"
        text += f"• Баллы: {result.score:.1f} из {result.max_score}\n"
        text += f"• Процент: {percentage:.1f}%\n"
        text += f"• Оценка: {grade}\n\n"
        
        text += "📅 <b>Дата прохождения:</b>\n"
        text += f"{result.completed_at.strftime('%d.%m.%Y в %H:%M')}\n\n"
        
        # Время прохождения
        if result.started_at:
            duration = result.completed_at - result.started_at
            minutes = duration.seconds // 60
            text += f"⏱ <b>Время прохождения:</b> {minutes} мин.\n"
        
        # Кнопки действий
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 Сохранить результат",
                    callback_data=f"save_result_{result.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад к результатам",
                    callback_data="back_to_results"
                )
            ]
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    await callback.answer()


@results_router.callback_query(F.data.startswith("save_result_"))
async def save_result(callback: types.CallbackQuery) -> None:
    """
    Сохранить результат в виде текстового файла.
    
    Args:
        callback: Callback query
    """
    parts = callback.data.split("_")
    result_id = int(parts[-1])
    
    async with async_session() as session:
        # Получаем результат
        result_query = await session.execute(
            select(TestResult).where(TestResult.id == result_id)
        )
        result = result_query.scalar_one_or_none()
        
        if not result:
            await callback.answer("❌ Результат не найден", show_alert=True)
            return
        
        # Получаем пользователя
        user_query = await session.execute(
            select(User).where(User.id == result.user_id)
        )
        user = user_query.scalar_one_or_none()
        
        # Получаем тест
        test_query = await session.execute(
            select(Test).where(Test.id == result.test_id)
        )
        test = test_query.scalar_one_or_none()
        
        # Формируем текст для сохранения
        percentage = (result.score / result.max_score * 100) if result.max_score > 0 else 0
        grade = get_grade(percentage)
        
        text = "=" * 50 + "\n"
        text += "РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ\n"
        text += "=" * 50 + "\n\n"
        
        text += f"Студент: {user.name}\n"
        text += f"Телефон: {user.phone}\n\n"
        
        # Не добавляем информацию о курсе
        
        if test:
            text += f"Тест: {test.title}\n\n"
        
        text += f"Баллы: {result.score:.1f} из {result.max_score}\n"
        text += f"Процент: {percentage:.1f}%\n"
        text += f"Оценка: {grade}\n\n"
        
        text += f"Дата: {result.completed_at.strftime('%d.%m.%Y')}\n"
        text += f"Время: {result.completed_at.strftime('%H:%M')}\n\n"
        
        if result.started_at:
            duration = result.completed_at - result.started_at
            minutes = duration.seconds // 60
            text += f"Время прохождения: {minutes} минут\n\n"
        
        text += "=" * 50 + "\n"
        
        # Отправляем файл
        from io import BytesIO
        file_data = BytesIO(text.encode('utf-8'))
        file_data.seek(0)
        
        filename = f"result_{user.name}_{result.completed_at.strftime('%Y%m%d')}.txt"
        
        await callback.message.bot.send_document(
            chat_id=callback.from_user.id,
            document=types.BufferedInputFile(
                file=file_data.read(),
                filename=filename
            ),
            caption="📄 Ваш результат тестирования"
        )
    
    await callback.answer("✅ Результат отправлен!", show_alert=True)


@results_router.callback_query(F.data == "back_to_results")
async def back_to_results(callback: types.CallbackQuery) -> None:
    """
    Вернуться к списку результатов.
    
    Args:
        callback: Callback query
    """
    # Создаем временное сообщение для вызова show_my_results
    await show_my_results(callback.message)
    await callback.answer()


def get_grade(percentage: float) -> str:
    """Получить оценку по проценту."""
    if percentage >= 90:
        return "5 (Отлично)"
    elif percentage >= 75:
        return "4 (Хорошо)"
    elif percentage >= 60:
        return "3 (Удовлетворительно)"
    elif percentage >= 50:
        return "2 (Неудовлетворительно)"
    else:
        return "1 (Плохо)"
