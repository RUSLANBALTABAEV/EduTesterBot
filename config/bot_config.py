"""Конфигурация бота."""
from dotenv import dotenv_values

config = dotenv_values('./config/.env')

API_TOKEN = config['TOKEN']
SQLALCHEMY_URL = config['SQLALCHEMY_URL']
ADMIN_ID = int(config.get("ADMIN_ID", "0"))
