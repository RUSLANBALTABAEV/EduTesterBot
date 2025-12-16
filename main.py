# main.py
"""
Главный файл для запуска бота EduTester.
"""
import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config.bot_config import API_TOKEN
from db.session import engine
from db.models import Base
from handlers.start import start_router
from handlers.auth import auth_router
from handlers.registration import registration_router
from handlers.tests import tests_router  # ИЗМЕНЕНО: заменяет courses
from handlers.my_tests import my_tests_router  # ИЗМЕНЕНО: заменяет my_courses
from handlers.testing import testing_router
from handlers.admin import admin_router
from handlers.admin_testing import admin_testing_router
from handlers.test_results import results_router  # НОВОЕ


async def create_tables():
    """Создать таблицы в базе данных."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main():
    """Основная функция запуска бота."""
    # Создаем таблицы
    await create_tables()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=API_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрируем роутеры
    dp.include_router(start_router)
    dp.include_router(auth_router)
    dp.include_router(registration_router)
    dp.include_router(tests_router)  # ИЗМЕНЕНО
    dp.include_router(my_tests_router)  # ИЗМЕНЕНО
    dp.include_router(testing_router)
    dp.include_router(admin_router)
    dp.include_router(admin_testing_router)
    dp.include_router(results_router)  # НОВОЕ
    
    try:
        # Запуск бота
        await bot.delete_webhook(drop_pending_updates=True)
        print("Бот запущен! Нажмите Ctrl+C для остановки.")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\nПолучен сигнал остановки. Завершение работы...")
    finally:
        await bot.session.close()
        print("Бот успешно остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем.")
        sys.exit(0)
