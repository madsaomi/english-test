#!/usr/bin/env python3
"""Second Brain & Project Integrity Checker."""

import sys
import os
from pathlib import Path

# Ensure Windows console supports UTF-8 / emojis
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ANSI colors for terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

BASE_DIR = Path(__file__).resolve().parent.parent.parent
AGENTS_DIR = BASE_DIR / "agents"

def log_check(name: str, passed: bool, details: str = ""):
    status = f"{GREEN}[OK]{RESET}" if passed else f"{RED}[FAIL]{RESET}"
    print(f"  {status} {name}")
    if details and not passed:
        print(f"       {YELLOW}--> {details}{RESET}")

def run_integrity_check():
    print(f"\n{BOLD}{CYAN}===================================================={RESET}")
    print(f"{BOLD}{CYAN}   🧠 Second Brain & System Integrity Checker       {RESET}")
    print(f"{BOLD}{CYAN}===================================================={RESET}\n")

    errors_count = 0

    # 1. Проверка структуры папки agents/
    print(f"{BOLD}1. Проверка структуры 'agents/' (Второй Мозг):{RESET}")
    required_subdirs = [
        "architecture", "bugs_and_fixes", "decisions", "deployment",
        "history", "plans", "registry", "rules", "runbooks",
        "tasks", "templates", "testing", "walkthroughs"
    ]
    for subdir in required_subdirs:
        path = AGENTS_DIR / subdir
        exists = path.is_dir()
        if not exists:
            errors_count += 1
        log_check(f"Каталог agents/{subdir}", exists, "Директория отсутствует!")

    # 2. Проверка ключевых файлов документации
    print(f"\n{BOLD}2. Проверка ключевых манифестов:{RESET}")
    required_manifests = [
        BASE_DIR / "AGENTS.md",
        AGENTS_DIR / "AGENT_GUIDE.md",
        AGENTS_DIR / "STATUS.md",
        AGENTS_DIR / "GLOSSARY.md",
        AGENTS_DIR / "rules" / "AGENT_RULES.md",
        AGENTS_DIR / "rules" / "ANTI_PATTERNS.md",
        AGENTS_DIR / "rules" / "CODING_STANDARDS.md",
    ]
    for mf in required_manifests:
        exists = mf.is_file() and mf.stat().st_size > 50
        if not exists:
            errors_count += 1
        log_check(f"Манифест {mf.relative_to(BASE_DIR)}", exists, "Файл отсутствует или пуст")

    # 3. Проверка шаблонов
    print(f"\n{BOLD}3. Проверка бланков шаблонов (agents/templates/):{RESET}")
    required_templates = [
        "template_session_log.md",
        "template_bug_report.md",
        "template_task.md",
        "template_adr.md"
    ]
    for tpl in required_templates:
        p = AGENTS_DIR / "templates" / tpl
        exists = p.is_file() and p.stat().st_size > 50
        if not exists:
            errors_count += 1
        log_check(f"Шаблон {tpl}", exists, "Шаблон отсутствует!")

    # 4. Проверка банка вопросов CEFR
    print(f"\n{BOLD}4. Проверка валидности банка вопросов (questions.py):{RESET}")
    try:
        sys.path.insert(0, str(BASE_DIR))
        from backend.questions import QUESTION_BANK
        
        has_min_questions = len(QUESTION_BANK) >= 25
        if not has_min_questions:
            errors_count += 1
        log_check(f"Количество вопросов в банке: {len(QUESTION_BANK)} (минимум 25)", has_min_questions)

        # Проверка всех уровней CEFR
        levels_present = set(q.level for q in QUESTION_BANK)
        all_cefr_levels = {"A1", "A2", "B1", "B2", "C1", "C2"}
        missing_levels = all_cefr_levels - levels_present
        cefr_ok = (len(missing_levels) == 0)
        if not cefr_ok:
            errors_count += 1
        log_check(f"Охват всех уровней CEFR (A1-C2)", cefr_ok, f"Отсутствуют уровни: {missing_levels}")

        # Проверка валидности индексов correct_option
        invalid_options = [q.id for q in QUESTION_BANK if not (0 <= q.correct_option < len(q.options))]
        options_ok = (len(invalid_options) == 0)
        if not options_ok:
            errors_count += 1
        log_check("Валидность индексов ответов (0 <= index < len)", options_ok, f"Ошибки в вопросах: {invalid_options}")

        # Проверка уникальности ID
        ids = [q.id for q in QUESTION_BANK]
        unique_ids = (len(ids) == len(set(ids)))
        if not unique_ids:
            errors_count += 1
        log_check("Уникальность ID всех вопросов", unique_ids, "Обнаружены дубликаты ID!")

    except Exception as e:
        errors_count += 1
        log_check("Импорт backend.questions", False, str(e))

    # 5. Проверка фронтенда
    print(f"\n{BOLD}5. Проверка файлов фронтенда (static/):{RESET}")
    static_files = [
        BASE_DIR / "static" / "index.html",
        BASE_DIR / "static" / "css" / "style.css",
        BASE_DIR / "static" / "js" / "app.js",
    ]
    for sf in static_files:
        exists = sf.is_file() and sf.stat().st_size > 100
        if not exists:
            errors_count += 1
        log_check(f"Файл {sf.relative_to(BASE_DIR)}", exists, "Файл отсутствует или пуст")

    # Итоговый вывод
    print(f"\n{BOLD}{CYAN}===================================================={RESET}")
    if errors_count == 0:
        print(f"{BOLD}{GREEN}  🎉 ИТОГ: ВСЕ СИСТЕМЫ И ВТОРОЙ МОЗГ В 100% ПОРЯДКЕ! {RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")
        return 0
    else:
        print(f"{BOLD}{RED}  ⚠️ ИТОГ: НАЙДЕНО ОШИБОК: {errors_count} {RESET}")
        print(f"{BOLD}{CYAN}===================================================={RESET}\n")
        return 1

if __name__ == "__main__":
    code = run_integrity_check()
    sys.exit(code)
