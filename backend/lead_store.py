"""Хранилище лидов: персистентные записи заявок с результатами теста.

Переживает рестарт сервера и GC сессий (данные пишутся в data/leads.json).
Используется для экспорта /api/export/leads и детальных результатов в боте.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .config import DATA_DIR
from .models import TestResult

logger = logging.getLogger("lead_store")

LEADS_FILE = DATA_DIR / "leads.json"


class LeadRecord:
    """Иммутабельная запись заявки (plain class, совместим с Pydantic dict)."""

    __slots__ = (
        "session_id", "student_name", "phone", "telegram_username", "tg_user_id",
        "test_id", "received_at", "result", "branch"
    )

    def __init__(self, session_id: str, student_name: str, phone: str,
                 telegram_username: Optional[str], tg_user_id: Optional[int],
                 test_id: str, received_at: datetime, result: TestResult,
                 branch: Optional[str] = "Главный офис"):
        self.session_id = session_id
        self.student_name = student_name
        self.phone = phone
        self.telegram_username = telegram_username
        self.tg_user_id = tg_user_id
        self.test_id = test_id
        self.received_at = received_at
        self.result = result
        self.branch = branch or "Главный офис"

    def to_dict(self) -> dict:
        data = {
            "session_id": self.session_id,
            "student_name": self.student_name,
            "phone": self.phone,
            "telegram_username": self.telegram_username,
            "test_id": self.test_id,
            "received_at": self.received_at.isoformat(timespec="seconds"),
            "branch": self.branch,
        }
        result = self.result.model_dump() if hasattr(self.result, "model_dump") else dict(self.result)
        # M2 (audit 2026-09-27): минимизация PII на диске.
        # - review (полный поразборный разбор с correct_*/explanation) нигде не
        #   используется, но раздувал файл и хранил правильные ответы;
        # - tg_user_id кандидата после PLAN-032 не нужен бизнесу.
        # В памяти данные остаются (LeadRecord), на диск не пишутся.
        result.pop("review", None)
        data["result"] = result
        return data


def _load_from_disk() -> Dict[str, LeadRecord]:
    records: Dict[str, LeadRecord] = {}
    if not LEADS_FILE.exists():
        return records
    try:
        raw = json.loads(LEADS_FILE.read_text(encoding="utf-8"))
        for item in raw:
            sid = item.get("session_id")
            if not sid:
                continue
            record = LeadRecord(
                session_id=sid,
                student_name=item.get("student_name", ""),
                phone=item.get("phone", ""),
                telegram_username=item.get("telegram_username"),
                tg_user_id=item.get("tg_user_id"),
                test_id=item.get("test_id", ""),
                received_at=datetime.fromisoformat(item.get("received_at", "")),
                result=TestResult(**item.get("result", {})),
                branch=item.get("branch", "Главный офис"),
            )
            records[sid] = record
    except Exception as e:
        logger.error(f"Не удалось загрузить {LEADS_FILE}: {e}. Старт с пустым хранилищем.")
    return records


class LeadStore:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._leads: Dict[str, LeadRecord] = _load_from_disk()
        # M2: одноразовая перезапись файла без чувствительных полей.
        # Старые записи (с review и tg_user_id) вычищаются при первом же старте.
        self._persist()

    def _persist(self) -> None:
        try:
            payload = json.dumps(
                [r.to_dict() for r in self._leads.values()],
                ensure_ascii=False,
                indent=2,
            )
            # Атомарная запись (M2): пишем в temp-файл и переименовываем.
            # Прямой write_text на большой файл мог порвать данные при краше (BUG_004).
            tmp = LEADS_FILE.with_name(LEADS_FILE.name + ".tmp")
            tmp.write_text(payload, encoding="utf-8")
            tmp.replace(LEADS_FILE)
        except Exception as e:
            logger.error(f"Не удалось сохранить лиды: {e}")

    def add_lead(self, record: LeadRecord) -> None:
        self._leads[record.session_id] = record
        self._persist()

    def get_lead(self, session_id: str) -> Optional[LeadRecord]:
        return self._leads.get(session_id)

    def list_leads(self) -> List[LeadRecord]:
        return list(self._leads.values())

    def count(self) -> int:
        return len(self._leads)


lead_store = LeadStore()