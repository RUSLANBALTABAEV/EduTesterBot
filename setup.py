# setup.py
"""
Установочный файл для создания базы данных и первоначальной настройки.
"""
import asyncio
from db.session import engine
from db.models import Base


async def setup_database():
    """Настройка базы данных."""
    print("Создание таблиц в базе данных...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы успешно созданы!")
    
    print("\nНе забудьте:")
    print("1. Заполнить config/.env файл:")
    print("   TOKEN=ваш_токен_бота")
    print("   ADMIN_ID=ваш_telegram_id")
    print("\n2. Установить зависимости:")
    print("   pip install -r requirements.txt")
    print("\n3. Запустить бота:")
    print("   python main.py")


if __name__ == "__main__":
    asyncio.run(setup_database())
