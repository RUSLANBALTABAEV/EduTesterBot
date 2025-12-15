# i18n/locales.py
"""
Модуль локализации для мультиязычной поддержки бота.
Поддерживает русский, английский и узбекский языки.
"""
from typing import Any

# Константа для минимальной длины названия сертификата
MIN_CERTIFICATE_TITLE_LENGTH = 3

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
        "btn_certificates": "Мои сертификаты",
        "btn_admin_certificates": "Сертификаты",
        "btn_admin_panel": "Управление курсами и пользователями",
        "btn_logout": "Выход",
        "btn_language": "🌐 Язык",

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

        # Сертификаты
        "no_access": "⛔ Нет доступа.",
        "no_certificates": "📭 Сертификатов пока нет.",
        "no_my_certificates": "📭 У вас пока нет сертификатов.",
        "certificate_file_error": (
            "⚠️ Ошибка при отправке файла сертификата."
        ),
        "your_certificate": "📄 Ваш сертификат",
        "certificate_file": "📄 Файл сертификата",

        # Администратор
        "admin_main_menu": "👤 Главное меню администратора:",
        "btn_show_users": "👥 Список пользователей",
        "btn_manage_courses": "📚 Управление курсами",
        "btn_add_course": "➕ Добавить курс",
        "btn_add_certificate": "🏅 Выдать сертификат",
        "btn_delete_all_users": "🗑 Удалить всех пользователей",
        "btn_admin_back": "🔝 Главное меню администратора",
        "no_users": "📭 Пользователей пока нет.",
        "btn_delete": "🗑 Удалить",
        "user_deleted": (
            "🗑 Пользователь «{name}» "
            "(TG ID: {telegram_id}) удалён."
        ),
        "user_not_found": "⚠️ Пользователь не найден.",
        "no_users_to_delete": "⚠️ Пользователей нет.",
        "all_users_deleted": "🗑 Все пользователи удалены.",
        "course_list": "📚 Список курсов:",
        "btn_edit": "✏️ Редактировать",
        "course_deleted": "🗑 Курс «{title}» удалён.",
        "course_updated": "✅ Курс «{title}» успешно обновлён!",
        "enter_course_title": "➕ Введите название нового курса:",
        "enter_course_description": "Введите описание курса:",
        "enter_course_price": "Введите цену курса (число):",
        "enter_start_date": (
            "Введите дату начала курса (ДД.MM.ГГГГ):"
        ),
        "invalid_date_format": (
            "⚠️ Неверный формат даты. "
            "Введите снова (ДД.MM.ГГГГ):"
        ),
        "enter_end_date": (
            "Введите дату окончания курса (ДД.MM.ГГГГ):"
        ),
        "end_date_before_start": (
            "⚠️ Дата окончания не может быть раньше "
            "даты начала."
        ),
        "course_title_exists": (
            "⚠️ Курс с таким названием уже существует!"
        ),
        "course_added": "✅ Курс «{title}» добавлен!",

        # Редактирование курса
        "edit_course_title": (
            "✏️ Редактирование курса «{title}»\n\n"
            "Введите новое название курса (текущее: {current}):"
        ),
        "edit_course_description": "Введите новое описание курса:",
        "edit_course_price": "Введите новую цену курса:",
        "edit_course_start_date": (
            "Введите новую дату начала курса (ДД.ММ.ГГГГ):"
        ),
        "edit_course_end_date": (
            "Введите новую дату окончания курса (ДД.ММ.ГГГГ):"
        ),

        # Сертификаты - администратор
        "select_user_for_certificate": (
            "👥 Выберите пользователя для выдачи сертификата:"
        ),
        "enter_certificate_title": "📝 Введите название сертификата:",
        "certificate_title_too_short": (
            "⚠️ Название сертификата должно содержать "
            "минимум 3 символа."
        ),
        "send_certificate_file": (
            "📄 Отправьте файл сертификата (документ) "
            "или нажмите 'Без файла':"
        ),
        "btn_no_file": "✅ Без файла",
        "certificate_issued": (
            "✅ Сертификат «{title}» выдан пользователю {name}"
        ),
        "certificate_issued_with_file": (
            "✅ Сертификат «{title}» выдан пользователю "
            "{name} с файлом"
        ),
        "certificate_notification": (
            "🏅 Поздравляем! Вам выдан сертификат:\n\n"
            "<b>{title}</b>"
        ),
        "your_certificate_file": "📄 Ваш сертификат",
        "error_invalid_certificate_data": (
            "⚠️ Ошибка: данные не найдены. "
            "Попробуйте снова."
        ),
        "invalid_price_format": (
            "⚠️ Введите корректную цену (только цифры):"
        ),
        "invalid_certificate_file_format": (
            "⚠️ Отправьте файл как документ "
            "или нажмите 'Без файла'"
        ),

        # Уведомления
        "course_starts_today": (
            "🚀 Сегодня стартует курс: <b>{title}</b>!\n"
            "Желаем удачи 🎉"
        ),
        "course_ends_today": (
            "📅 Сегодня завершился курс: <b>{title}</b>.\n"
            "Спасибо за обучение 🙌"
        ),

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
        "btn_certificates": "My Certificates",
        "btn_admin_certificates": "Certificates",
        "btn_admin_panel": "Manage Courses and Users",
        "btn_logout": "Logout",
        "btn_language": "🌐 Language",

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

        # Certificates
        "no_access": "⛔ Access denied.",
        "no_certificates": "📭 No certificates yet.",
        "no_my_certificates": (
            "📭 You don't have any certificates yet."
        ),
        "certificate_file_error": (
            "⚠️ Error sending certificate file."
        ),
        "your_certificate": "📄 Your certificate",
        "certificate_file": "📄 Certificate file",

        # Admin
        "admin_main_menu": "👤 Administrator main menu:",
        "btn_show_users": "👥 Users list",
        "btn_manage_courses": "📚 Manage courses",
        "btn_add_course": "➕ Add course",
        "btn_add_certificate": "🏅 Issue certificate",
        "btn_delete_all_users": "🗑 Delete all users",
        "btn_admin_back": "🔝 Administrator main menu",
        "no_users": "📭 No users yet.",
        "btn_delete": "🗑 Delete",
        "user_deleted": (
            "🗑 User «{name}» (TG ID: {telegram_id}) deleted."
        ),
        "user_not_found": "⚠️ User not found.",
        "no_users_to_delete": "⚠️ No users to delete.",
        "all_users_deleted": "🗑 All users deleted.",
        "course_list": "📚 Courses list:",
        "btn_edit": "✏️ Edit",
        "course_deleted": "🗑 Course «{title}» deleted.",
        "course_updated": "✅ Course «{title}» successfully updated!",
        "enter_course_title": "➕ Enter new course title:",
        "enter_course_description": "Enter course description:",
        "enter_course_price": "Enter course price (number):",
        "enter_start_date": (
            "Enter course start date (DD.MM.YYYY):"
        ),
        "invalid_date_format": (
            "⚠️ Invalid date format. Enter again (DD.MM.YYYY):"
        ),
        "enter_end_date": "Enter course end date (DD.MM.YYYY):",
        "end_date_before_start": (
            "⚠️ End date cannot be earlier than start date."
        ),
        "course_title_exists": (
            "⚠️ Course with this title already exists!"
        ),
        "course_added": "✅ Course «{title}» added!",

        # Course editing
        "edit_course_title": (
            "✏️ Editing course «{title}»\n\n"
            "Enter new course title (current: {current}):"
        ),
        "edit_course_description": "Enter new course description:",
        "edit_course_price": "Enter new course price:",
        "edit_course_start_date": (
            "Enter new course start date (DD.MM.YYYY):"
        ),
        "edit_course_end_date": (
            "Enter new course end date (DD.MM.YYYY):"
        ),

        # Certificates - admin
        "select_user_for_certificate": (
            "👥 Select user to issue certificate:"
        ),
        "enter_certificate_title": "📝 Enter certificate title:",
        "certificate_title_too_short": (
            "⚠️ Certificate title must contain "
            "at least 3 characters."
        ),
        "send_certificate_file": (
            "📄 Send certificate file (document) "
            "or click 'Without file':"
        ),
        "btn_no_file": "✅ Without file",
        "certificate_issued": (
            "✅ Certificate «{title}» issued to user {name}"
        ),
        "certificate_issued_with_file": (
            "✅ Certificate «{title}» issued to user "
            "{name} with file"
        ),
        "certificate_notification": (
            "🏅 Congratulations! "
            "You have been issued a certificate:\n\n"
            "<b>{title}</b>"
        ),
        "your_certificate_file": "📄 Your certificate",
        "error_invalid_certificate_data": (
            "⚠️ Error: data not found. Please try again."
        ),
        "invalid_price_format": (
            "⚠️ Enter correct price (numbers only):"
        ),
        "invalid_certificate_file_format": (
            "⚠️ Send file as document or click 'Without file'"
        ),

        # Notifications
        "course_starts_today": (
            "🚀 Course starts today: <b>{title}</b>!\n"
            "Good luck 🎉"
        ),
        "course_ends_today": (
            "📅 Course ended today: <b>{title}</b>.\n"
            "Thank you for studying 🙌"
        ),

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
        "btn_courses": "Kurslar",
        "btn_my_courses": "Mening kurslarim",
        "btn_certificates": "Mening sertifikatlarim",
        "btn_admin_certificates": "Sertifikatlar",
        "btn_admin_panel": "Kurs va foydalanuvchilarni boshqarish",
        "btn_logout": "Chiqish",
        "btn_language": "🌐 Til",

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

        # Sertifikatlar
        "no_access": "⛔ Ruxsat yo'q.",
        "no_certificates": "📭 Hozircha sertifikatlar yo'q.",
        "no_my_certificates": "📭 Sizda hozircha sertifikatlar yo'q.",
        "certificate_file_error": (
            "⚠️ Sertifikat faylini yuborishda xatolik."
        ),
        "your_certificate": "📄 Sizning sertifikatingiz",
        "certificate_file": "📄 Sertifikat fayli",

        # Administrator
        "admin_main_menu": "👤 Administrator asosiy menyusi:",
        "btn_show_users": "👥 Foydalanuvchilar ro'yxati",
        "btn_manage_courses": "📚 Kurslarni boshqarish",
        "btn_add_course": "➕ Kurs qo'shish",
        "btn_add_certificate": "🏅 Sertifikat berish",
        "btn_delete_all_users": (
            "🗑 Barcha foydalanuvchilarni o'chirish"
        ),
        "btn_admin_back": "🔝 Administrator asosiy menyusi",
        "no_users": "📭 Hozircha foydalanuvchilar yo'q.",
        "btn_delete": "🗑 O'chirish",
        "user_deleted": (
            "🗑 Foydalanuvchi «{name}» "
            "(TG ID: {telegram_id}) o'chirildi."
        ),
        "user_not_found": "⚠️ Foydalanuvchi topilmadi.",
        "no_users_to_delete": (
            "⚠️ O'chiriladigan foydalanuvchilar yo'q."
        ),
        "all_users_deleted": (
            "🗑 Barcha foydalanuvchilar o'chirildi."
        ),
        "course_list": "📚 Kurslar ro'yxati:",
        "btn_edit": "✏️ Tahrirlash",
        "course_deleted": "🗑 «{title}» kursi o'chirildi.",
        "course_updated": (
            "✅ «{title}» kursi muvaffaqiyatli yangilandi!"
        ),
        "enter_course_title": "➕ Yangi kurs nomini kiriting:",
        "enter_course_description": "Kurs tavsifini kiriting:",
        "enter_course_price": "Kurs narxini kiriting (raqam):",
        "enter_start_date": (
            "Kurs boshlanish sanasini kiriting (KK.OO.YYYY):"
        ),
        "invalid_date_format": (
            "⚠️ Noto'g'ri sana formati. "
            "Qayta kiriting (KK.OO.YYYY):"
        ),
        "enter_end_date": (
            "Kurs tugash sanasini kiriting (KK.OO.YYYY):"
        ),
        "end_date_before_start": (
            "⚠️ Tugash sanasi boshlanish sanasidan "
            "oldin bo'la olmaydi."
        ),
        "course_title_exists": (
            "⚠️ Bunday nomli kurs allaqachon mavjud!"
        ),
        "course_added": "✅ «{title}» kursi qo'shildi!",

        # Kursni tahrirlash
        "edit_course_title": (
            "✏️ «{title}» kursini tahrirlash\n\n"
            "Yangi kurs nomini kiriting (hozirgi: {current}):"
        ),
        "edit_course_description": "Yangi kurs tavsifini kiriting:",
        "edit_course_price": "Yangi kurs narxini kiriting:",
        "edit_course_start_date": (
            "Yangi boshlanish sanasini kiriting (KK.OO.YYYY):"
        ),
        "edit_course_end_date": (
            "Yangi tugash sanasini kiriting (KK.OO.YYYY):"
        ),

        # Sertifikatlar - administrator
        "select_user_for_certificate": (
            "👥 Sertifikat berish uchun foydalanuvchini tanlang:"
        ),
        "enter_certificate_title": "📝 Sertifikat nomini kiriting:",
        "certificate_title_too_short": (
            "⚠️ Sertifikat nomi kamida 3 ta belgi bo'lishi kerak."
        ),
        "send_certificate_file": (
            "📄 Sertifikat faylini yuboring (hujjat) "
            "yoki 'Faylsiz' tugmasini bosing:"
        ),
        "btn_no_file": "✅ Faylsiz",
        "certificate_issued": (
            "✅ «{title}» sertifikati {name} "
            "foydalanuvchiga berildi"
        ),
        "certificate_issued_with_file": (
            "✅ «{title}» sertifikati {name} "
            "foydalanuvchiga fayl bilan berildi"
        ),
        "certificate_notification": (
            "🏅 Tabriklaymiz! Sizga sertifikat berildi:\n\n"
            "<b>{title}</b>"
        ),
        "your_certificate_file": "📄 Sizning sertifikatingiz",
        "error_invalid_certificate_data": (
            "⚠️ Xato: ma'lumot topilmadi. Qayta urinib ko'ring."
        ),
        "invalid_price_format": (
            "⚠️ To'g'ri narxni kiriting (faqat raqamlar):"
        ),
        "invalid_certificate_file_format": (
            "⚠️ Faylni hujjat sifatida yuboring "
            "yoki 'Faylsiz' tugmasini bosing"
        ),

        # Bildirishnomalar
        "course_starts_today": (
            "🚀 Bugun kurs boshlanadi: <b>{title}</b>!\n"
            "Omad yor bo'lsin 🎉"
        ),
        "course_ends_today": (
            "📅 Bugun kurs tugadi: <b>{title}</b>.\n"
            "O'qiganingiz uchun rahmat 🙌"
        ),

        # Umumiy
        "without_name": "Ismsiz",
        "not_specified": "ko'rsatilmagan",
        "not_indicated": "ko'rsatilmagan",
        "unknown": "noma'lum",
        "user": "👤 Foydalanuvchi: {name}",
    }
}

# Доступные языки
AVAILABLE_LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇺🇸 English",
    "uz": "🇺🇿 O'zbek"
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


def get_user_language(user_id: int) -> str:
    """
    Получить язык пользователя (по умолчанию русский).

    В реальном проекте можно хранить в БД.

    Args:
        user_id: ID пользователя

    Returns:
        Код языка по умолчанию 'ru'
    """
    # Пока что возвращаем русский по умолчанию
    # В будущем можно добавить таблицу user_settings в БД
    return "ru"
