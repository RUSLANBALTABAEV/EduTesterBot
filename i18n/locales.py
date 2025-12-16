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
        "btn_registration": "Регистрация",
        "btn_auth": "Авторизация",
        "btn_courses": "Курсы",
        "btn_my_courses": "Мои курсы",
        "btn_admin_panel": "Управление курсами и пользователями",
        "btn_logout": "Выход",
        "btn_language": "🌐 Язык",

        # Авторизация - новые переводы
        "send_phone_btn": "📱 Отправить номер телефона",
        "enter_manual_btn": "✏️ Ввести вручную",
        "auth_instruction": "Для авторизации отправьте номер телефона:",
        "enter_phone_manual": "Введите ваш номер телефона (в формате +998900000000):",

        # Регистрация
        "already_registered": (
            "⚠️ Вы уже зарегистрированы.\n"
            "👤 Имя: {name}\n"
            "📱 Телефон: {phone}"
        ),
        "enter_name": "Введите ваше имя:",
        "enter_age": "Введите ваш возраст (числом):",
        "invalid_age": (
            "⚠️ Укажите реальный возраст (1–120). "
            "Попробуйте ещё раз."
        ),
        "enter_phone": "Введите ваш номер телефона:",
        "phone_exists": "⚠️ Этот номер уже зарегистрирован.",
        "send_photo": (
            "Отправьте вашу фотографию "
            "(как фото, не файлом):"
        ),
        "send_document": (
            "Отправьте документ "
            "(PDF или изображение как файл):"
        ),
        "invalid_document": (
            "⚠️ Допустимы только PDF или изображения "
            "(JPG/JPEG/PNG)."
        ),
        "registration_complete": "✅ Регистрация завершена!",
        "user_exists": "⚠️ Пользователь уже существует.",
        "new_user_notification": (
            "👤 Новый пользователь: {name}, "
            "Телефон: {phone}, TG ID: {user_id}"
        ),

        # Авторизация
        "already_logged_in": "✅ Вы уже вошли в систему!",
        "enter_phone_auth": (
            "Введите ваш номер телефона "
            "(в формате +99890000xxxx):"
        ),
        "account_already_active": (
            "⚠️ Этот аккаунт уже привязан и активен."
        ),
        "login_success": "✅ Вход выполнен!",
        "user_not_found": (
            "⚠️ Пользователь не найден. "
            "Используйте /register."
        ),
        "logout_success": "🚪 Вы вышли из системы.",
        "not_authorized": "⚠️ Вы не авторизованы.",

        # Курсы
        "no_courses": "📚 Курсов пока нет.",
        "available_courses": (
            "📚 Доступные курсы:\n\n"
            "Выберите курс:"
        ),
        "course_not_found": "⚠️ Курс не найден.",
        "price": "💰 Цена: {price} сум.",
        "dates": "📅 Даты: {start} — {end}",
        "status": "Статус: {status}",
        "status_completed": "✅ Завершён",
        "status_until": "📅 До {date}",
        "btn_enroll": "✅ Записаться",
        "btn_unenroll": "🚪 Отписаться",
        "btn_back": "🔙 Назад",
        "register_first": (
            "⚠️ Сначала зарегистрируйтесь (/register)."
        ),
        "already_enrolled": "⚠️ Вы уже записаны.",
        "enrolled_success": "✅ Вы записались на курс «{title}»!",
        "not_enrolled": "⚠️ Вы не записаны на этот курс.",
        "unenrolled_success": "🚪 Вы отписались от курса.",

        # Мои курсы
        "not_registered": (
            "⚠️ Вы не зарегистрированы. "
            "Используйте /register."
        ),
        "no_my_courses": "📭 У вас пока нет курсов.",
        "no_description": "Без описания",

        # Администратор
        "no_access": "⛔ Нет доступа.",
        "btn_show_users": "👥 Список пользователей",
        "btn_manage_courses": "📚 Управление курсами",
        "btn_add_course": "➕ Добавить курс",
        "btn_delete_all_users": "🗑 Удалить всех пользователей",

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
        "btn_courses": "Courses",
        "btn_my_courses": "My Courses",
        "btn_admin_panel": "Manage Courses and Users",
        "btn_logout": "Logout",
        "btn_language": "🌐 Language",

        # Authorization - new translations
        "send_phone_btn": "📱 Send phone number",
        "enter_manual_btn": "✏️ Enter manually",
        "auth_instruction": "For authorization send your phone number:",
        "enter_phone_manual": "Enter your phone number (format +998900000000):",

        # Registration
        "already_registered": (
            "⚠️ You are already registered.\n"
            "👤 Name: {name}\n📱 Phone: {phone}"
        ),
        "enter_name": "Enter your name:",
        "enter_age": "Enter your age (number):",
        "invalid_age": (
            "⚠️ Enter a valid age (1–120). Try again."
        ),
        "enter_phone": "Enter your phone number:",
        "phone_exists": "⚠️ This number is already registered.",
        "send_photo": "Send your photo (as photo, not file):",
        "send_document": "Send document (PDF or image as file):",
        "invalid_document": (
            "⚠️ Only PDF or images (JPG/JPEG/PNG) are allowed."
        ),
        "registration_complete": "✅ Registration completed!",
        "user_exists": "⚠️ User already exists.",
        "new_user_notification": (
            "👤 New user: {name}, Phone: {phone}, TG ID: {user_id}"
        ),

        # Authorization
        "already_logged_in": "✅ You are already logged in!",
        "enter_phone_auth": (
            "Enter your phone number (format +99890000xxxx):"
        ),
        "account_already_active": (
            "⚠️ This account is already linked and active."
        ),
        "login_success": "✅ Login successful!",
        "user_not_found": "⚠️ User not found. Use /register.",
        "logout_success": "🚪 You have logged out.",
        "not_authorized": "⚠️ You are not authorized.",

        # Courses
        "no_courses": "📚 No courses available yet.",
        "available_courses": (
            "📚 Available courses:\n\nChoose a course:"
        ),
        "course_not_found": "⚠️ Course not found.",
        "price": "💰 Price: {price} sum.",
        "dates": "📅 Dates: {start} — {end}",
        "status": "Status: {status}",
        "status_completed": "✅ Completed",
        "status_until": "📅 Until {date}",
        "btn_enroll": "✅ Enroll",
        "btn_unenroll": "🚪 Unsubscribe",
        "btn_back": "🔙 Back",
        "register_first": "⚠️ Register first (/register).",
        "already_enrolled": "⚠️ You are already enrolled.",
        "enrolled_success": "✅ You enrolled in course «{title}»!",
        "not_enrolled": "⚠️ You are not enrolled in this course.",
        "unenrolled_success": "🚪 You unsubscribed from the course.",

        # My courses
        "not_registered": (
            "⚠️ You are not registered. Use /register."
        ),
        "no_my_courses": "📭 You don't have any courses yet.",
        "no_description": "No description",

        # Admin
        "no_access": "⛔ Access denied.",
        "btn_show_users": "👥 Users list",
        "btn_manage_courses": "📚 Manage courses",
        "btn_add_course": "➕ Add course",
        "btn_delete_all_users": "🗑 Delete all users",
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
        "btn_courses": "Kurslar",
        "btn_my_courses": "Mening kurslarim",
        "btn_admin_panel": "Kurs va foydalanuvchilarni boshqarish",
        "btn_logout": "Chiqish",
        "btn_language": "🌐 Til",

        # Avtorizatsiya - yangi tarjimalar
        "send_phone_btn": "📱 Telefon raqamini yuborish",
        "enter_manual_btn": "✏️ Qo'lda kiritish",
        "auth_instruction": "Avtorizatsiya uchun telefon raqamingizni yuboring:",
        "enter_phone_manual": "Telefon raqamingizni kiriting (format +998900000000):",

        # Ro'yxatdan o'tish
        "already_registered": (
            "⚠️ Siz allaqachon ro'yxatdan o'tgansiz.\n"
            "👤 Ism: {name}\n📱 Telefon: {phone}"
        ),
        "enter_name": "Ismingizni kiriting:",
        "enter_age": "Yoshingizni kiriting (raqamda):",
        "invalid_age": (
            "⚠️ Haqiqiy yoshni kiriting (1–120). "
            "Qayta urinib ko'ring."
        ),
        "enter_phone": "Telefon raqamingizni kiriting:",
        "phone_exists": (
            "⚠️ Bu raqam allaqachon ro'yxatdan o'tgan."
        ),
        "send_photo": (
            "Rasmingizni yuboring (rasm sifatida, fayl emas):"
        ),
        "send_document": (
            "Hujjat yuboring (PDF yoki rasm fayl sifatida):"
        ),
        "invalid_document": (
            "⚠️ Faqat PDF yoki rasmlar (JPG/JPEG/PNG) "
            "ruxsat etiladi."
        ),
        "registration_complete": "✅ Ro'yxatdan o'tish yakunlandi!",
        "user_exists": "⚠️ Foydalanuvchi allaqachon mavjud.",
        "new_user_notification": (
            "👤 Yangi foydalanuvchi: {name}, "
            "Telefon: {phone}, TG ID: {user_id}"
        ),

        # Avtorizatsiya
        "already_logged_in": "✅ Siz allaqachon tizimga kirdingiz!",
        "enter_phone_auth": (
            "Telefon raqamingizni kiriting "
            "(+99890000xxxx formatida):"
        ),
        "account_already_active": (
            "⚠️ Bu hisob allaqachon bog'langan va faol."
        ),
        "login_success": "✅ Kirish muvaffaqiyatli!",
        "user_not_found": (
            "⚠️ Foydalanuvchi topilmadi. "
            "/register dan foydalaning."
        ),
        "logout_success": "🚪 Siz tizimdan chiqdingiz.",
        "not_authorized": "⚠️ Siz avtorizatsiya qilinmagansiz.",

        # Kurslar
        "no_courses": "📚 Hozircha kurslar yo'q.",
        "available_courses": (
            "📚 Mavjud kurslar:\n\nKurs tanlang:"
        ),
        "course_not_found": "⚠️ Kurs topilmadi.",
        "price": "💰 Narx: {price} so'm.",
        "dates": "📅 Sanalar: {start} — {end}",
        "status": "Holat: {status}",
        "status_completed": "✅ Yakunlangan",
        "status_until": "📅 {date} gacha",
        "btn_enroll": "✅ Ro'yxatdan o'tish",
        "btn_unenroll": "🚪 Bekor qilish",
        "btn_back": "🔙 Orqaga",
        "register_first": (
            "⚠️ Avval ro'yxatdan o'ting (/register)."
        ),
        "already_enrolled": (
            "⚠️ Siz allaqachon ro'yxatdan o'tgansiz."
        ),
        "enrolled_success": "✅ Siz «{title}» kursiga yozdingiz!",
        "not_enrolled": "⚠️ Siz bu kursga yozilmagansiz.",
        "unenrolled_success": "🚪 Siz kursdan chiqib ketdingiz.",

        # Mening kurslarim
        "not_registered": (
            "⚠️ Siz ro'yxatdan o'tmagansiz. "
            "/register dan foydalaning."
        ),
        "no_my_courses": "📭 Sizda hozircha kurslar yo'q.",
        "no_description": "Tavsif yo'q",

        # Administrator
        "no_access": "⛔ Ruxsat yo'q.",
        "btn_show_users": "👥 Foydalanuvchilar ro'yxati",
        "btn_manage_courses": "📚 Kurslarni boshqarish",
        "btn_add_course": "➕ Kurs qo'shish",
        "btn_delete_all_users": (
            "🗑 Barcha foydalanuvchilarni o'chirish"
        ),
    }
}
