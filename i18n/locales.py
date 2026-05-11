# i18n/locales.py
"""
Модуль локализации для мультиязычной поддержки бота.
Поддерживает русский, английский и узбекский языки.
"""
from typing import Any

# Доступные языки
AVAILABLE_LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇺🇸 English",
    "uz": "🇺🇿 O'zbek"
}

# Словари переводов
TRANSLATIONS = {
    "ru": {
        # Стартовые сообщения
        "welcome": (
            "👋 Здравствуйте! Добро пожаловать!\n"
            "Выберите действие:"
        ),
        "choose_language": "🌐 Выберите язык:",
        "language_changed": "✅ Язык изменен на русский",

        # Кнопки главного меню
        "btn_start": "Старт",
        "btn_list_of_tests": "📋 Список тестов",
        "btn_registration": "Регистрация",
        "btn_auth": "Авторизация",
        "btn_tests": "Тесты",
        "btn_my_tests": "Мои тесты",
        "btn_my_results": "📊 Мои результаты",
        "btn_admin_panel": "Управление тестами",
        "btn_logout": "Выход",
        "btn_language": "🌐 Язык",

        # Авторизация
        "send_phone_btn": "📱 Отправить номер телефона",
        "enter_manual_btn": "✏️ Ввести вручную",
        "auth_instruction": "Для авторизации отправьте номер телефона:",
        "enter_phone_manual": "Введите ваш номер телефона (в формате +998900000000):",
        "already_logged_in": "✅ Вы уже вошли в систему!",
        "enter_phone_auth": "Введите ваш номер телефона (в формате +99890000xxxx):",
        "account_already_active": "⚠️ Этот аккаунт уже привязан и активен.",
        "login_success": "✅ Вход выполнен!",
        "user_not_found": "⚠️ Пользователь не найден. Используйте /register.",
        "logout_success": "🚪 Вы вышли из системы.",
        "not_authorized": "⚠️ Вы не авторизованы.",

        # Регистрация
        "already_registered": (
            "⚠️ Вы уже зарегистрированы.\n"
            "👤 Имя: {name}\n"
            "📱 Телефон: {phone}"
        ),
        "enter_name": "Введите ваше имя:",
        "enter_age": "Введите ваш возраст (числом):",
        "invalid_age": "⚠️ Укажите реальный возраст (1–120). Попробуйте ещё раз.",
        "enter_phone": "Введите ваш номер телефона:",
        "phone_exists": "⚠️ Этот номер уже зарегистрирован.",
        "send_photo": "Отправьте вашу фотографию (как фото, не файлом):",
        "send_document": "Отправьте документ (PDF или изображение как файл):",
        "invalid_document": "⚠️ Допустимы только PDF или изображения (JPG/JPEG/PNG).",
        "registration_complete": "✅ Регистрация завершена!",
        "user_exists": "⚠️ Пользователь уже существует.",
        "new_user_notification": "👤 Новый пользователь: {name}, Телефон: {phone}, TG ID: {user_id}",

        # Тесты
        "no_tests": "📚 Тестов пока нет.",
        "available_tests": "📚 Доступные тесты:\n\nВыберите тест:",
        "test_not_found": "⚠️ Тест не найден.",
        "btn_start_test": "▶️ Начать тест",
        "btn_back": "🔙 Назад",
        "register_first": "⚠️ Сначала зарегистрируйтесь (/register).",
        "test_started": "✅ Тест начат!",
        "test_locked": "🔒 Этот тест еще недоступен. Дождитесь назначенного времени.",

        # Мои тесты
        "not_registered": "⚠️ Вы не зарегистрированы. Используйте /register.",
        "no_my_tests": "📭 У вас пока нет доступных тестов.",
        "no_description": "Без описания",

        # Результаты
        "no_results": "📭 У вас пока нет результатов.",
        "my_results_title": "📊 Ваши результаты тестирования:",
        "result_details": "📊 Детали результата",

        # Администратор
        "no_access": "⛔ Нет доступа.",
        "btn_show_users": "👥 Список пользователей",
        "btn_show_list_of_tests": "📋 Список тестов:",
        "btn_manage_tests": "📋 Управление тестами",
        "btn_delete_all_users": "🗑 Удалить всех пользователей",
        "btn_create_test": "➕ Создать тест",
        "btn_add_questions": "📝 Добавить вопросы",
        "btn_test_results": "📊 Результаты тестов",
        "btn_upload_excel": "📤 Загрузить тест из Excel",
        "btn_download_template": "📥 Скачать шаблон Excel",
        "manage_testing_title": "📋 Управление тестированием:",
        "cancel": "❌ Отмена",
        "enter_test_title": "Введите название теста:",
        "enter_test_description": "Введите описание теста (или отправьте '-' для пропуска):",
        "enter_total_questions": "Введите количество вопросов (по умолчанию 50):",
        "enter_time_limit": "Введите лимит времени в минутах (0 - без ограничения):",
        "enter_scheduled_time": "Введите дату и время начала теста (ДД.ММ.ГГГГ ЧЧ:ММ или '-' для немедленного):",
        "invalid_format_datetime": "Неверный формат. Используйте ДД.MM.ГГГГ ЧЧ:ММ или '-'",
        "send_excel_file": "Отправьте файл Excel (.xlsx) с вопросами (лист 'Questions' с колонками: question,type,points,options).",
        "upload_success": "✅ Тест и вопросы успешно загружены из Excel.",
        "upload_failed": "⚠️ Не удалось обработать файл Excel: {error}",
        "download_template": "Шаблон Excel отправлен.",
        "confirm_test_question": "Создать тест?",
        "yes": "✅ Да",
        "no": "❌ Нет",
        "no_courses": "Нет доступных курсов",
        
        "choose_test_for_results": "Выберите тест для просмотра результатов:",
        "export_to_excel": "📥 Выгрузить в Excel",
        "list_results": "👥 Список результатов",
        "no_results_for_test": "Нет результатов для этого теста",
        "no_data_export": "Нет данных для экспорта",
        "export_caption": "Результаты теста ID: {test_id}",
        "test_created": "✅ Тест '{title}' создан!",
        "admin_main_title": "👤 Главное меню администратора:",
        "users_empty": "📭 Пользователей пока нет.",
        "btn_delete": "🗑 Удалить",
        "user_deleted": "🗑 Пользователь «{name}» удалён.",
        "all_users_deleted": "🗑 Все пользователи удалены.",

        # Общие
        "without_name": "Без имени",
        "not_specified": "не указан",
        "not_indicated": "не указана",
        "unknown": "неизвестный",
        "user": "👤 Пользователь: {name}",
    },

    "en": {
        # Start messages
        "welcome": "👋 Hello! Welcome!\nChoose an action:",
        "choose_language": "🌐 Choose language:",
        "language_changed": "✅ Language changed to English",

        # Main menu buttons
        "btn_start": "Start",
        "btn_registration": "Registration",
        "btn_auth": "Authorization",
        "btn_tests": "Tests",
        "btn_my_tests": "My Tests",
        "btn_my_results": "📊 My Results",
        "btn_admin_panel": "Manage Tests",
        "btn_logout": "Logout",
        "btn_language": "🌐 Language",

        # Authorization
        "send_phone_btn": "📱 Send phone number",
        "enter_manual_btn": "✏️ Enter manually",
        "auth_instruction": "For authorization send your phone number:",
        "enter_phone_manual": "Enter your phone number (format +998900000000):",
        "already_logged_in": "✅ You are already logged in!",
        "enter_phone_auth": "Enter your phone number (format +99890000xxxx):",
        "account_already_active": "⚠️ This account is already linked and active.",
        "login_success": "✅ Login successful!",
        "user_not_found": "⚠️ User not found. Use /register.",
        "logout_success": "🚪 You have logged out.",
        "not_authorized": "⚠️ You are not authorized.",

        # Registration
        "already_registered": (
            "⚠️ You are already registered.\n"
            "👤 Name: {name}\n📱 Phone: {phone}"
        ),
        "enter_name": "Enter your name:",
        "enter_age": "Enter your age (number):",
        "invalid_age": "⚠️ Enter a valid age (1–120). Try again.",
        "enter_phone": "Enter your phone number:",
        "phone_exists": "⚠️ This number is already registered.",
        "send_photo": "Send your photo (as photo, not file):",
        "send_document": "Send document (PDF or image as file):",
        "invalid_document": "⚠️ Only PDF or images (JPG/JPEG/PNG) are allowed.",
        "registration_complete": "✅ Registration completed!",
        "user_exists": "⚠️ User already exists.",
        "new_user_notification": "👤 New user: {name}, Phone: {phone}, TG ID: {user_id}",

        # Tests
        "no_tests": "📚 No tests available yet.",
        "available_tests": "📚 Available tests:\n\nChoose a test:",
        "test_not_found": "⚠️ Test not found.",
        "btn_start_test": "▶️ Start test",
        "btn_back": "🔙 Back",
        "register_first": "⚠️ Register first (/register).",
        "test_started": "✅ Test started!",
        "test_locked": "🔒 This test is not available yet. Wait for the scheduled time.",

        # My tests
        "not_registered": "⚠️ You are not registered. Use /register.",
        "no_my_tests": "📭 You don't have any available tests yet.",
        "no_description": "No description",

        # Results
        "no_results": "📭 You don't have any results yet.",
        "my_results_title": "📊 Your test results:",
        "result_details": "📊 Result details",

        # Admin
        "no_access": "⛔ Access denied.",
        "btn_show_users": "👥 Users list",
        "btn_manage_tests": "📋 Manage tests",
        "btn_list_of_tests": "📋 List of tests",
        "btn_delete_all_users": "🗑 Delete all users",
        "btn_create_test": "➕ Create test",
        "btn_add_questions": "📝 Add questions",
        "btn_test_results": "📊 Test results",
        "btn_upload_excel": "📤 Upload test from Excel",
        "btn_download_template": "📥 Download Excel template",
        "manage_testing_title": "📋 Testing management:",
        "cancel": "❌ Cancel",
        "enter_test_title": "Enter test title:",
        "enter_test_description": "Enter test description (or send '-' to skip):",
        "enter_total_questions": "Enter number of questions (default 50):",
        "enter_time_limit": "Enter time limit in minutes (0 - unlimited):",
        "enter_scheduled_time": "Enter scheduled start (DD.MM.YYYY HH:MM or '-' for immediate):",
        "invalid_format_datetime": "Invalid format. Use DD.MM.YYYY HH:MM or '-'",
        "send_excel_file": "Send an Excel file (.xlsx) with questions (sheet 'Questions' with columns: question,type,points,options).",
        "upload_success": "✅ Test and questions successfully uploaded from Excel.",
        "upload_failed": "⚠️ Failed to process Excel file: {error}",
        "download_template": "Template sent.",
        "confirm_test_question": "Create test?",
        "yes": "✅ Yes",
        "no": "❌ No",
        "no_courses": "No available courses",
        
        "choose_test_for_results": "Choose a test to view results:",
        "export_to_excel": "📥 Export to Excel",
        "list_results": "👥 List results",
        "no_results_for_test": "No results for this test",
        "no_data_export": "No data to export",
        "export_caption": "Results for test ID: {test_id}",
        "test_created": "✅ Test '{title}' created!",
        "admin_main_title": "👤 Admin main menu:",
        "users_empty": "📭 No users yet.",
        "btn_delete": "🗑 Delete",
        "user_deleted": "🗑 User «{name}» deleted.",
        "all_users_deleted": "🗑 All users deleted.",

        # Common
        "without_name": "Without name",
        "not_specified": "not specified",
        "not_indicated": "not indicated",
        "unknown": "unknown",
        "user": "👤 User: {name}",
    },

    "uz": {
        # Boshlash xabarlari
        "welcome": "👋 Salom! Xush kelibsiz!\nAmalni tanlang:",
        "choose_language": "🌐 Tilni tanlang:",
        "language_changed": "✅ Til o'zbek tiliga o'zgartirildi",

        # Asosiy menyu tugmalari
        "btn_start": "Boshlash",
        "btn_registration": "Ro'yxatdan o'tish",
        "btn_auth": "Kirish",
        "btn_tests": "Testlar",
        "btn_my_tests": "Mening testlarim",
        "btn_my_results": "📊 Mening natijalarim",
        "btn_list_of_tests": "📋 Testlar ro'yxati",
        "btn_admin_panel": "Testlarni boshqarish",
        "btn_logout": "Chiqish",
        "btn_language": "🌐 Til",

        # Avtorizatsiya
        "send_phone_btn": "📱 Telefon raqamini yuborish",
        "enter_manual_btn": "✏️ Qo'lda kiritish",
        "auth_instruction": "Avtorizatsiya uchun telefon raqamingizni yuboring:",
        "enter_phone_manual": "Telefon raqamingizni kiriting (format +998900000000):",
        "already_logged_in": "✅ Siz allaqachon tizimga kirdingiz!",
        "enter_phone_auth": "Telefon raqamingizni kiriting (+99890000xxxx formatida):",
        "account_already_active": "⚠️ Bu hisob allaqachon bog'langan va faol.",
        "login_success": "✅ Kirish muvaffaqiyatli!",
        "user_not_found": "⚠️ Foydalanuvchi topilmadi. /register dan foydalaning.",
        "logout_success": "🚪 Siz tizimdan chiqdingiz.",
        "not_authorized": "⚠️ Siz avtorizatsiya qilinmagansiz.",

        # Ro'yxatdan o'tish
        "already_registered": (
            "⚠️ Siz allaqachon ro'yxatdan o'tgansiz.\n"
            "👤 Ism: {name}\n📱 Telefon: {phone}"
        ),
        "enter_name": "Ismingizni kiriting:",
        "enter_age": "Yoshingizni kiriting (raqamda):",
        "invalid_age": "⚠️ Haqiqiy yoshni kiriting (1–120). Qayta urinib ko'ring.",
        "enter_phone": "Telefon raqamingizni kiriting:",
        "phone_exists": "⚠️ Bu raqam allaqachon ro'yxatdan o'tgan.",
        "send_photo": "Rasmingizni yuboring (rasm sifatida, fayl emas):",
        "send_document": "Hujjat yuboring (PDF yoki rasm fayl sifatida):",
        "invalid_document": "⚠️ Faqat PDF yoki rasmlar (JPG/JPEG/PNG) ruxsat etiladi.",
        "registration_complete": "✅ Ro'yxatdan o'tish yakunlandi!",
        "user_exists": "⚠️ Foydalanuvchi allaqachon mavjud.",
        "new_user_notification": "👤 Yangi foydalanuvchi: {name}, Telefon: {phone}, TG ID: {user_id}",

        # Testlar
        "no_tests": "📚 Hozircha testlar yo'q.",
        "available_tests": "📚 Mavjud testlar:\n\nTest tanlang:",
        "test_not_found": "⚠️ Test topilmadi.",
        "btn_start_test": "▶️ Testni boshlash",
        "btn_back": "🔙 Orqaga",
        "register_first": "⚠️ Avval ro'yxatdan o'ting (/register).",
        "test_started": "✅ Test boshlandi!",
        "test_locked": "🔒 Bu test hali mavjud emas. Rejalashtirilgan vaqtni kuting.",

        # Mening testlarim
        "not_registered": "⚠️ Siz ro'yxatdan o'tmagansiz. /register dan foydalaning.",
        "no_my_tests": "📭 Sizda hozircha mavjud testlar yo'q.",
        "no_description": "Tavsif yo'q",

        # Natijalar
        "no_results": "📭 Sizda hozircha natijalar yo'q.",
        "my_results_title": "📊 Sizning test natijalaringiz:",
        "result_details": "📊 Natija tafsilotlari",

        # Administrator
        "no_access": "⛔ Ruxsat yo'q.",
        "btn_show_users": "👥 Foydalanuvchilar ro'yxati",
        "btn_manage_tests": "📋 Testlarni boshqarish",
        "btn_delete_all_users": "🗑 Barcha foydalanuvchilarni o'chirish",
            "btn_create_test": "➕ Test yaratish",
            "btn_add_questions": "📝 Savollar qo'shish",
                "btn_test_results": "📊 Test natijalari",
                "btn_upload_excel": "📤 Testni Excel-dan yuklash",
                "btn_download_template": "📥 Excel shablonini yuklab olish",
            "manage_testing_title": "📋 Testlarni boshqarish:",
            "cancel": "❌ Bekor qilish",
            "enter_test_title": "Test nomini kiriting:",
            "enter_test_description": "Test tavsifini kiriting (yoki '-' yuboring):",
            "enter_total_questions": "Savollar sonini kiriting (standart 50):",
            "enter_time_limit": "Vaqt cheklovini daqiqalarda kiriting (0 - cheksiz):",
            "enter_scheduled_time": "Test boshlanish vaqtini kiriting (DD.MM.YYYY HH:MM yoki '-' uchun):",
                "invalid_format_datetime": "Noto'g'ri format. DD.MM.YYYY HH:MM yoki '-' ishlating",
                "send_excel_file": "Savollar bilan Excel faylini yuboring (.xlsx) (sahifa 'Questions' ustunlar: question,type,points,options).",
                "upload_success": "✅ Test va savollar Excel-dan muvaffaqiyatli yuklandi.",
                "upload_failed": "⚠️ Excel faylini qayta ishlashda xatolik: {error}",
                "download_template": "Shablon yuborildi.",
            "confirm_test_question": "Test yaratilsinmi?",
            "yes": "✅ Ha",
            "no": "❌ Yo'q",
            "no_courses": "Mavjud kurslar yo'q",
            
            "choose_test_for_results": "Natijalarni ko'rish uchun test tanlang:",
            "export_to_excel": "📥 Excelga yuklash",
            "list_results": "👥 Natijalar ro'yxati",
            "no_results_for_test": "Bu test uchun natijalar yo'q",
            "no_data_export": "Eksport uchun ma'lumot yo'q",
            "export_caption": "Test ID natijalari: {test_id}",
            "test_created": "✅ '{title}' nomli test yaratildi!",
            "admin_main_title": "👤 Administrator bosh menyusi:",
            "users_empty": "📭 Foydalanuvchilar hali yo'q.",
            "btn_delete": "🗑 O'chirish",
            "user_deleted": "🗑 Foydalanuvchi «{name}» o'chirildi.",
            "all_users_deleted": "🗑 Barcha foydalanuvchilar o'chirildi.",

        # Umumiy
        "without_name": "Imsiz",
        "not_specified": "ko'rsatilmagan",
        "not_indicated": "ko'rsatilmagan",
        "unknown": "noma'lum",
        "user": "👤 Foydalanuvchi: {name}",
    }
}


def get_text(key: str, lang: str = "ru", **kwargs: Any) -> str:
    """
    Получить локализованный текст.

    Args:
        key: Ключ перевода
        lang: Код языка (ru/en/uz)
        **kwargs: Параметры для форматирования строки

    Returns:
        Локализованная строка с подставленными параметрами
    """
    if lang not in TRANSLATIONS:
        lang = "ru"

    text = TRANSLATIONS[lang].get(
        key,
        TRANSLATIONS["ru"].get(key, key)
    )

    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text

    return text
