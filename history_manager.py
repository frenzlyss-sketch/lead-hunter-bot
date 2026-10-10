"""
Менеджер истории обработанных лидов.
Сохраняет данные между запусками GitHub Actions.
"""

import json
import os
from typing import Optional

import config


class HistoryManager:
    """Управляет историей в data/history.json."""

    def __init__(self, history_file: Optional[str] = None) -> None:
        self.history_file: str = history_file or config.HISTORY_FILE
        self._ensure_data_dir()
        self.history: list = self._load_history()

    def _ensure_data_dir(self) -> None:
        data_dir: str = os.path.dirname(self.history_file)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

    def _load_history(self) -> list:
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save_history(self) -> None:
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def is_processed(self, name: str, contact: str = "") -> bool:
        name_lower: str = (name or "").strip().lower()
        contact_lower: str = (contact or "").strip().lower()
        for entry in self.history:
            entry_name: str = (entry.get("name") or "").strip().lower()
            entry_contact: str = (entry.get("contact") or "").strip().lower()
            if name_lower and entry_name == name_lower:
                return True
            if contact_lower and entry_contact == contact_lower:
                return True
        return False

    def add(self, name: str, category: str, contact: str,
            service_idea: str = "", client_message: str = "") -> None:
        entry: dict = {
            "name": name,
            "category": category,
            "contact": contact,
            "service_idea": service_idea,
            "client_message": client_message,
        }
        self.history.append(entry)
        self._save_history()

    def count(self) -> int:
        return len(self.history)