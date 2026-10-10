"""
Валидаторы для лидов и AI-ответов.
Проверяет контакты, язык и отсутствие лишних просьб.
"""

import re
from typing import List, Optional

# --- Контакты ---
PHONE_PATTERN: str = r'(?:\+7|8|7)?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}'
EMAIL_PATTERN: str = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
TG_USERNAME_PATTERN: str = r'@?[a-zA-Z0-9_]{5,32}'


def has_phone(text: str) -> bool:
    """Проверяет, есть ли в тексте российский номер телефона (минимум 10 цифр)."""
    return bool(re.search(r'(?:\+7|8|7)?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}', text))


def has_email(text: str) -> bool:
    """Проверяет, есть ли в тексте email."""
    return bool(re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text))


def has_telegram(text: str) -> bool:
    """Проверяет, есть ли в тексте username Telegram."""
    return bool(re.search(r'(?:t\.me/|telegram\.me/|@)[a-zA-Z0-9_]{5,}', text))


def has_any_contact(text: str) -> bool:
    """Проверяет, есть ли хотя бы один контакт."""
    return has_phone(text) or has_email(text) or has_telegram(text)


def extract_contacts(text: str) -> List[str]:
    """Извлекает все контакты из текста: телефоны, email, Telegram usernames."""
    contacts: List[str] = []
    phones: List[str] = re.findall(PHONE_PATTERN, text)
    emails: List[str] = re.findall(EMAIL_PATTERN, text)
    tg_users: List[str] = re.findall(r'(?:t\.me/|telegram\.me/|@)([a-zA-Z0-9_]{5,32})', text)
    for p in phones:
        contacts.append(p.strip())
    for e in emails:
        contacts.append(e.strip())
    for t in tg_users:
        contacts.append(f"@{t}")
    # Убираем дубликаты, сохраняя порядок
    seen: set = set()
    unique: List[str] = []
    for c in contacts:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


# --- Язык ---
CYRILLIC_PATTERN: str = r'[а-яА-ЯёЁ]'
ENGLISH_PATTERN: str = r'[a-zA-Z]'


def is_russian(text: str) -> bool:
    """Проверяет, predominantly ли текст на русском языке."""
    if not text:
        return False
    cyrillic: int = len(re.findall(CYRILLIC_PATTERN, text))
    english: int = len(re.findall(ENGLISH_PATTERN, text))
    return cyrillic >= english


# --- Запрещённые просьбы ---
# Фразы, которые указывают, что боту сказали "сделай это для меня"
FORBIDDEN_PHRASES: List[str] = [
    "напиши мне",
    "напиши для меня",
    "сделай для меня",
    "сделай мне",
    "помоги мне",
    "помоги",
    "нарисуй",
    "сгенерируй",
    "придумай",
    "создай мне",
    "создай для меня",
    "нужно сделать",
    "нужно сделать мне",
    "что мне нужно",
    "мне нужно",
    "я хочу",
    "давай сделай",
    "пожалуйста, напиши",
    "пожалуйста, сделай",
    "обязательно напиши",
    "обязательно сделай",
    "чтобы я мог",
    "чтобы я могла",
    "создай сайт",
    "создай лендинг",
    "создай сайт для",
    "создай лендинг для",
    "сделай сайт",
    "сделай лендинг",
    "сделай сайт для",
    "сделай лендинг для",
    "напиши сайт",
    "напиши лендинг",
    "напиши сайт для",
    "напиши лендинг для",
    "нужен сайт",
    "нужен лендинг",
    "нужен сайт для",
    "нужен лендинг для",
    "нужно создать сайт",
    "нужно создать лендинг",
    "нужно создать сайт для",
    "нужно создать лендинг для",
    "хочу сайт",
    "хочу лендинг",
    "хочу сайт для",
    "хочу лендинг для",
]


def has_forbidden_request(text: str) -> bool:
    """Проверяет, есть ли в тексте просьба что-либо сделать для бота."""
    if not text:
        return False
    lower: str = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if re.search(re.escape(phrase), lower):
            return True
    return False


def validate_lead(name: str, contact: str) -> bool:
    """
    Проверяет, проходит ли лид валидацию.
    Требует: название не пустое, контакт содержит телефон/email/telegram.
    """
    if not name or not name.strip():
        return False
    if not has_any_contact(contact):
        return False
    return True