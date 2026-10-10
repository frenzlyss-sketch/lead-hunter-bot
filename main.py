"""
Главная точка входа Lead Hunter.
Инициализирует все модули, ищет лидов, анализирует и отправляет в Telegram.
"""

import os
import config
from ai_analyzer import AIAnalyzer
from history_manager import HistoryManager
from parser import LeadParser
from telegram_bot import TelegramNotifier
from validators import (
    has_any_contact,
    has_forbidden_request,
    is_russian,
    validate_lead,
)


def main() -> None:
    """Запускает один цикл поиска и обработки лидов."""
    history: HistoryManager = HistoryManager()
    parser: LeadParser = LeadParser()
    # Поддерживаем несколько ключей для обхода rate limit
    api_keys: list = [
        os.environ.get("OPENROUTER_API_KEY", ""),
        os.environ.get("OPENROUTER_API_KEY_2", ""),
    ]
    api_keys = [k for k in api_keys if k]
    analyzer: AIAnalyzer = AIAnalyzer(api_keys=api_keys if api_keys else None)
    notifier: TelegramNotifier = TelegramNotifier()

    print(f"[main] Начинаю поиск. Лимит: {config.MAX_LEADS_PER_RUN} лидов.")
    print(f"[main] AI-ключей: {len(analyzer.api_keys)}")

    leads = parser.find_new_leads(max_leads=config.MAX_LEADS_PER_RUN)
    print(f"[main] Найдено новых лидов: {len(leads)}")

    sent_count: int = 0
    for lead in leads:
        name: str = lead.get("name", "Без названия")
        category: str = lead.get("category", "Без категории")
        contact: str = lead.get("contact", "не указаны")

        # --- Валидация контактов ---
        if not validate_lead(name, contact):
            print(f"[main] Пропускаю {name}: нет контактов (телефон/email/telegram).")
            continue

        if not has_any_contact(contact):
            print(f"[main] Пропускаю {name}: контакт не содержит телефона, email или Telegram.")
            continue

        print(f"[main] Обработка: {name} | {category} | {contact}")

        analysis: dict = analyzer.analyze(name, category)
        # Если ИИ вернул {} (не реальный бизнес) — пропускаем
        if analysis is not None and not analysis.get("service_idea"):
            print(f"[main] Пропускаю {name}: ИИ определил, что это не реальный бизнес.")
            continue
        # Если ИИ полностью недоступен — используем локальный шаблон
        if analysis is None:
            print(f"[main] ИИ недоступен для {name}, использую локальный шаблон.")
            analysis = analyzer._local_fallback(name, category)

        service_idea: str = analysis.get("service_idea", "")
        client_message: str = analysis.get("client_message", "")

        # --- Проверка языка: только русский ---
        if not is_russian(service_idea):
            print(f"[main] Пропускаю {name}: service_idea не на русском.")
            continue

        # --- Проверка на запрещённые просьбы ---
        if has_forbidden_request(client_message):
            print(f"[main] Пропускаю {name}: в client_message есть просьба к боту.")
            continue

        success: bool = notifier.send(
            name=name,
            category=category,
            service_idea=service_idea,
            contact=contact,
        )
        if success:
            print(f"[main] Отправил в Telegram: {name}")
            sent_count += 1
        else:
            print(f"[main] Ошибка отправки в Telegram для {name}")

        history.add(
            name=name,
            category=category,
            contact=contact,
            service_idea=service_idea,
            client_message=client_message,
        )
        print(f"[main] История обновлена. Всего записей: {history.count()}")

    print(f"[main] Цикл завершён. Отправок: {sent_count}/{len(leads)}.")


if __name__ == "__main__":
    main()