# Requirements: Jarvis ST8-AI

**Defined:** 2026-04-15
**Core Value:** Jarvis должен отвечать точно и мгновенно — любая задержка или неверный ответ стоит реальной сделки.

## v1.0 Requirements — Smart Model Routing

### Routing

- [x] **ROUTE-01**: Система определяет модель для запроса до вызова API (проактивный роутинг)
- [ ] **ROUTE-02**: Запросы короче 100 токенов без признаков сложности маршрутизируются на Haiku
- [ ] **ROUTE-03**: Запросы с кодом, анализом документов или длиной > 500 токенов маршрутизируются на Sonnet
- [ ] **ROUTE-04**: Правила маршрутизации (пороги, ключевые слова) настраиваются в `.env` без правки кода
- [x] **ROUTE-05**: При неопределённой сложности — fallback на существующий ST8ModelRouter (quality cascade)

### Metrics

- [ ] **METRIC-01**: Каждый вызов модели логирует: имя модели, input tokens, output tokens, cost $ в `jarvis_live.log`
- [ ] **METRIC-02**: Команда `/stats` в Telegram возвращает агрегированную сводку за текущий день (кол-во вызовов, токены, сумма расходов по моделям)

## v2 Requirements (Future)

### Advanced Routing

- **ROUTE-06**: Роутинг на основе агента (Sales Hunter всегда Sonnet, простые ответы всегда Haiku)
- **ROUTE-07**: A/B тестирование порогов — автоматически выбирает оптимальные пороги по качеству

### Monitoring

- **METRIC-03**: Еженедельный отчёт о стоимости токенов в Telegram (понедельник 09:00)
- **METRIC-04**: Алерт в Telegram если дневной расход > $X

## Out of Scope

| Feature | Reason |
|---------|--------|
| Замена ST8ModelRouter | Сохраняем quality cascade как fallback — не трогаем |
| Web-дашборд метрик | Только лог-файл в v1.0, дашборд в будущем |
| Роутинг через OpenRouter | Нет нужды в доп. зависимостях — Anthropic API достаточно |
| Изменение prompts агентов | Не в scope этого milestone |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ROUTE-01 | Phase 1 | Complete |
| ROUTE-02 | Phase 1 | Pending |
| ROUTE-03 | Phase 1 | Pending |
| ROUTE-04 | Phase 1 | Pending |
| ROUTE-05 | Phase 1 | Complete |
| METRIC-01 | Phase 2 | Pending |
| METRIC-02 | Phase 2 | Pending |

**Coverage:**
- v1.0 requirements: 7 total
- Mapped to phases: 7
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-15*
*Last updated: 2026-04-15 after milestone v1.0 initialization*
