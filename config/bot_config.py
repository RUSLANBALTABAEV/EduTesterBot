# config/bot_config.py
"""Конфигурация бота."""
import os
from pathlib import Path
from dotenv import dotenv_values

# Получаем абсолютный путь к директории проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Абсолютный путь к .env файлу
env_path = os.path.join(BASE_DIR, 'config', '.env')

# Загружаем конфигурацию
config = dotenv_values(env_path)

API_TOKEN = config['TOKEN']
SQLALCHEMY_URL = config['SQLALCHEMY_URL']
ADMIN_ID = int(config.get("ADMIN_ID", "0"))