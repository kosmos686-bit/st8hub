# ST8-AI — Product Context

## Компания

**ST8-AI** (st8-ai.ru) — российская AI-платформа для автоматизации бизнеса.
Фокус: HoReCa, ритейл, производство, логистика.
Статистика: 47 проектов · 94% точность прогнозов · 0 провальных внедрений.

## Команда

| Роль | Человек | Контакт |
|------|---------|---------|
| Сооснователь, AI-архитектор | Алексей Леонидович Гагарин | @Zzima686, kosmos686@gmail.com |
| Ведущий разработчик, подписант | Юлия Попова (ИП) | @P2024_1, ИНН 662607100653 |

Юлия — единственный подписант всех договоров. Альберт Хайров вышел из команды.

## Продукты ST8-AI

### ST8 Resto (основной продукт HoReCa)
- Backend: FastAPI (30 файлов), Frontend: Next.js 15 (7 TSX), Mobile: Flutter (5 dart)
- Инфраструктура: docker-compose
- Архив: ST8_Resto_Full_v1.zip, TZ v2.2

### ST8 Hub (внутренний инструмент продаж)
- URL: kosmos686-bit.github.io/st8hub/
- CRM: 19 клиентов, 18 КП
- AI-генератор КП (claude-sonnet-4-20250514)
- localStorage: st8_clients, st8_apikey
- Дизайн: #0A0F1A/#D4A017, Montserrat

### Unikfood Pilot (Екатеринбург, PP-доставка)
- ТЗ: TZ_Unikfood_Pilot_v1.docx
- App: unikfood-v4.jsx (5 табов, AI-диетолог, дизайн #0A0A0A/#C8F53C, Barlow Condensed)
- Ограничение: iiko и 1С не интегрируются между собой — двойной импорт в БД ST8

### Хокку-бот (Polyana Group, Самара)
- Telegram: @hokku_samara_bot — ЖИВОЙ, в продакшне
- Клиент: Polyana Group, контакт Роман Вавилин
- Операционный директор по маркетингу: Анастасия
- Ожидаем: API-ключ + ID заведения MCRM Superkit (mcrmkit.ru)

### Atelier Family (Москва)
- atelierfamily.ru, владельцы Марк + Ира
- Статус: отказ от консьержа, согласие на мобильное приложение
- App v3: atelier-v3.jsx, B2B dashboard, retention, unit economics
- Демо: atelier-family-web-x0gcv8.abacusai.app

### Лёгкий Шаг (сайт-клиент)
- legkiishag.ru — Центр подологии, Москва
- Владелец: Шмидт Виктория Викторовна
- Стек: Next.js
- Реквизиты: счёт 40817810638126977423, ПАО Сбербанк, БИК 044525225

## Партнёры

### ОДИСпро (hardware, СКУД/CV)
- Контроллер: 2 камеры, ANPR 99.6%/220мс, до 62 на объект, скидка 20%
- Кастомные CV-модели: датасет от ST8-AI, права наши
- Договор: Dogovor_ST8AI_ODISPro.docx
- Эксклюзив по дефектоскопии: 12 месяцев
- White label, NDA

## Технический стек

```
Backend:     Python / FastAPI / PostgreSQL (Alembic) / ClickHouse / Redis
Frontend:    Next.js 15 / React / TypeScript
Mobile:      Flutter / Dart
Боты:        aiogram 3.x / FSM / webhook (никогда polling)
CV:          PyTorch + YOLO / OpenCV / Albumentations / ONNX
Infra:       Docker Compose
AI:          Anthropic Claude API (claude-sonnet-4-20250514)
Интеграции:  iiko REST / MCRM Superkit / 1С / Telegram / Мессенджер Макс
```

## Библиотека агентов

9 агентов, установка: `cp -r st8-agents/* ~/.claude/agents/`

| Агент | Роль |
|-------|------|
| st8-ai-director | Оркестратор |
| st8-backend-architect | FastAPI / PostgreSQL / ClickHouse |
| st8-security-auditor | Security review (≥3–5 проблем) |
| st8-integration-engineer | iiko / MCRM / 1С / Макс |
| st8-bot-developer | aiogram 3.x / FSM |
| st8-cv-vision-engineer | ОДИСпро / YOLO / дефектоскопия |
| st8-kp-architect | КП по стандарту ST8 |
| st8-sales-strategist | Переговоры / пайплайн |
| st8-horeca-consultant | Пресейл HoReCa |
| st8-qa-engineer | QA перед сдачей |
