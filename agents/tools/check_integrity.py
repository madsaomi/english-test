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

# 4. Проверка валидности основного теста (tests_data/test_general_2026.json)
    print(f"\n{BOLD}4. Проверка валидности основного теста (test_general_2026):{RESET}")
    try:
        import json as _json

        bank_file = BASE_DIR / "tests_data" / "test_general_2026.json"
        if not bank_file.exists():
            errors_count += 1
            log_check("Файл tests_data/test_general_2026.json", False, "Файл отсутствует")
        else:
            with open(bank_file, encoding="utf-8") as _f:
                raw = _json.load(_f)

            suite_id_ok = raw.get("id") == "test_general_2026"
            if not suite_id_ok:
                errors_count += 1
            log_check("id набора == test_general_2026", suite_id_ok, f"Получен id: {raw.get('id')}")

            mode_ok = raw.get("mode") == "fixed"
            if not mode_ok:
                errors_count += 1
            log_check("mode == fixed", mode_ok, f"Получен mode: {raw.get('mode')}")

            questions = raw.get("questions", [])
            has_min_questions = len(questions) >= 50
            if not has_min_questions:
                errors_count += 1
            log_check(f"Количество вопросов: {len(questions)} (минимум 50)", has_min_questions)

            ids = [q.get("id") for q in questions]
            unique_ids = (len(ids) == len(set(ids)))
            if not unique_ids:
                errors_count += 1
            log_check("Уникальность ID всех вопросов", unique_ids, "Обнаружены дубликаты ID!")

            all_cefr_levels = {"A1", "A2", "B1", "B2", "C1", "C2"}
            levels = {q.get("level") for q in questions}
            levels_valid = levels and levels <= all_cefr_levels
            if not levels_valid:
                errors_count += 1
            log_check("Все level из набора CEFR (A1-C2)", bool(levels_valid), f"Лишние уровни: {levels - all_cefr_levels}")

            distinct_ok = len(levels) >= 4
            if not distinct_ok:
                errors_count += 1
            log_check(f"Разные уровни сложности (минимум 4, есть {len(levels)})", distinct_ok, f"Найдено уровней: {sorted(levels)}")

            choice_qs = [q for q in questions if q.get("question_type", "choice") == "choice"]
            text_qs = [q for q in questions if q.get("question_type") == "text"]

            bad_choice = []
            for q in choice_qs:
                opts = q.get("options") or []
                co = q.get("correct_option")
                if len(opts) != 4 or co is None or not (0 <= co < len(opts)):
                    bad_choice.append(q.get("id"))
            choice_ok = len(choice_qs) == 45 and not bad_choice
            if not choice_ok:
                errors_count += 1
            log_check(f"Choice-вопросы: {len(choice_qs)} шт., валидные correct_option", choice_ok, f"Проблемы: {bad_choice}")

            bad_text = [q.get("id") for q in text_qs if not (q.get("correct_text") or "").strip() or q.get("correct_option") is not None]
            text_ok = len(text_qs) == 5 and not bad_text
            if not text_ok:
                errors_count += 1
            log_check(f"Text-вопросы: {len(text_qs)} шт., непустой correct_text, без correct_option", text_ok, f"Проблемы: {bad_text}")

            # Loader действительно загружает набор
            sys.path.insert(0, str(BASE_DIR))
            from backend.test_loader import test_repository
            loaded_ok = test_repository.get_test_suite("test_general_2026") is not None
            if not loaded_ok:
                errors_count += 1
            log_check("TestRepository загружает test_general_2026", loaded_ok, "Набор не найден в репозитории")

            # Единственность наборов (автотесты удалены)
            only_one = len(test_repository.test_suites) == 1
            if not only_one:
                errors_count += 1
            log_check("В каталоге ровно 1 тест (main suite)", only_one,
                      f"Найдено наборов: {list(test_repository.test_suites)}")

    except Exception as e:
        errors_count += 1
        log_check("Загрузка/валидация test_general_2026.json", False, str(e))

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

    # 6. Проверка безопасности и персистентности (PLAN-015)
    print(f"\n{BOLD}6. Проверка безопасности и персистентности:{RESET}")
    try:
        main_py = (BASE_DIR / "backend" / "main.py").read_text(encoding="utf-8")
        config_py = (BASE_DIR / "backend" / "config.py").read_text(encoding="utf-8")
        lead_store_py = (BASE_DIR / "backend" / "lead_store.py").read_text(encoding="utf-8")
        env_example = (BASE_DIR / ".env.example").read_text(encoding="utf-8")
        railway = (BASE_DIR / "railway.json").read_text(encoding="utf-8")
        gitignore = (BASE_DIR / ".gitignore").read_text(encoding="utf-8")

        # Экспорт лидов (PII) обязан быть закрыт ключом
        export_protected = (
            'alias="X-API-Key"' in main_py
            and "EXPORT_API_KEY" in main_py
            and "status_code=401" in main_py.replace(" ", "").replace("status_code = 401", "status_code=401")
        )
        if not export_protected:
            errors_count += 1
        log_check("Эндпоинт /api/export/leads защищён X-API-Key", export_protected,
                  "В backend/main.py нет проверки заголовка X-API-Key")

        key_in_config = "EXPORT_API_KEY" in config_py
        if not key_in_config:
            errors_count += 1
        log_check("EXPORT_API_KEY читается из env в backend/config.py", key_in_config,
                  "Переменная не объявлена в config.py")

        data_dir_config = "DATA_DIR" in config_py and "from .config import DATA_DIR" in lead_store_py
        if not data_dir_config:
            errors_count += 1
        log_check("DATA_DIR настраивается через env и используется в lead_store", data_dir_config,
                  "lead_store.py должен импортировать DATA_DIR из config")

        volume_ok = '"volumes"' in railway and "/app/data" in railway
        if not volume_ok:
            errors_count += 1
        log_check("Railway: volume примонтирован в /app/data", volume_ok,
                  "В railway.json нет volumes с mountPath /app/data")

        env_documented = "EXPORT_API_KEY" in env_example and "DATA_DIR" in env_example
        if not env_documented:
            errors_count += 1
        log_check("Новые переменные документированы в .env.example", env_documented,
                  "Добавь EXPORT_API_KEY и DATA_DIR в .env.example")

        leads_ignored = "data/leads.json" in gitignore
        if not leads_ignored:
            errors_count += 1
        log_check("Лиды (data/leads.json) не попадают в git", leads_ignored,
                  "Добавь data/leads.json в .gitignore")

        # Секреты не должны попадать в код
        secrets_in_code = []
        for py_file in (BASE_DIR / "backend").glob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if "8935002748" in content or "8804738116" in content:
                secrets_in_code.append(py_file.name)
        if secrets_in_code:
            errors_count += 1
        log_check("Токены и ID чата не зашиты в код", not secrets_in_code,
                  f"Найдено в: {secrets_in_code}")

        # --- PLAN-017: rate limiting, CORS, анти-спуфинг tg_user_id ---
        rate_limit_ok = all(token in main_py for token in (
            "RATE_LIMIT_REQUESTS", "rate_limit_middleware", "status_code=429", "Retry-After"
        )) and "RATE_LIMIT_REQUESTS" in config_py
        if not rate_limit_ok:
            errors_count += 1
        log_check("Rate limiting мутационных запросов реализован (429 + Retry-After)", rate_limit_ok,
                  "В backend/main.py нет rate_limit_middleware или RATE_LIMIT_* в config.py")

        antispoof_ok = (
            "payload.tg_user_id is not None" in main_py
            and "initData обязательна вместе с tg_user_id" in main_py
        )
        if not antispoof_ok:
            errors_count += 1
        log_check("Анти-спуфинг: tg_user_id требует подписанной initData", antispoof_ok,
                  "Проверка tg_user_id должна требовать tg_init_data (403 иначе)")

        cors_warn_ok = "IS_CORS_WILDCARD" in config_py and "ALLOWED_ORIGINS не задан" in main_py
        if not cors_warn_ok:
            errors_count += 1
        log_check("CORS: предупреждение о wildcard '*' при старте", cors_warn_ok,
                  "Добавь IS_CORS_WILDCARD в config.py и WARNING в lifespan")

        rl_documented = all(v in env_example for v in (
            "RATE_LIMIT_ENABLED", "RATE_LIMIT_REQUESTS", "RATE_LIMIT_WINDOW_SECONDS"
        ))
        if not rl_documented:
            errors_count += 1
        log_check("Переменные rate limit документированы в .env.example", rl_documented,
                  "Добавь RATE_LIMIT_* в .env.example")
    except Exception as e:
        errors_count += 1
        log_check("Проверка безопасности и персистентности", False, str(e))

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
