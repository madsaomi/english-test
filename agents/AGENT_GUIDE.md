# 🧠 Второй Мозг Проекта: Полная Инструкция для Агентов (AGENT_GUIDE.md)

Добро пожаловать в проект **English Level CAT Platform & Telegram Bot**!

Этот каталог `agents/` является **полноценным Вторым Мозгом (Second Brain)** проекта. Здесь хранится вся долговременная память, стандарты разработки, архитектурные решения, база знаний по багам, шаблоны и регламенты.

---

## ⚡ ДВА КАТЕГОРИЧЕСКИХ ПРАВИЛА ДЛЯ ЛЮБОГО АГЕНТА:
> **1. ПРАВИЛО №0 («ВТОРОЙ МОЗГ»):**  
> Перед внесением любых изменений в код полностью изучи регламенты:  
> 👉 **[agents/rules/AGENT_RULES.md](file:///c:/Users/~/Desktop/New%20folder%20(2)/agents/rules/AGENT_RULES.md)**  
> и список строгих запретов:  
> 👉 **[agents/rules/ANTI_PATTERNS.md](file:///c:/Users/~/Desktop/New%20folder%20(2)/agents/rules/ANTI_PATTERNS.md)**
>
> **2. ПРАВИЛО №1 («PLAN-FIRST» — СНАЧАЛА ПЛАН, ПОТОМ КОД):**  
> Категорически запрещено писать или менять код без предварительно составленного плана и **явного одобрения пользователя (Proceed / подтверждение в чате)**. Нарушение приводит к поломке рабочего функционала и потере прогресса.

---

## 🗺️ Полная Карта «Второго Мозга» (`agents/`)

```
agents/
├── AGENT_GUIDE.md                 # 🌟 Главный навигатор по «Второму Мозгу» (этот файл)
├── STATUS.md                      # 📊 Живой дашборд состояния проекта в реальном времени
├── GLOSSARY.md                    # 📖 Глоссарий терминов предметной области (CEFR, CAT, TMA, Lifespan)
│
├── rules/                         # 📜 Обязательные регламенты для агентов
│   ├── AGENT_RULES.md             # Правило №0, порядок входа и передачи эстафеты
│   ├── ANTI_PATTERNS.md           # Строгие запреты (анти-чит, запрет time.sleep, защита истории)
│   └── CODING_STANDARDS.md        # Стандарты типизации Python (Pydantic v2) и верстки
│
├── templates/                     # 📐 Стандартизированные бланки (заполнять только их!)
│   ├── template_session_log.md    # Шаблон отчета о сессии в history/
│   ├── template_bug_report.md     # Шаблон баг-репорта (Симптом ➔ Причина ➔ Решение)
│   ├── template_task.md           # Шаблон карточки новой задачи
│   └── template_adr.md            # Шаблон архитектурного решения (ADR)
│
├── architecture/                  # 🏗️ Архитектурные спецификации и схемы
│   ├── CODEBASE_MAP.md            # Карта кодовой базы и граф зависимостей между файлами
│   ├── CAT_ALGORITHM_SPEC.md      # Формулы шага CAT, стрейки, ротация категорий и сходимость
│   ├── QUESTION_AUTHORING_GUIDE.md# Правила добавления новых вопросов и калибровки сложностей
│   ├── SESSION_LIFECYCLE.md       # Стейт-машина тестирования и политика сборки мусора
│   ├── SECURITY_SPEC.md           # Модель безопасности, защита от списывания, F12 и CORS
│   └── TELEGRAM_INTEGRATION_SPEC.md# Lifespan в FastAPI, aiogram 3.x и авто-детекция WebApp
│
├── decisions/                     # 🏛️ Каталог архитектурных решений (ADR)
│   ├── ADR_001_single_process_fastapi_aiogram.md # Почему единый сервер вместо микросервисов
│   ├── ADR_002_vanilla_css_glassmorphism.md     # Почему Vanilla CSS вместо тяжелых фреймворков
│   └── ADR_003_adaptive_cat_algorithm_design.md # Выбор адаптивной модели CAT
│
├── bugs_and_fixes/                # 🐛 База знаний по ошибкам и багам (ПОЧЕМУ возникли и как решены)
│   ├── BUG_001_pydantic_v2_optional_validation.md # Ошибка Pydantic v2 при None
│   ├── BUG_002_winerror_10048_port_binding.md     # Ошибка занятости сокета порта 8000 на Windows
│   └── BUG_003_windows_console_cp1252_encoding.md # Ошибка кодировки cp1252 в PowerShell
│
├── deployment/                    # 🚀 Руководства по Production деплою и HTTPS
│   └── DEPLOYMENT_RUNBOOK.md      # Ubuntu 22/24, Systemd, Nginx, Let's Encrypt SSL, ngrok
│
├── runbooks/                      # 🚑 Аварийный справочник на случай сбоев
│   └── TROUBLESHOOTING.md         # Решение TelegramConflictError, белого экрана TMA, портов
│
├── testing/                       # 🧪 Тестирование и контроль качества
│   └── QA_CHECKLIST.md            # Обязательный чек-лист регрессионной проверки
│
├── plans/                         # 📐 Implementation Plans
│   └── plan_001_initial_cat_setup.md # Архитектурный план разработки
│
├── walkthroughs/                  # 🚀 Walkthroughs
│   └── walkthrough_001_initial_release.md # Отчет о релизе, тесты и результаты
│
├── registry/                      # 👤 Реестр агентов (кто работал над проектом)
│   └── agent_gemini_antigravity.md # Карточка текущего агента (Gemini 3.8 Flash)
│
├── history/                       # 📝 Инкрементальный журнал сессий (строго без перезаписи!)
│   ├── session_2026-09-17_01_init.md
│   ├── session_2026-09-17_02_implementation.md
│   ├── session_2026-09-17_03_second_brain_upgrade.md
│   └── session_2026-09-17_04_second_brain_completion.md
│
└── tasks/                         # 📋 Управление задачами
    ├── active_task.md             # Активная задача с чеклистом
    ├── backlog.md                 # Идеи на будущее (AI Speaking/Writing, PDF-сертификаты)
    └── archive/                   # Архив закрытых задач
```

---

## 🔄 Как передавать эстафету, если сессия оборвалась:
1. Следующий агент открывает `agents/STATUS.md` и `agents/tasks/active_task.md`.
2. Находит первый незавершенный пункт `[ ]`.
3. Сверяется с `agents/rules/ANTI_PATTERNS.md` и `agents/bugs_and_fixes/`.
4. Выполняет работу, копируя готовый шаблон из `agents/templates/`.
5. По завершении добавляет новую запись в `agents/history/`.
