"""
Telegram-нотификатор.
Отправляет красивые сообщения через Bot API.
"""

import time
from typing import Optional

import requests

import config


class TelegramNotifier:
    """Отправляет лиды в Telegram-чат."""

    def __init__(self, bot_token: str = "", chat_id: str = "") -> None:
        self.bot_token: str = bot_token or config.TELEGRAM_BOT_TOKEN
        self.chat_id: str = chat_id or config.TELEGRAM_CHAT_ID
        self.api_url: str = config.TELEGRAM_API_URL_TEMPLATE.format(token=self.bot_token)

    def send(self, name: str, category: str, service_idea: str, contact: str, retries: int = 2) -> bool:
        """
        Формирует и отправляет сообщение.
        Возвращает True при успехе, False при ошибке.
        """
        if not self.bot_token or not self.chat_id:
            return False
        text: str = (
            f"🎯 **НОВЫЙ ЛИД (АВТО-ПОИСК)**\n\n"
            f"🏢 **Компания:** {name}\n"
            f"💡 **Что предложить:** {service_idea}\n"
            f"📞 **Контакт:** {contact}\n"
            f"📂 **Категория:** {category}"
        )
        payload: dict = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        for attempt in range(retries + 1):
            try:
                resp: requests.Response = requests.post(self.api_url, json=payload, timeout=15)
                if resp.status_code == 200:
                    return True
                if resp.status_code == 429:
                    time.sleep(5 * (attempt + 1))
                    continue
                print(f"[Telegram] HTTP {resp.status_code}: {resp.text[:200]}")
                return False
            except requests.RequestException as e:
                print(f"[Telegram] Request error: {e}")
                if attempt < retries:
                    time.sleep(3)
        return False