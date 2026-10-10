"""
Конфигурация Lead Hunter.
Загружает переменные окружения из GitHub Secrets и задаёт константы.
"""

import os
from typing import List

# --- Telegram ---
TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")

# --- OpenRouter ---
OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY", "")

# --- Папка для данных ---
DATA_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
HISTORY_FILE: str = os.path.join(DATA_DIR, "history.json")

# --- Поисковые ниши / запросы ---
SEARCH_QUERIES: List[str] = [
    "автосервис без сайта",
    "ремонт квартир услуга",
    "столярные работы без сайта",
    "сварочные работы компания",
    "сантехника магазин без сайта",
    "электромонтажные работы",
    "дизайн-проекты интерьера без сайта",
    "установка окон и дверей",
    "клубы и секции без сайта",
    "рассадка и аренда залов",
    "мебельная мастерская",
    "рестораны и кафе без сайта",
    "кофейни без сайта",
    "спортзалы и фитнес без сайта",
    "автошколы без сайта",
    "юридические услуги без сайта",
    "бухгалтерские услуги без сайта",
    " клининговые услуги без сайта",
    "ремонт телефонов и ноутбуков",
    "прокат инструментов и техники",
]

# --- Лимит лидов за одну сессию ---
MAX_LEADS_PER_RUN: int = 5

# --- Задержки ---
REQUEST_DELAY_MIN: float = 1.0
REQUEST_DELAY_MAX: float = 3.0
AI_REQUEST_DELAY: float = 1.0

# --- User-Agent'ы ---
USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

# --- OpenRouter ---
OPENROUTER_URL: str = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
OPENROUTER_FALLBACK_MODEL: str = "nvidia/nemotron-3.5-lightning:free"

# --- Telegram API ---
TELEGRAM_API_URL_TEMPLATE: str = "https://api.telegram.org/bot{token}/sendMessage"

# --- Ключи для обхода rate limit (поддерживаются через env) ---
OPENROUTER_API_KEY_2: str = os.environ.get("OPENROUTER_API_KEY_2", "")