# CLAUDE.md — ST8-AI Workspace

## Роль

Джарвис — персональный AI-ассистент Алексея Леонидовича (ST8-AI).
Telegram-бот для ежедневного управления продажами, лидами и личной продуктивностью.

---

## Запускаемые процессы

Автозапуск при старте ПК: `C:\Users\user\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\ST8-AI.vbs` → `start_jarvis.bat`

| Процесс | Скрипт | Роль |
|---|---|---|
| jarvis.py | главный бот + планировщик сообщений | Telegram polling, обработка команд |
| meal_watchdog.py | watchdog для meal_scheduler.py | перезапускает при падении |
| meal_scheduler.py | питание — меню, проверка, итог | отправляет в 08:00 / 18:30 / 21:00 |
| hourly_monitor.py | мониторинг входящих Kwork | проверяет ответы Юли каждый час |
| error_watcher.py | лог-монитор | следит за ошибками, 0 API токенов |

scheduler.py (Алина / KworkSender) — **отключён**, не запускать.

---

## Расписание сообщений Джарвиса (МСК)

| Время | Функция | Содержание |
|---|---|---|
| 08:00 | make_good_morning | погода + план дня P0/P1/P2 + клиенты |
| 08:00 | meal_scheduler | меню на день (28-дневный цикл) |
| 10:00 | make_call_reminder | напоминание о звонках |
| 11:00 | make_motivation | мотивация |
| 12:00 | make_lead_digest | дайджест лидов |
| 13:00 | make_lunch_tip | обед + совет на вторую половину |
| 15:00 | make_no_response_reminder | follow-up клиентам без ответа 3+ дней |
| 16:00 | make_energy_boost | что успеть до конца дня |
| 17:00 | make_day_summary | итог дня |
| 17:30 | make_weekly_report | еженедельный отчёт (только пятница) |
| 18:30 | meal_scheduler | проверка продуктов на завтра |
| 19:00 | make_evening_summary | вечерний итог |
| 21:00 | meal_scheduler | краткий итог дня питания |
| вс 09:00 | meal_scheduler | недельный отчёт по весу |

---

## Формат сообщений Telegram

Единый стиль для всех сообщений:

```
📅 {дата}

🔴 P0 — срочно:
• Компания (ЛПР) — детали

🟡 P1 — важно:
• Компания (ЛПР) — детали

🟢 P2 — в работе:
• Компания — статус

📋 клиенты:
• AIRI: статус
```

Правила:
- один эмодзи в начале строки
- строчные буквы в заголовках (не ЗАГЛАВНЫЕ)
- нет `---` разделителей и `## заголовков`
- нет `*звёздочек*` Markdown (parse_mode не задан)
- нет `[скобок]` как псевдо-чекбоксов
- нет Latin слов (`Tel:`, `Follow-up:`) — только русский

---

## Структура файлов

### Ядро
- `jarvis.py` — главный бот (2400+ строк), все обработчики команд
- `meal_scheduler.py` — планировщик питания (SEND-ONLY, не полит токен)
- `meal_watchdog.py` — watchdog для meal_scheduler
- `hourly_monitor.py` — мониторинг Kwork inbox (Юля)
- `error_watcher.py` — мониторинг логов
- `scheduler.py` — Kwork-охотник (Алина), сейчас отключён

### Данные
- `st8hub/leads.json` — база лидов (525 записей, очищена от дублей)
- `leads_status.md` — таблица статусов переговоров
- `st8-memory-bank/activeContext.md` — текущие задачи
- `st8-memory-bank/clientPipeline.md` — пайплайн клиентов
- `data/meal_sent.json` — лог отправки питания
- `data/meal_evening_state.json` — состояние вечерней проверки продуктов
- `data/confirmed_menu_{дата}.json` — подтверждённое меню дня
- `meal_plan_28.json` — 28-дневный план питания (~1900 ккал/день)
- `jarvis_session_log.json` — история диалогов
- `jarvis_memory.json` — долгосрочная память по клиентам
- `leads/seen_phones.json` — дедупликация лидов по телефону

### Агенты (agents/)
- `st8_ceo_assistant.py` — CEO-ассистент
- `airi.md`, `bolshakova.md`, `target_clients.md` — контекст по клиентам
- `new_client_kontakt.md` — шаблон нового клиента

### Утилиты
- `_gen_meal_plan.py` — генератор meal_plan_28.json (запустить если нужен новый план)
- `start_jarvis.bat` — ручной/автозапуск всех процессов
- `gis_hunter.py` — сбор лидов через 2GIS
- `hh_hunter.py` — сбор лидов через HeadHunter
- `smart_agents.py` — мульти-агентная система

---

## Питание (meal_scheduler)

28-дневный цикл, старт 2026-04-23. День = `(сегодня - 2026-04-23).days % 28 + 1`.

Обработка входящих сообщений — только через `jarvis.py`:
- `завтрак ок` / `обед ок` / `ужин ок` → подтверждение продуктов
- `нет X` / `замени X` → Claude Haiku подбирает замену с сохранением КБЖУ
- `/вес N` → запись веса в `data/weight_log.json`

---

## Ключевые клиенты

- **AIRI** — партнёрство (ST8-AI 40% / AIRI 60%), договор в работе
- **Большакова Юлия** — договор 200к, ждём подписания
- **Unik Food** — тест amoCRM, контакт Антон
- **Atelier Family** — app v3, митап Марк/Ира
- **Логистический хаб** — 481 лид, топ: CDEK, Вэд партнер, Восточный путь

---

## API и токены

- `JARVIS_BOT_TOKEN` — Telegram бот Джарвис (jarvis.py + meal_scheduler)
- `YULIA_BOT_TOKEN` — Telegram бот Юля (hourly_monitor)
- `ANTHROPIC_API_KEY` — Claude API (Haiku для дешёвых задач, Sonnet для сложных)
- `TAVILY_API_KEY` — веб-поиск
- Стоимость: ~$1–1.5/день при текущей нагрузке

---

## Поведение Джарвиса

- Тон: деловой, конкретный, без воды
- Если данных нет — пишет "нет данных", не придумывает
- `get_moscow_weather()` всегда доступна, не говорить "нет доступа к погоде"
- Mempalace подключён через MCP, не говорить "не знаю mempalace"
- Короткие ответы в Telegram, не использовать WhatsApp-стиль

---

## Навигация по контексту (Claude Code)

1. Перед архитектурными вопросами — читать `graphify-out/GRAPH_REPORT.md`
2. Точка входа в граф: `graphify-out/wiki/index.md`
3. Читать файлы только если явно сказано "прочитай файл"
4. После изменения кода — запустить `graphify update .` (без API cost)

---

## Журнал изменений

### 2026-04-23
- Стиль сообщений Telegram приведён к единому формату в `jarvis.py` и `meal_scheduler.py`:
  - `get_moscow_weather()` — убраны вербальные лейблы ("Погода в Москве:", "Одежда:", "Зонт:", "Обувь:")
  - `make_good_morning()` — ПЛАН ДНЯ / СРОЧНО / ВАЖНО / В РАБОТЕ → строчные
  - `make_no_response_reminder()` — убраны `[Company]`, `Tel:`, `Follow-up:` → добавлены 📌 📞
  - `smart_add_lead()` — убраны `*звёздочки*` Markdown
  - `format_morning_menu()` — разбита двойная эмодзи-строка на две отдельные
  - `format_evening_check()` — ЗАВТРА → завтра
- Старт 28-дневного цикла питания (день 1)
- CLAUDE.md переписан с полным контекстом проекта


# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

