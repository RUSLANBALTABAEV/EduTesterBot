# main.py
"""
Главный файл для запуска бота EduTester.
"""
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config.bot_config import API_TOKEN
from db.session import engine
from db.models import Base
from handlers import (
    start_router,
    auth_router,
    registration_router,
    courses_router,
    my_courses_router,
    admin_router,
    testing_router,
    admin_testing_router
)
from handlers.certificates import certificates_router
from handlers.my_certificates import my_certificates_router


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
    
    # Планировщик для уведомлений
    scheduler = AsyncIOScheduler()
    
    # Регистрируем роутеры
    dp.include_router(start_router)
    dp.include_router(auth_router)
    dp.include_router(registration_router)
    dp.include_router(courses_router)
    dp.include_router(my_courses_router)
    dp.include_router(certificates_router)
    dp.include_router(my_certificates_router)
    dp.include_router(testing_router)
    dp.include_router(admin_router)
    dp.include_router(admin_testing_router)
    
    # Запускаем планировщик
    scheduler.start()
    
    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
