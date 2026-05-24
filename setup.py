#!/bin/bash
# setup_bot.sh - Автоматическая настройка бота на alwaysdata
# Использование: bash setup_bot.sh

echo "=========================================="
echo "  Настройка EduTesterBot на alwaysdata"
echo "=========================================="
echo ""

# Проверка, что скрипт запущен на сервере
if [ ! -d "/home/edutestbot" ]; then
    echo "⚠️  ОШИБКА: Этот скрипт должен быть запущен НА СЕРВЕРЕ alwaysdata"
    echo "Сначала подключитесь: ssh edutestbot@ssh-edutestbot.alwaysdata.net"
    exit 1
fi

# Переход в домашнюю директорию
cd ~
echo "✓ Текущая директория: $(pwd)"

# Проверка наличия файлов бота
if [ ! -f "www/bot/main.py" ]; then
    echo ""
    echo "❌ ОШИБКА: Файлы бота не найдены в ~/www/bot/"
    echo ""
    echo "Сначала загрузите файлы бота:"
    echo "1. Создайте папку: mkdir -p ~/www/bot"
    echo "2. Загрузите файлы через SFTP/FileZilla в ~/www/bot/"
    echo "3. Запустите этот скрипт снова"
    exit 1
fi

echo "✓ Файлы бота найдены в ~/www/bot/"

# Переход в папку бота
cd ~/www/bot
echo "✓ Перешёл в директорию бота"

# Проверка наличия requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "❌ ОШИБКА: Файл requirements.txt не найден"
    exit 1
fi

echo ""
echo "📦 Установка зависимостей Python..."
pip install --user -r requirements.txt 2>&1 | tail -10

if [ $? -ne 0 ]; then
    echo "⚠️  pip не найден, пробую python3 -m pip..."
    python3 -m pip install --user -r requirements.txt 2>&1 | tail -10
fi

echo "✓ Зависимости установлены"

# Проверка наличия .env файла
echo ""
echo "🔍 Проверка конфигурации..."
if [ ! -f "config/.env" ]; then
    echo "❌ ОШИБКА: Файл config/.env не найден"
    echo "Создайте файл config/.env с содержимым:"
    echo "TOKEN=ваш_токен_бота"
    echo "SQLALCHEMY_URL=sqlite+aiosqlite:///./db.sqlite3"
    echo "ADMIN_ID=ваш_telegram_id"
    exit 1
fi

echo "✓ Файл .env найден"

# Показываем содержимое .env (скрываем токен)
echo ""
echo "Содержимое config/.env:"
cat config/.env | sed 's/\(TOKEN=\).*/\1***скрыто***/'

# Создаём резервную копию bot_config.py
if [ -f "config/bot_config.py" ]; then
    echo ""
    echo "📝 Создаю резервную копию config/bot_config.py..."
    cp config/bot_config.py config/bot_config.py.backup
    echo "✓ Резервная копия: config/bot_config.py.backup"
fi

# Исправляем bot_config.py
echo ""
echo "🔧 Исправляю config/bot_config.py..."
cat > config/bot_config.py << 'EOF'
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
EOF

echo "✓ Файл config/bot_config.py обновлён"

# Устанавливаем права доступа на .env
echo ""
echo "🔒 Устанавливаю безопасные права доступа на .env..."
chmod 600 config/.env
echo "✓ Права доступа установлены (600)"

# Тестовый запуск
echo ""
echo "=========================================="
echo "  ТЕСТОВЫЙ ЗАПУСК БОТА"
echo "=========================================="
echo ""
echo "Запускаю бота для проверки..."
echo "Бот запустится на 5 секунд, затем автоматически остановится"
echo ""

# Запускаем бота на фоне с таймаутом
timeout 5 python main.py &
PID=$!

# Ждём 5 секунд
sleep 5

# Проверяем, запущен ли ещё процесс
if ps -p $PID > /dev/null 2>&1; then
    echo ""
    echo "✅ БОТ РАБОТАЕТ КОРРЕКТНО!"
    kill $PID 2>/dev/null
else
    echo ""
    echo "⚠️  Бот завершился раньше времени. Проверьте ошибки выше."
    echo ""
    echo "Для полного запуска выполните:"
    echo "  python ~/www/bot/main.py"
fi

echo ""
echo "=========================================="
echo "  СЛЕДУЮЩИЕ ШАГИ"
echo "=========================================="
echo ""
echo "1. Зайдите в admin.alwaysdata.com → Services → edutestbot"
echo ""
echo "2. Установите настройки:"
echo "   Command: python main.py"
echo "   Working directory: /home/edutestbot/www/bot/"
echo "   Environment: (оставьте пустым)"
echo "   Paused: снимите галочку"
echo ""
echo "3. Нажмите Submit"
echo ""
echo "4. Проверьте логи в Services → edutestbot → Logs"
echo "   Должно появиться: 'Бот запущен!'"
echo ""
echo "=========================================="
echo "  Настройка завершена! 🚀"
echo "=========================================="