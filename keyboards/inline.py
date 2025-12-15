# keyboards/inline.py
"""
Inline клавиатуры для бота.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from i18n.locales import get_text


def course_keyboard(courses, lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Создать клавиатуру со списком курсов.
    
    Args:
        courses: Список курсов
        lang: Язык
        
    Returns:
        InlineKeyboardMarkup
    """
    keyboard = []
    
    for course in courses:
        keyboard.append([
            InlineKeyboardButton(
                text=course.title,
                callback_data=f"course_{course.id}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def enrollment_keyboard(course_id: int, is_enrolled: bool, lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для записи на курс.
    
    Args:
        course_id: ID курса
        is_enrolled: Записан ли пользователь
        lang: Язык
        
    Returns:
        InlineKeyboardMarkup
    """
    if is_enrolled:
        buttons = [
            InlineKeyboardButton(
                text=get_text("btn_unenroll", lang),
                callback_data=f"unenroll_{course_id}"
            )
        ]
    else:
        buttons = [
            InlineKeyboardButton(
                text=get_text("btn_enroll", lang),
                callback_data=f"enroll_{course_id}"
            )
        ]
    
    buttons.append(
        InlineKeyboardButton(
            text=get_text("btn_back", lang),
            callback_data="back_to_courses"
        )
    )
    
    return InlineKeyboardMarkup(
        inline_keyboard=[buttons]
    )


def back_to_courses_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для возврата к курсам.
    
    Args:
        lang: Язык
        
    Returns:
        InlineKeyboardMarkup
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=get_text("btn_back", lang),
                callback_data="back_to_courses"
            )
        ]]
    )


def my_courses_keyboard(courses, lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Создать клавиатуру с курсами пользователя.
    
    Args:
        courses: Список курсов
        lang: Язык
        
    Returns:
        InlineKeyboardMarkup
    """
    keyboard = []
    
    for course in courses:
        keyboard.append([
            InlineKeyboardButton(
                text=course.title,
                callback_data=f"mycourse_{course.id}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
