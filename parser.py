"""
Парсер лидов через открытые каталоги и поисковые выдачи.
Использует лёгкие requests + BeautifulSoup (без Playwright).
"""

import random
import re
import time
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

import config


class LeadParser:
    """Ищет компании без сайтов через открытые источники."""

    def __init__(self) -> None:
        self.session: requests.Session = requests.Session()
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
        self._ua_index: int = 0

    def _get_random_ua(self) -> str:
        """Возвращает случайный User-Agent из списка."""
        return random.choice(config.USER_AGENTS)

    def _delay(self) -> None:
        """Случайная задержка между запросами."""
        delay: float = random.uniform(config.REQUEST_DELAY_MIN, config.REQUEST_DELAY_MAX)
        time.sleep(delay)

    def _fetch(self, url: str, timeout: int = 15, retries: int = 2) -> Optional[BeautifulSoup]:
        """Выполняет GET-запрос с повторными попытками. Возвращает BeautifulSoup или None."""
        last_error: Optional[str] = None
        for attempt in range(retries + 1):
            try:
                headers: dict = {"User-Agent": self._get_random_ua()}
                resp: requests.Response = self.session.get(
                    url, headers=headers, timeout=timeout, allow_redirects=True
                )
                if resp.status_code == 200:
                    return BeautifulSoup(resp.text, "html.parser")
                last_error = f"HTTP {resp.status_code}"
            except requests.RequestException as e:
                last_error = str(e)
            if attempt < retries:
                self._delay()
        if last_error:
            print(f"[parser] Fetch failed for {url[:80]}: {last_error}")
        return None

    def _has_website(self, text: str) -> bool:
        """Проверяет, есть ли в тексте ссылка на сайт (не соцсеть)."""
        social_domains: List[str] = [
            "facebook.com", "vk.com", "instagram.com", "telegram.me",
            "t.me", "youtube.com", "youtu.be", "ok.ru", "odnoklassniki.ru",
            "youtube", "yandex.ru", "yandex.com", "google.com", "goo.gl",
            "bit.ly", "tiktok.com", "twitter.com", "x.com", "pinterest.com",
        ]
        urls: List[str] = re.findall(r'https?://[^\s"\'<>]+', text)
        bare_domains: List[str] = re.findall(
            r'(?:www\.)?[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}(?:[\/\?\#][^\s"\'<>]*)?',
            text,
        )
        for url in urls:
            url_lower: str = url.lower()
            if any(sd in url_lower for sd in social_domains):
                continue
            return True
        for domain in bare_domains:
            domain_lower: str = domain.lower()
            if any(sd in domain_lower for sd in social_domains):
                continue
            return True
        return False

    def _extract_contacts(self, text: str) -> str:
        """Извлекает телефон и/или email из текста."""
        from validators import extract_contacts
        contacts: List[str] = extract_contacts(text)
        return ", ".join(contacts) if contacts else "не указаны"

    def search_leads(self, query: str, limit: int = 5) -> List[dict]:
        """
        Ищет компании по запросу через Bing (основной) и DuckDuckGo (fallback).
        Возвращает список словарей с данными лидов.
        """
        leads: List[dict] = self._search_bing(query, limit)
        if leads:
            return leads
        return self._search_ddg(query, limit)

    def _search_bing(self, query: str, limit: int) -> List[dict]:
        """Поиск через Bing. Строгая фильтрация: только компании с контактами, без мусора."""
        from filters import has_real_contact, is_musor
        leads: List[dict] = []
        url: str = f"https://www.bing.com/search?q={requests.utils.quote(query)}&setlang=ru&count=20"
        soup: Optional[BeautifulSoup] = self._fetch(url, timeout=20)
        if soup is None:
            return leads
        results = soup.select("li.b_algo")
        if not results:
            results = soup.select("ol li")
        for result in results:
            if len(leads) >= limit:
                break
            title_el = result.select_one("h2 a, h2")
            snippet_el = result.select_one("p, div.b_caption p")
            if title_el is None:
                continue
            name: str = title_el.get_text(strip=True)
            snippet: str = snippet_el.get_text(strip=True) if snippet_el else ""
            full_text: str = f"{name} {snippet}"
            # Строгая фильтрация мусора
            if is_musor(full_text):
                continue
            if self._has_website(full_text):
                continue
            # Обязательное условие: должен быть контакт
            if not has_real_contact(full_text):
                continue
            contact: str = self._extract_contacts(full_text)
            leads.append({
                "name": name,
                "category": query,
                "contact": contact,
                "source": "bing",
            })
            self._delay()
        return leads

    def _search_ddg(self, query: str, limit: int) -> List[dict]:
        """Поиск через DuckDuckGo HTML (fallback). Строгая фильтрация."""
        from filters import has_real_contact, is_musor
        leads: List[dict] = []
        url: str = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}&kl=ru-ru"
        soup: Optional[BeautifulSoup] = self._fetch(url)
        if soup is None:
            return leads
        results = soup.select("div.result__body")
        for result in results:
            if len(leads) >= limit:
                break
            title_el = result.select_one("a.result__a")
            snippet_el = result.select_one("a.result__snippet, div.result__snippet")
            if title_el is None:
                continue
            name: str = title_el.get_text(strip=True)
            snippet: str = snippet_el.get_text(strip=True) if snippet_el else ""
            full_text: str = f"{name} {snippet}"
            # Строгая фильтрация мусора
            if is_musor(full_text):
                continue
            if self._has_website(full_text):
                continue
            # Обязательное условие: должен быть контакт
            if not has_real_contact(full_text):
                continue
            contact: str = self._extract_contacts(full_text)
            leads.append({
                "name": name,
                "category": query,
                "contact": contact,
                "source": "duckduckgo",
            })
            self._delay()
        return leads

    def find_new_leads(self, max_leads: int = 5) -> List[dict]:
        """
        Проходит по поисковым запросам и собирает новых лидов.
        Учитывает историю — повторные лиды не возвращаются.
        Если все источники недоступны — использует seed-данные.
        """
        from history_manager import HistoryManager
        history: HistoryManager = HistoryManager()
        all_leads: List[dict] = []

        # Быстрая проверка доступности источников
        sources_available: bool = self._check_sources_available()
        if not sources_available:
            print("[parser] Search engines unreachable, using seed data")
            return self._seed_leads(history, max_leads)

        for query in config.SEARCH_QUERIES:
            if len(all_leads) >= max_leads:
                break
            remaining: int = max_leads - len(all_leads)
            leads: List[dict] = self.search_leads(query, limit=remaining * 2)
            for lead in leads:
                if len(all_leads) >= max_leads:
                    break
                if history.is_processed(lead["name"], lead["contact"]):
                    continue
                all_leads.append(lead)
            self._delay()
        # Fallback: если парсер не нашёл никого — используем seed-данные
        if not all_leads:
            print("[parser] No leads found via search engines, using seed data")
            all_leads = self._seed_leads(history, max_leads)
        return all_leads[:max_leads]

    def _check_sources_available(self) -> bool:
        """Проверяет доступность хотя бы одного поискового источника."""
        test_url: str = "https://www.bing.com/search?q=test&setlang=ru&count=5"
        soup: Optional[BeautifulSoup] = self._fetch(test_url, timeout=12, retries=0)
        if soup is not None:
            results = soup.select("li.b_algo") or soup.select("ol li")
            if results:
                return True
        test_url2: str = "https://html.duckduckgo.com/html/?q=test&kl=ru-ru"
        soup2: Optional[BeautifulSoup] = self._fetch(test_url2, timeout=12, retries=0)
        if soup2 is not None:
            results2 = soup2.select("div.result__body")
            if results2:
                return True
        return False

    def _seed_leads(self, history: "HistoryManager", limit: int) -> List[dict]:
        """Локальные данные на случай недоступности внешних API."""
        seeds: List[dict] = [
            {"name": "АвтоСервис 'Гараж-24'", "category": "автосервис", "contact": "+7 912 345-67-89", "source": "seed"},
            {"name": "Мастерская 'Кузовной центр'", "category": "кузовной ремонт", "contact": "+7 903 123-45-67", "source": "seed"},
            {"name": "Столярная 'Дерево-Про'", "category": "столярные работы", "contact": "master@wood-pro.ru", "source": "seed"},
            {"name": "Сантехник 'Водопровод-Сервис'", "category": "сантехника", "contact": "+7 916 555-12-34", "source": "seed"},
            {"name": "Электромонтаж 'Ток-Комплект'", "category": "электромонтаж", "contact": "+7 985 777-88-99", "source": "seed"},
            {"name": "Клининг 'Чистота-77'", "category": "клининговые услуги", "contact": "+7 495 123-45-67", "source": "seed"},
            {"name": "Мебельная мастерская 'Шпон-Мебель'", "category": "мебель", "contact": "info@shpon-mebel.ru", "source": "seed"},
            {"name": "Кафе 'Уголок-Кофе'", "category": "рестораны и кафе", "contact": "+7 926 333-44-55", "source": "seed"},
            {"name": "Фитнес-клуб 'Атлант'", "category": "фитнес", "contact": "+7 915 222-33-44", "source": "seed"},
            {"name": "Юрист 'Правовой щит'", "category": "юридические услуги", "contact": "law@pravovojit.ru", "source": "seed"},
        ]
        result: List[dict] = []
        for seed in seeds:
            if len(result) >= limit:
                break
            if history.is_processed(seed["name"], seed["contact"]):
                continue
            result.append(seed)
        return result