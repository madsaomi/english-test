#!/usr/bin/env python3
"""Export student leads and test results to CSV / JSON format for CRM or teachers.

Данные берутся с реального эндпоинта GET /api/export/leads работающего бэкенда.
Если сервер недоступен или список пуст — записывается демо-запись (fallback).
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import json
import csv
from datetime import datetime
from pathlib import Path
import urllib.request

BASE_DIR = Path(__file__).resolve().parent.parent.parent
EXPORTS_DIR = BASE_DIR / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)

LEADS_ENDPOINT = "/api/export/leads"

def fetch_leads(api_url: str):
    """Запрашивает реальные лиды с бэкенда по /api/export/leads."""
    url = api_url.rstrip("/") + LEADS_ENDPOINT
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def export_leads(api_url: str = "http://127.0.0.1:8000"):
    print(f"📡 Запрос реальных данных с сервера {api_url}{LEADS_ENDPOINT}...")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    leads_data = []
    server_ok = False
    try:
        leads_data = fetch_leads(api_url)
        server_ok = True
        print(f"  Получено записей с сервера: {len(leads_data)}")
    except Exception as e:
        print(f"⚠️ Не удалось подключиться к серверу: {e}")

    if server_ok and not leads_data:
        print("  Сервер вернул пустой список реальных лидов.")

    # Fallback: демо-запись, только если данные получить не удалось
    if not leads_data:
        print("  Экспорт демо-записи (сервер недоступен или нет лидов)...")
        leads_data.append({
            "created_at": datetime.now().isoformat(),
            "session_id": "demo-session-uuid",
            "student_name": "Демо Студент",
            "phone": "+7 999 123-45-67",
            "telegram_username": "@student_tg",
            "test_id": "test_general_2026",
            "cefr_level": "B2",
            "level_title": "B2 (Upper-Intermediate)",
            "score": 82,
            "accuracy_pct": 85,
            "time_seconds": 320,
            "weak_topics": ["Conditionals", "Phrasal Verbs"]
        })

    csv_file = EXPORTS_DIR / f"leads_{timestamp}.csv"
    json_file = EXPORTS_DIR / f"leads_{timestamp}.json"

    fieldnames = [
        "created_at", "session_id", "student_name", "phone",
        "telegram_username", "test_id", "cefr_level", "level_title",
        "score", "accuracy_pct", "time_seconds", "weak_topics"
    ]

    # Запись CSV
    with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in leads_data:
            row_copy = dict(row)
            if isinstance(row_copy.get("weak_topics"), list):
                row_copy["weak_topics"] = ", ".join(row_copy["weak_topics"])
            row_copy.setdefault("created_at", datetime.now().isoformat())
            writer.writerow(row_copy)

    # Запись JSON
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(leads_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Экспорт успешно завершен:")
    print(f"   📄 CSV:  {csv_file}")
    print(f"   📋 JSON: {json_file}\n")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    export_leads(url)