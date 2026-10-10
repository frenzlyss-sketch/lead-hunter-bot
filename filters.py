import re
from typing import List

# --- Фильтр мусора ---
MUSOR_KEYWORDS: List[str] = [
    "youtube", "ютуб", "не работает", "недоступен", "ошибка",
    "форум", "новости", "статья", "блог", "обзор", "отзыв",
    "вконтакте", "vk.com", "твиттер", "twitter",
    "google", "google.com", "yandex", "яндекс",
    "реклама", "рекламное", "спонсор", "партнер",
    "домен", "хостинг", "регистрация",
    "официальный сайт", "перейти на сайт",
    "подписаться", "подписаться на",
    "канал", "группа", "сообщество",
    "новостной", "новостной сайт",
    "редакция", "редактор",
    "МЕТОДИКА", "methodology",
    "пользователь", "пользователи",
    "обсуждение", "обсуждать",
    "вопрос", "ответ", "вопросы",
    "чаво", "faq",
    "контакты для связи", "связаться с",
    "напоминание", "напоминаем",
    "важно", "внимание",
    "предупреждение", "предупреждаем",
]


def is_musor(text: str) -> bool:
    """Проверяет, является ли текст мусором (заголовок статьи, форум, новости)."""
    if not text:
        return True
    lower: str = text.lower()
    for kw in MUSOR_KEYWORDS:
        if kw in lower:
            return True
    return False


def has_real_contact(text: str) -> bool:
    """Проверяет, есть ли в тексте реальный контакт (телефон, email, telegram)."""
    if not text:
        return False
    if re.search(r'(?:\+7|8|7)?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}', text):
        return True
    if re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text):
        return True
    if re.search(r'(?:t\.me/|telegram\.me/|@)[a-zA-Z0-9_]{5,}', text):
        return True
    return False