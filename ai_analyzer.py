"""
AI-анализатор через OpenRouter API.
Генерирует service_idea и client_message для каждого лида.
Поддерживает несколько API-ключей для обхода rate limit.
"""

import json
import re
import time
from typing import List, Optional

import requests

import config


class AIAnalyzer:
    """Отправляет данные лида в OpenRouter и возвращает структурированный ответ."""

    def __init__(self, api_keys: Optional[List[str]] = None) -> None:
        keys: List[str] = api_keys or [config.OPENROUTER_API_KEY]
        # Фильтруем пустые ключи
        self.api_keys: List[str] = [k for k in keys if k]
        if not self.api_keys:
            self.api_keys = [""]
        self._key_index: int = 0
        self.session: requests.Session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/lead-hunter",
            "X-Title": "Lead Hunter Bot",
        })

    @property
    def api_key(self) -> str:
        """Текущий активный ключ."""
        return self.api_keys[self._key_index]

    def _rotate_key(self) -> None:
        """Переключается на следующий ключ при rate limit."""
        if len(self.api_keys) > 1:
            self._key_index = (self._key_index + 1) % len(self.api_keys)
            print(f"[AIAnalyzer] Switched to key #{self._key_index + 1}/{len(self.api_keys)}")

    def _build_headers(self) -> dict:
        """Возвращает заголовки с текущим ключом."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/lead-hunter",
            "X-Title": "Lead Hunter Bot",
        }

    def _build_prompt(self, name: str, category: str) -> str:
        """Формирует системный промпт для ИИ."""
        return (
            f"Компания: {name}. Ниша: {category}. "
            "Сначала проверь: реальный ли это бизнес (а не новость, форум, заголовок статьи, мусор)? "
            "Если НЕ реальный бизнес — ответь пустым JSON: {}. "
            "Если реальный — дай КРАТКУЮ сводку: что компании не хватает и что можно предложить. "
            "Главный упор — сайт (лендинг/каталог/онлайн-запись). "
            "Также можно упомянуть лёгкую автоматизацию: онлайн-запись, мессенгер-бота, "
            "автоответы, простые forms, интеграцию с картами. "
            "Верни ТОЛЬКО один JSON-объект без пояснений, мыслительных блоков, markdown: "
            '{"service_idea":"1-2 предложения: кратко, что предложить (сайт + лёгкая автоматизация)",'
            '"client_message":"одно предложение: краткое вежливое сообщение для клиента"}. '
            "Никакого другого текста."
        )

    def analyze(self, name: str, category: str, retries: int = 2) -> Optional[dict]:
        """
        Отправляет запрос в OpenRouter и возвращает словарь с service_idea и client_message.
        Поддерживает переключение моделей и ключей при rate limit.
        """
        if not self.api_key:
            return None
        time.sleep(config.AI_REQUEST_DELAY)
        models: List[str] = [config.OPENROUTER_MODEL, config.OPENROUTER_FALLBACK_MODEL]
        last_error: Optional[str] = None
        for model in models:
            for attempt in range(retries + 1):
                try:
                    payload: dict = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "Ты — строгий JSON-сервис. Отвечай ТОЛЬКО валидным JSON-объектом. Не добавляй пояснений, markdown, мыслительных блоков или текста вне JSON."},
                            {"role": "user", "content": self._build_prompt(name, category)},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 512,
                    }
                    resp: requests.Response = self.session.post(
                        config.OPENROUTER_URL, json=payload, headers=self._build_headers(), timeout=45
                    )
                    if resp.status_code == 429:
                        last_error = "rate limited"
                        # Пробуем следующий ключ, если есть
                        if len(self.api_keys) > 1:
                            self._rotate_key()
                            print(f"[AIAnalyzer] Rate limited, switched to key #{self._key_index + 1}")
                            continue
                        wait = 5 * (attempt + 1)
                        print(f"[AIAnalyzer] Rate limited, waiting {wait}s (attempt {attempt + 1}/{retries + 1})")
                        time.sleep(wait)
                        continue
                    if resp.status_code != 200:
                        print(f"[AIAnalyzer] HTTP {resp.status_code} [{model}]: {resp.text[:200]}")
                        # Пробуем следующую модель
                        break
                    data: dict = resp.json()
                    content: str = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    result = self._parse_response(content)
                    if result is not None:
                        return result
                    last_error = "no valid JSON in response"
                except requests.RequestException as e:
                    print(f"[AIAnalyzer] Request error: {e}")
                    return None
                except (KeyError, IndexError, json.JSONDecodeError) as e:
                    print(f"[AIAnalyzer] Parse error: {e}")
                    return None
        print(f"[AIAnalyzer] Gave up after {len(models)} models x {retries + 1} attempts: {last_error}")
        print("[AIAnalyzer] Using local rule-based fallback")
        return self._local_fallback(name, category)

    def _parse_response(self, content: str) -> Optional[dict]:
        """Очищает ответ ИИ от мусора и извлекает JSON."""
        if not content:
            return None
        # Шаблонные значения, которые модель может скопировать из промпта
        template_values: List[str] = [
            "1-2 sentences", "brief, what to offer", "one sentence",
            "brief polite message", "одно предложение",
        ]
        # Ищем JSON-объект с service_idea (игнорируем thinking-блоки)
        match: Optional[re.Match] = re.search(r'\{[^{}]*"service_idea"[^{}]*\}', content, re.DOTALL)
        if match:
            try:
                parsed: dict = json.loads(match.group(0))
                if isinstance(parsed, dict) and "service_idea" in parsed and "client_message" in parsed:
                    idea: str = str(parsed.get("service_idea", ""))
                    if not any(tv.lower() in idea.lower() for tv in template_values):
                        return parsed
            except json.JSONDecodeError:
                pass
        # Fallback: ищем любой JSON-объект
        candidates: List[str] = re.findall(r'\{[^{}]*\}', content, re.DOTALL)
        for candidate in candidates:
            try:
                parsed: dict = json.loads(candidate)
                if isinstance(parsed, dict) and "service_idea" in parsed and "client_message" in parsed:
                    idea: str = str(parsed.get("service_idea", ""))
                    if not any(tv.lower() in idea.lower() for tv in template_values):
                        return parsed
            except json.JSONDecodeError:
                continue
        # Последняя попытка — regex на всю строку
        match2: Optional[re.Match] = re.search(r'\{.*\}', content, re.DOTALL)
        if match2:
            try:
                parsed: dict = json.loads(match2.group(0))
                if isinstance(parsed, dict) and "service_idea" in parsed and "client_message" in parsed:
                    idea: str = str(parsed.get("service_idea", ""))
                    if not any(tv.lower() in idea.lower() for tv in template_values):
                        return parsed
            except json.JSONDecodeError:
                pass
        return None

    def _local_fallback(self, name: str, category: str) -> Optional[dict]:
        """
        Локальный rule-based fallback, когда API недоступен.
        Генерирует валидный русский ответ на основе категории.
        """
        templates: dict = {
            "автосервис": (
                "Создайте современный сайт-каталог с услугами, ценами и онлайн-записью. "
                "Подключите лёгкую автоматизацию: мессенгер-бота для приёма заявок, автоответы и интеграцию с картами.",
                "Здравствуйте! Предлагаю создать удобный сайт с онлайн-записью и настроить базовую автоматизацию, чтобы привлечь больше клиентов."
            ),
            "кузовной ремонт": (
                "Разработайте лендинг с портфолио работ, отзывами и формой заявки. "
                "Добавьте онлайн-калькулятор стоимости и мессенгер-бота для консультаций.",
                "Здравствуйте! Предлагаю создать сайт с портфолио и онлайн-записью, чтобы вы получали больше заказов."
            ),
            "столярные работы": (
                "Создайте сайт-каталог с образцами работ и ценами. "
                "Подключите онлайн-запись и мессенгер-бота для консультаций по проектам.",
                "Здравствуйте! Предлагаю создать удобный сайт с каталогом работ и онлайн-записью."
            ),
            "сантехника": (
                "Сделайте сайт с каталогом товаров, ценами и формой заказа. "
                "Добавьте онлайн-консультацию и интеграцию с картами для доставки.",
                "Здравствуйте! Предлагаю создать сайт с каталогом и онлайн-заказом, чтобы вы были доступны клиентам 24/7."
            ),
            "электромонтаж": (
                "Разработайте сайт с перечнем услуг, ценами и формой заявки. "
                "Подключите мессенгер-бота для приёма заявок и автоответы.",
                "Здравствуйте! Предлагаю создать сайт с услугами и онлайн-записью, чтобы упростить работу."
            ),
            "мебель": (
                "Создайте сайт-каталог с образцами, ценами и формой заказа. "
                "Добавьте онлайн-консультацию и 3D-визуализацию.",
                "Здравствуйте! Предлагаю создать удобный сайт с каталогом и онлайн-заказом."
            ),
            "рестораны и кафе": (
                "Сделайте сайт с меню, фото, отзывами и формой брони. "
                "Подключите онлайн-заказ и мессенгер-бота для доставки.",
                "Здравствуйте! Предлагаю создать сайт с меню и онлайн-бронированием, чтобы привлечь больше гостей."
            ),
            "фитнес": (
                "Разработайте сайт с расписанием, ценами и формой записи. "
                "Добавьте онлайн-запись и мессенгер-бота для напоминаний.",
                "Здравствуйте! Предлагаю создать сайт с онлайн-записью и автоматизацией, чтобы упростить работу."
            ),
            "юридические услуги": (
                "Создайте сайт с перечнем услуг, ценами и формой консультации. "
                "Подключите мессенгер-бота для приёма обращений и автоответы.",
                "Здравствуйте! Предлагаю создать сайт с услугами и онлайн-консультацией."
            ),
            "клининговые услуги": (
                "Сделайте сайт с услугами, ценами и формой заказа. "
                "Добавьте онлайн-калькулятор стоимости и мессенгер-бота для заявок.",
                "Здравствуйте! Предлагаю создать сайт с онлайн-заказом и автоматизацией."
            ),
        }
        # Ищем совпадение по ключевым словам в категории
        lower_cat: str = (category or "").lower()
        for key, (idea, msg) in templates.items():
            if key in lower_cat:
                return {"service_idea": idea, "client_message": msg}
        # Общий шаблон
        return {
            "service_idea": (
                f"Для компании '{name}' в нише '{category}' рекомендуется создать сайт "
                f"(лендинг или каталог) с онлаин-записью и формой обратной связи. "
                f"Также можно подключить лёгкую автоматизацию: мессенгер-бота, автоответы."
            ),
            "client_message": (
                f"Здравствуйте! Предлагаю помочь '{name}' с созданием сайта "
                f"и лёгкой автоматизацией, чтобы вы стали доступнее клиентам."
            ),
        }