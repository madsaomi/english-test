# 📋 PLAN-021: Фикс регрессии hover + safe-area + состояния успеха/тоста/скроллбара

**Статус:** ✅ COMPLETED (ожидает коммита)

## ✅ Фактическая верификация (2026-09-26)

| Проверка | Результат |
|---|---|
| `check_integrity.py` | **100%** |
| `test_api_http.py` | **19/19** PASSED |
| `test_multi_suites.py` | 4/4 PASSED |
| CSS | скобки **359/359** |
| `optionEnter` fill-mode | `backwards` (не `both`) → `hover` снова работает ✅ |
| `optionConfirm` | полностью удалён (и правило, и keyframes) |
| `safe-area` | top — 1 вхождение, bottom — 2 вхождения |
| `successIn` / `successRing` / `badgeRing` | присутствуют |
| Toast | `scale(0.96)` → `scale(1)` |
| Скроллбар | `::-webkit-scrollbar-thumb` + `scrollbar-color` |
| Live static / 22 id | 200 / ✅ |
| Live полный прогон | **50/50**, score 100, Advanced |
| Временный сервер | погашен |

## 📌 Урок (важно для будущих правок)

Анимация в CSS **приоритетнее** обычных объявлений в каскаде. Поэтому
`animation: ... both` с `transform` в `to`-состоянии **навсегда** перекрывает
`:hover { transform: ... }`, пока анимация активна. Для «появления» элементов
использовать только `backwards` (нужен для задержки) или `none`.
Отдельно: правило с `:not(.skeleton)` (0,3,0) перебивает `.option-card.selected`
(0,2,0) — специфичность надо считать, а не надеяться на порядок.
**Дата:** 2026-09-26
**Причина:** регрессия, найденная при разборе каскада стилей

## 🔍 Найдено

| # | Проблема | Где |
|---|---|---|
| 1 | **`hover`-подъём карточек ответа сломан.** В PLAN-020 добавлен каскад с `animation: ... both`. Заполнение `both` удерживает `transform: translateY(0)` **после** анимации, а анимации в каскаде приоритетнее обычных правил — значит `.option-card:hover { transform: translateY(-2px) }` больше не работает | `style.css` |
| 2 | Из-за более высокой специфичности `:not(.skeleton)` (0,3,0) vs `.option-card.selected` (0,2,0) **гаснет `optionConfirm`** — не было отклика при выборе | `style.css` |
| 3 | Липкий header без `env(safe-area-inset-top)` — в Telegram WebApp на iPhone с вырезом верхний край уходит под статус-бар | `style.css` |
| 4 | Экран результата/вопроса без `safe-area-inset-bottom` — нижние кнопки близко к «домашней» полосе | `style.css` |
| 5 | Сообщение об успехе и toast появляются только fade — нет «живого» масштаба | `style.css` |
| 6 | Скроллбар системный, не в бренде | `style.css` |

## 📋 Шаги

| # | Шаг | Статус |
|---|---|---|
| 1 | `both` → `backwards` в каскаде: после анимации стили возвращаются, hover работает | ✅ |
| 2 | Убрать конфликтующий `optionConfirm` из `.option-card.selected` (+ удалить мёртвые keyframes); отклик при выборе остаётся через transition фона и `checkPop` на галочке | ✅ |
| 3 | `safe-area-inset-top` для `.site-header`, `safe-area-inset-bottom` для `.screen` | ✅ |
| 4 | Успех: scale-in + мягкая жёлтая пульсация рамки | ✅ |
| 5 | Toast: scale-in при появлении | ✅ |
| 6 | Фирменный скроллбар (WebKit + `scrollbar-color`) | ✅ |
| 7 | Completion-badge: мягкое пульсирующее кольцо | ✅ |
| 8 | Верификация: integrity, api_http, live smoke, баланс скобок | ✅ |
| 9 | Коммит + push | ⏳ ждать «да» |

## 🔒 Инварианты

- Только CSS; разметка, 22 id, логика не меняются
- Никаких регулярных выражений по CSS
- `prefers-reduced-motion` глушит всё, включая новые keyframes
