import asyncio
import json
import os
import re
import urllib.request
import warnings
import logging
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')
logging.disable(logging.CRITICAL)

import pytz
from dotenv import load_dotenv
import anthropic
from telegram import Bot
from telegram.error import TelegramError

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

# ── Mem0 long-term memory (lazy init) ────────────────────────────────────────
_mem0_instance = None

def _get_mem0():
    global _mem0_instance
    if _mem0_instance is not None:
        return _mem0_instance
    try:
        from mem0 import Memory
        config = {
            'llm': {
                'provider': 'anthropic',
                'config': {
                    'model': 'claude-haiku-4-5-20251001',
                    'api_key': os.getenv('ANTHROPIC_API_KEY'),
                }
            },
            'embedder': {
                'provider': 'huggingface',
                'config': {'model': 'multi-qa-MiniLM-L6-cos-v1'}
            },
            'vector_store': {
                'provider': 'qdrant',
                'config': {
                    'collection_name': 'jarvis_mem',
                    'path': os.path.join(os.path.dirname(__file__), 'mem0_db'),
                    'embedding_model_dims': 384,
                }
            }
        }
        _mem0_instance = Memory.from_config(config)
    except Exception:
        _mem0_instance = None
    return _mem0_instance


# ═══════════════════════════════════════════════════════
#  ST8-AI SUPER AGENTS — встроены в Jarvis
# ═══════════════════════════════════════════════════════

BUILTIN_AGENTS = {
    "sales-hunter": """Ты ST8-AI Sales Hunter — лучший холодный продажник России.
Твоя задача: взять холодный лид и провести его от первого контакта до назначенной встречи или демо.

Этапы которыми владеешь в совершенстве:
1. РАЗВЕДКА — по названию компании/сегменту определяешь: кто ЛПР, какая боль, какой крючок зайдёт
2. ПЕРВЫЙ КОНТАКТ — цепляющее сообщение/скрипт звонка: 15 секунд, одна боль, один вопрос
3. КВАЛИФИКАЦИЯ — BANT за 3 вопроса: есть ли бюджет, кто решает, есть ли потребность, когда нужно
4. ПРОГРЕВ — серия из 3-5 касаний (день 1 / день 3 / день 7 / день 14) с нарастающей ценностью
5. НАЗНАЧЕНИЕ ВСТРЕЧИ — конкретное предложение с датой, не "давайте созвонимся когда-нибудь"

Для каждого лида из хаба даёшь:
- Крючок: что именно зацепит этого клиента (боль сегмента)
- Первое сообщение: готовый текст для Telegram/звонка (до 3 предложений)
- Скрипт квалификации: 3 вопроса которые нужно задать
- Follow-up план: что писать если не ответил

Правила холодного outreach:
- Никогда не начинай с "Добрый день, меня зовут..."
- Первая фраза = боль клиента или провокационный вопрос
- Одно сообщение — одна мысль, одно действие
- Персонализация обязательна: упоминай сегмент, конкурентов, конкретную боль
- Дедлайн или причина написать сейчас — всегда

Контекст ST8-AI: AI-автоматизация, 47 проектов, окупаемость от 3 мес, 94% точность.
Пакеты: Базовый 65к / Бизнес 165к / Сеть 385к.
Сегменты: HoReCa, ритейл, логистика, производство.
Никогда не упоминай WhatsApp.

ВАЖНО: Ты и есть агент-продажник. Ты работаешь прямо здесь в этом чате.
Не спрашивай "где продажник" — ты он и есть. Не говори что нужно куда-то "подключиться".
Действуй сам: давай скрипты, тексты, стратегию прямо сейчас.""",

    "sales-closer": """Ты ST8-AI Sales Closer — эксперт по закрытию сделок.
Твоя задача: помочь Алексею закрыть конкретную сделку прямо сейчас.

Техники: SPIN, BANT, MEDDIC, Challenger Sale.
Когда клиент говорит — даёшь конкретный скрипт ответа.

"Дорого" → 3 варианта ответа: через ROI, через сравнение, через рассрочку
"Подумаю" → выясняешь реальное возражение, даёшь дедлайн
"Не сейчас" → фиксируешь дату, оставляешь зацепку
"Есть другие предложения" → переводишь на уникальность ST8-AI

Контекст ST8-AI: 47 проектов, 94% точность, окупаемость от 3 мес.
Пакеты: Базовый от 65к, Бизнес от 165к, Сеть от 385к.

Всегда давай конкретный текст который можно скопировать и отправить клиенту.""",

    "objection-handler": """Ты ST8-AI Objection Handler — специалист по возражениям.
Разбираешь каждое возражение и даёшь 3 варианта ответа в разных стилях.

Стиль 1 — Мягкий: понимание + логика + предложение
Стиль 2 — Напористый: факты + срочность + прямой вопрос  
Стиль 3 — Вопросом: переводишь возражение в вопрос клиенту

Топ возражений ST8-AI:
- "Дорого" / "Нет бюджета"
- "Нам это не нужно" / "У нас всё работает"
- "Давайте позже" / "Сейчас не время"
- "Я должен согласовать с руководством"
- "Мы уже работаем с другими"
- "Не уверены в результате"

После каждого варианта — короткое объяснение почему этот стиль работает.""",

    "kp-writer": """Ты ST8-AI KP Writer — пишешь убийственные коммерческие предложения.

Стиль документов ST8-AI:
- Без воды, каждое слово продаёт
- Начинаешь с боли клиента, а не с описания компании
- Цифры везде: ROI, окупаемость, % точности
- Социальное доказательство: 47 проектов, 94% точность, 0 провальных внедрений
- Окупаемость от 3 месяцев
- Эксклюзивность по городу/сегменту

Структура КП:
1. Заголовок — боль клиента одной фразой
2. Ситуация — что происходит у них сейчас
3. Решение — что конкретно делает ST8-AI
4. Результат — цифры и сроки
5. Пакеты и цены
6. Следующий шаг — конкретное действие

Интеграции: iiko, R-Keeper, 1С, MCRM, Telegram, Мессенджер Макс.
Никогда не упоминай WhatsApp.""",

    "deal-analyst": """Ты ST8-AI Deal Analyst — стратег по сделкам.
Анализируешь текущую ситуацию по клиенту и говоришь что делать дальше.

Твой анализ включает:
1. Стадия сделки: холодный/тёплый/горячий/зависший
2. Главный стопор: цена/доверие/время/технические вопросы/согласование
3. Следующий шаг: конкретное действие с текстом сообщения или скриптом звонка
4. Дедлайн: когда и как создать срочность
5. Риск: что может убить сделку и как предотвратить

Используй OODA: Observe (что происходит) → Orient (почему) → Decide (что делать) → Act (конкретный текст/скрипт).

Всегда заканчивай конкретным следующим шагом с готовым текстом.""",

    "st8-kp-architect": """Ты ST8-AI KP Architect — лучший архитектор коммерческих предложений в России.
Ты не просто пишешь КП — ты проектируешь убеждение. Каждый элемент документа бьёт в конкретную боль клиента.

Твои принципы:
- Структура КП — это воронка: боль → осознание → решение → доказательство → действие
- Никогда не начинай с "О нас" — начинай с ситуации клиента
- Каждый блок должен отвечать на вопрос: "И что мне с этого?"
- Цифры заменяют слова: не "быстро", а "за 14 дней"; не "выгодно", а "ROI 280% за 6 месяцев"

Архитектура сильного КП для ST8-AI:
1. ЗАГОЛОВОК — боль одной фразой (не название компании!)
2. СИТУАЦИЯ — 3 предложения: что сейчас происходит у клиента и чего это стоит
3. ПРОБЛЕМА — почему текущий подход не работает (конкретно для их сегмента)
4. РЕШЕНИЕ — что делает ST8-AI, без технического жаргона
5. МЕХАНИКА — как именно это работает, шаги внедрения
6. ДОКАЗАТЕЛЬСТВА — кейсы, цифры, 47 проектов, 94% точность
7. ПАКЕТЫ — Базовый 65к / Бизнес 165к / Сеть 385к с расшифровкой ценности каждого
8. ROI-КАЛЬКУЛЯТОР — считаешь окупаемость под конкретный бизнес клиента
9. СЛЕДУЮЩИЙ ШАГ — одно простое действие с дедлайном

Сегменты: HoReCa (iiko/R-Keeper), ритейл (1С), логистика, производство.
Интеграции: iiko, R-Keeper, 1С, MCRM, Telegram, Мессенджер Макс.
Никогда не упоминай WhatsApp.

Всегда спрашивай: для какого сегмента, какая боль, какой бюджет — и делаешь КП точно под это.""",

    "st8-sales-strategist": """Ты ST8-AI Sales Strategist — стратег продаж уровня топ-консультанта McKinsey, специализирующийся на B2B-продажах AI-решений в России.

Твоя экспертиза:
- Стратегия выхода на холодного клиента (outreach, первый контакт, прогрев)
- Построение воронки от первого касания до подписания договора
- Работа с ЛПР (лицо принимающее решение) и центром закупок
- Многоуровневые продажи: собственник / коммерческий директор / IT / финдиректор
- Конкурентное позиционирование ST8-AI против самописных решений и конкурентов

Методологии которыми владеешь: MEDDIC, Sandler, Challenger Sale, Value Selling, Gap Selling.

Для каждой задачи даёшь:
1. Стратегию: какой подход и почему
2. Тактику: конкретные шаги с текстами/скриптами
3. Временную шкалу: что делать на неделе 1, 2, 3
4. Метрики: как понять что движемся правильно
5. Запасной план: если не отвечают / отказывают

Контекст ST8-AI: AI-автоматизация для HoReCa, ритейла, логистики, производства.
Пакеты: Базовый 65к / Бизнес 165к / Сеть 385к. Окупаемость от 3 мес. 47 проектов. 94% точность.
Никогда не упоминай WhatsApp.""",

    "st8-horeca-consultant": """Ты ST8-AI HoReCa Consultant — лучший эксперт по автоматизации ресторанного бизнеса и гостиничного сектора в России.

Твоя экспертиза — глубокое понимание боли HoReCa:
- Нехватка персонала и высокая текучка
- Потери на кухне: пересортица, списания, воровство
- Средний чек падает, гости не возвращаются
- Управляющие тонут в операционке, нет времени на развитие
- Интеграции: iiko, R-Keeper, 1С, MCRM, Poster, Frontpad

Что умеет ST8-AI для HoReCa:
- AI-анализ меню: какие позиции убивают маржу, что поднять/убрать
- Прогноз спроса: сколько заготовить, чтобы не выбрасывать и не 86'ить
- Умные напоминания гостям: возвращаемость +30-40%
- Анализ отзывов: что реально раздражает гостей
- Автоматические отчёты для управляющего каждое утро
- Бот для персонала: инструкции, стандарты, стоп-листы

Говоришь языком ресторатора: "гость", "средний чек", "оборот стола", "86'd", "фудкост", "GP", "выручка на посадочное место".

Для каждого клиента определяешь:
- Тип заведения (ресторан/кафе/сеть/отель/фастфуд)
- Главная боль прямо сейчас
- Конкретная функция ST8-AI которая закроет эту боль
- ROI в рублях и месяцах

Никогда не упоминай WhatsApp.""",

    "st8-bot-developer": """Ты ST8-AI Bot Developer — ведущий разработчик Telegram-ботов и AI-интеграций в экосистеме ST8-AI.

Технический стек которым владеешь:
- Python: python-telegram-bot, aiogram, telebot
- AI/ML: Anthropic Claude API, OpenAI, Whisper (голос → текст)
- Базы данных: SQLite, PostgreSQL, Redis (кэш/очереди)
- Интеграции: iiko API, R-Keeper XML, 1С HTTP-сервисы, MCRM, amoCRM
- Инфраструктура: Windows Server, Linux VPS, systemd/supervisor, watchdog-паттерн
- Мессенджеры: Telegram Bot API, Мессенджер Макс

Что умеешь:
- Проектировать архитектуру бота от нуля до продакшена
- Отлаживать конфликты polling (getUpdates), race conditions, утечки памяти
- Строить multi-agent системы с роутингом запросов
- Настраивать автозапуск и watchdog для бесперебойной работы
- Интегрировать бота с кассовыми системами HoReCa и ритейла

Стиль ответов:
- Даёшь рабочий код, не абстракции
- Объясняешь почему именно такое решение
- Указываешь подводные камни и как их обойти
- Если вопрос про ST8-AI систему — даёшь конкретику по нашей архитектуре

Никогда не упоминай WhatsApp.""",

    "st8-backend-architect": """Ты ST8-AI Backend Architect — senior-архитектор бэкенд-систем с 15+ годами опыта в enterprise и стартапах.

Специализация:
- Проектирование масштабируемых AI-систем для бизнеса
- API-дизайн: REST, webhooks, интеграционные шины
- Очереди и асинхронность: фоновые задачи, retry-логика, dead-letter
- Хранение данных: выбор БД под задачу, схемы, индексы, миграции
- Безопасность: секреты, токены, rate limiting, аутентификация
- Мониторинг: логирование, алерты, watchdog-паттерны

Для ST8-AI контекст:
- Python-монолиты с scheduler + watchdog
- Telegram Bot API как основной интерфейс
- Интеграции с iiko, R-Keeper, 1С через HTTP/XML
- Хранение лидов и памяти в JSON + mem0/qdrant
- Windows Server как основная среда деплоя

Принципы которым следуешь:
- Простота > сложность: не усложняй без причины
- Отказоустойчивость: что будет если упадёт, как восстановиться
- Наблюдаемость: логируй всё что нужно для отладки
- Безопасность по умолчанию: никаких секретов в коде

Даёшь конкретные решения с кодом, объясняешь trade-offs, предупреждаешь о ловушках.""",

    "st8-security-auditor": """Ты ST8-AI Security Auditor — эксперт по безопасности приложений и инфраструктуры уровня OSCP/CEH.

Твоя специализация:
- Аудит Python-приложений: инъекции, небезопасные десериализации, path traversal
- Безопасность API: аутентификация, авторизация, rate limiting, токены
- Секреты и конфигурация: .env файлы, API-ключи, их хранение и ротация
- Telegram Bot Security: защита от несанкционированного доступа, валидация update
- Безопасность Windows Server: права процессов, файловые разрешения
- Зависимости: устаревшие пакеты, CVE, supply chain риски

Методология аудита:
1. РАЗВЕДКА — что запущено, что открыто, что хранит секреты
2. АНАЛИЗ КОДА — OWASP Top 10, логические уязвимости, небезопасные паттерны
3. КОНФИГУРАЦИЯ — права доступа, открытые порты, дефолтные пароли
4. ДАННЫЕ — что хранится, где, кто имеет доступ
5. РЕКОМЕНДАЦИИ — приоритизированный список: критично / высоко / средне / низко

Для ST8-AI системы знаешь:
- Архитектуру: jarvis.py + scheduler.py + watchdog + .env
- Риски: утечка API-ключей, несанкционированный доступ к боту, небезопасное хранение лидов

Даёшь конкретные исправления с кодом, не абстрактные советы.""",

    "st8-ai-director": """Ты ST8-AI Director — визионер и стратег развития AI-продуктов уровня Chief AI Officer.

Твоя экспертиза:
- Продуктовая стратегия AI-решений для SMB в России
- Конкурентный анализ: кто что делает на рынке AI-автоматизации
- Roadmap: что строить следующим, почему именно это, как приоритизировать
- Монетизация: модели ценообразования, пакеты, upsell, LTV
- Партнёрства: интеграторы, дистрибьюторы, отраслевые ассоциации
- Позиционирование: как ST8-AI отличается от конкурентов и как это транслировать рынку

Продуктовый портфель ST8-AI:
- Базовый пакет 65к: один сегмент, базовая автоматизация
- Бизнес пакет 165к: несколько направлений, аналитика
- Сеть 385к: мультилокационный, корпоративные интеграции
- Целевые сегменты: HoReCa, ритейл, логистика, производство
- Tech stack: Claude AI, Python, Telegram, iiko/R-Keeper/1С/MCRM

Для каждого стратегического вопроса:
1. Ситуация: где мы сейчас
2. Возможность: что открывается
3. Решение: конкретный шаг с обоснованием
4. Риски: что может пойти не так
5. Метрика успеха: как поймём что сработало

Мыслишь горизонтом 3-6-12 месяцев, но даёшь конкретику на ближайшие 2 недели.""",
}

EXTERNAL_AGENTS_DIR = os.path.expanduser(r"~\.claude\agents")

def load_external_agents():
    """Загружает агентов из ~/.claude/agents/*.md"""
    agents = {}
    if not os.path.exists(EXTERNAL_AGENTS_DIR):
        return agents
    for fname in os.listdir(EXTERNAL_AGENTS_DIR):
        if fname.endswith(".md"):
            name = fname[:-3]
            try:
                with open(os.path.join(EXTERNAL_AGENTS_DIR, fname), encoding="utf-8") as f:
                    content = f.read()
                # Извлекаем description или берём весь контент
                agents[name] = content
            except Exception:
                pass
    return agents

ALL_AGENTS = {**BUILTIN_AGENTS}
ALL_AGENTS.update(load_external_agents())

AGENT_ROUTER_PROMPT = """Ты роутер агентов ST8-AI. Определи какой агент нужен для ответа на сообщение.

Доступные агенты:
- sales-hunter: холодный лид, первый контакт, как написать/позвонить, квалификация, follow-up серия, прогрев до встречи
- sales-closer: клиент говорит дорого/подумаю/не сейчас/есть другие — нужен скрипт закрытия прямо сейчас
- objection-handler: нужны варианты ответов на конкретное возражение (3 стиля)
- kp-writer: написать готовое КП, питч, предложение для конкретного клиента
- deal-analyst: что происходит с этой сделкой, почему зависла, что делать дальше
- st8-kp-architect: как выстроить структуру КП, что включить, как убедить через документ
- st8-sales-strategist: стратегия выхода на рынок/сегмент, построение воронки, outreach
- st8-horeca-consultant: вопросы про рестораны, кафе, отели, iiko, R-Keeper, HoReCa-боли
- st8-bot-developer: разработка ботов, Telegram API, код, интеграции, технические баги
- st8-backend-architect: архитектура системы, API-дизайн, БД, масштабирование, деплой
- st8-security-auditor: безопасность кода, утечки ключей, аудит, уязвимости
- st8-ai-director: стратегия развития ST8-AI как продукта, roadmap, позиционирование, рынок
- none: общий вопрос, личное, погода, что-то не про бизнес

Ответь ТОЛЬКО именем агента без пояснений. Например: sales-closer"""


def route_to_agent(user_text, claude_client, model):
    """Определяет нужного агента. Поддерживает прямой вызов: /agent-name или !agent-name."""
    # Прямой вызов: /sales-hunter текст или !deal-analyst текст
    stripped = user_text.strip()
    for prefix in ('/', '!'):
        if stripped.startswith(prefix):
            candidate = stripped[len(prefix):].split()[0].lower().rstrip(':')
            if candidate in ALL_AGENTS:
                return candidate
    try:
        response = claude_client.messages.create(
            model=model,
            max_tokens=50,
            messages=[
                {"role": "user", "content": f"{AGENT_ROUTER_PROMPT}\n\nСообщение: {user_text}"}
            ]
        )
        agent_name = response.content[0].text.strip().lower()
        return agent_name if agent_name in ALL_AGENTS else "none"
    except Exception:
        return "none"


_JARVIS_PROMPT_CACHE = {'prompt': None, 'hub_block': None, 'mtime': None}


def _load_agent_memory_md():
    """Читает все .md файлы из agent_memory/ и ключевые файлы из st8-memory-bank/."""
    parts = []

    # Все .md из agent_memory/
    mem_dir = os.path.join(BASE_DIR, 'agent_memory')
    if os.path.isdir(mem_dir):
        for fname in sorted(os.listdir(mem_dir)):
            if not fname.endswith('.md'):
                continue
            try:
                with open(os.path.join(mem_dir, fname), 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                if content:
                    parts.append(f"[{fname}]\n{content[:1000]}")
            except Exception:
                pass

    # Ключевые файлы из st8-memory-bank/
    bank_dir = os.path.join(BASE_DIR, 'st8-memory-bank')
    bank_files = ['airi_context.md', 'clientPipeline.md', 'productContext.md', 'activeContext.md']
    for fname in bank_files:
        path = os.path.join(bank_dir, fname)
        if not os.path.exists(path):
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw = f.read()
            # Убираем мусорные AUTO UPDATE строки
            lines = [l for l in raw.splitlines() if '> AUTO UPDATE' not in l]
            content = '\n'.join(lines).strip()
            if content:
                parts.append(f"[{fname}]\n{content[:1200]}")
        except Exception:
            pass

    return '\n\n'.join(parts)


# ─── AGENT SESSION LOG ───────────────────────────────────────────────────────
_SESSION_LOG_PATH = os.path.join(os.path.dirname(__file__), 'jarvis_session_log.json')
_MAX_SESSION_ENTRIES = 5


def _load_session_log():
    try:
        with open(_SESSION_LOG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _save_session_entry(agent_name, user_text, response_snippet):
    log = _load_session_log()
    log.append({
        'time': datetime.now().strftime('%d.%m %H:%M'),
        'agent': agent_name if agent_name != 'none' else 'jarvis',
        'query': user_text[:80],
        'result': response_snippet[:200],
    })
    if len(log) > _MAX_SESSION_ENTRIES:
        log = log[-_MAX_SESSION_ENTRIES:]
    try:
        with open(_SESSION_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _build_session_block():
    log = _load_session_log()
    if not log:
        return ''
    lines = [
        f"[{e['time']}] {e['agent']}: {e['query'][:60]} -> {e['result'][:120]}"
        for e in log[-3:]
    ]
    return '\n\n=== ЭСТАФЕТА АГЕНТОВ (что уже сделано) ===\n' + '\n'.join(lines)


# Правила авто-цепочек: {агент: [(паттерн_в_ответе, след_агент, подсказка)]}
AGENT_CHAIN_HINTS = {
    'sales-hunter': [
        (r'bant\+|квалифицирован|тёплый лид|встреча назначена|готов к встрече',
         'deal-analyst', '📊 Хотите анализ сделки?'),
    ],
    'deal-analyst': [
        (r'написать кп|нужно кп|подготовить предложение|отправить кп|составить кп',
         'st8-kp-architect', '📄 Составить КП?'),
        (r'возражени|говорит дорого|сомневается|не готов платить',
         'objection-handler', '🛡 Разобрать возражение?'),
        (r'холодный|нет ответа|не отвечает|реанимировать',
         'sales-hunter', '🎯 Написать скрипт прогрева?'),
    ],
    'st8-kp-architect': [
        (r'написать текст|полный текст|заполнить шаблон',
         'kp-writer', '✍️ Написать полный текст КП?'),
    ],
    'kp-writer': [
        (r'возражени|клиент сомневается|ответить на',
         'objection-handler', '🛡 Подготовить ответы на возражения?'),
    ],
    'st8-sales-strategist': [
        (r'первый контакт|написать лиду|скрипт звонка|холодный',
         'sales-hunter', '🎯 Составить скрипт?'),
    ],
}


def _detect_chain_hint(agent_name, response_text):
    """Возвращает подсказку о следующем агенте или пустую строку."""
    for pattern, next_agent, hint in AGENT_CHAIN_HINTS.get(agent_name, []):
        if re.search(pattern, response_text, re.IGNORECASE):
            return f'\n\n—\n➡️ {hint} (/{next_agent})'
    return ''


_MEMPALACE_CLIENT = None

def _mempalace_search(query, n_results=3):
    """Семантический поиск по mempalace ChromaDB."""
    global _MEMPALACE_CLIENT
    try:
        import chromadb
        if _MEMPALACE_CLIENT is None:
            palace_path = os.path.join(os.path.expanduser('~'), '.mempalace', 'palace')
            _MEMPALACE_CLIENT = chromadb.PersistentClient(path=palace_path)
        col = _MEMPALACE_CLIENT.get_collection('mempalace_drawers')
        results = col.query(query_texts=[query], n_results=n_results, include=['documents'])
        docs = results.get('documents', [[]])[0]
        return [d[:400] for d in docs if d]
    except Exception:
        return []


def _build_hub_data():
    """Возвращает (jarvis_prompt, hub_block) с кэшированием по mtime."""
    try:
        mtime = os.path.getmtime(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    except OSError:
        mtime = None
    if _JARVIS_PROMPT_CACHE['prompt'] and _JARVIS_PROMPT_CACHE['mtime'] == mtime:
        return _JARVIS_PROMPT_CACHE['prompt'], _JARVIS_PROMPT_CACHE['hub_block']

    leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    total = len(leads) if leads else 0
    if leads:
        lines = []
        for lead in leads[:15]:
            name = lead.get('company_name', '—')
            seg = lead.get('segment', '—')
            lpr = lead.get('lpr', '—')
            phone = lead.get('phone', '—')
            status = lead.get('status', '—')
            lines.append(f"• {name} [{seg}] ЛПР: {lpr}, тел: {phone}, статус: {status}")
        leads_summary = "\n".join(lines)
    else:
        leads_summary = 'Лидов нет'

    context_md = _load_agent_memory_md()
    context_section = f"\n\n=== КОНТЕКСТ ST8-AI ===\n{context_md}" if context_md else ""

    hub_block = f"""=== ХАБ ЛИДОВ ST8-AI (всего: {total}) ===
{leads_summary}{context_section}

ПРАВИЛА:
- У тебя есть прямой доступ к этим данным — используй их сразу
- Ты работаешь напрямую в этом чате — не говори что нужно "подключиться к агенту" или "передать запрос"
- Ты и есть тот агент/специалист — действуй сам, отвечай сразу
- Никогда не говори "нет доступа" или "нет подключения" — всё что нужно уже есть выше"""

    jarvis_prompt = f"""Ты Jarvis — персональный AI-ассистент Алексея Леонидовича (ST8-AI).

{hub_block}

Ты можешь:
- Видеть и анализировать все лиды из хаба выше
- Искать конкретного клиента по названию
- Готовить ответы, КП, скрипты звонков
- Анализировать статусы и рекомендовать следующие шаги

Отвечай коротко, конкретно, по-деловому."""

    _JARVIS_PROMPT_CACHE['prompt'] = jarvis_prompt
    _JARVIS_PROMPT_CACHE['hub_block'] = hub_block
    _JARVIS_PROMPT_CACHE['mtime'] = mtime
    return jarvis_prompt, hub_block


def _build_jarvis_system_prompt():
    jarvis_prompt, _ = _build_hub_data()
    return jarvis_prompt


def process_with_agent(user_text, history, claude_client, model):
    """Обрабатывает сообщение через нужного агента с межагентским контекстом."""
    agent_name = route_to_agent(user_text, claude_client, model)

    jarvis_prompt, hub_block = _build_hub_data()

    # Контекст предыдущих агентских шагов (эстафета)
    session_block = _build_session_block()

    # Семантический поиск по mempalace
    palace_hits = _mempalace_search(user_text, n_results=3)
    palace_block = ""
    if palace_hits:
        palace_block = "\n\n=== ПАМЯТЬ (mempalace) ===\n" + "\n---\n".join(palace_hits)

    if agent_name == "none":
        system_prompt = jarvis_prompt + session_block + palace_block
    else:
        agent_prompt = ALL_AGENTS.get(agent_name, "")
        base = f"{agent_prompt}\n\n---\n\n{hub_block}" if agent_prompt else jarvis_prompt
        system_prompt = base + session_block + palace_block

    messages = []
    for h in history[-10:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_text})

    try:
        kwargs = {
            "model": model,
            "max_tokens": 1500,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = claude_client.messages.create(**kwargs)
        reply = response.content[0].text.strip()

        # Сохраняем в эстафету
        _save_session_entry(agent_name, user_text, reply)

        # Подсказка следующего агента в цепочке
        chain_hint = _detect_chain_hint(agent_name, reply)

        return reply + chain_hint
    except Exception as e:
        if "529" in str(e) or "overloaded" in str(e).lower():
            import time
            time.sleep(15)
            try:
                response = claude_client.messages.create(**kwargs)
                reply = response.content[0].text.strip()
                _save_session_entry(agent_name, user_text, reply)
                return reply + _detect_chain_hint(agent_name, reply)
            except Exception:
                pass
        return f"[Ошибка агента {agent_name}]: {e}"


JARVIS_BOT_TOKEN = os.getenv('JARVIS_BOT_TOKEN')
JARVIS_CHAT_ID = 6152243830
YULIA_CHAT_ID = 5438530925
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CLAUDE_MODEL = 'claude-sonnet-4-6'

if not ANTHROPIC_API_KEY:
    raise RuntimeError('ANTHROPIC_API_KEY must be set for Jarvis')

claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
MOSCOW_TZ = pytz.timezone('Europe/Moscow')
LAST_JARVIS_RUN = {}

BASE_DIR = os.path.dirname(__file__)
MEMORY_PATH = os.path.join(BASE_DIR, 'jarvis_memory.json')
OFFSET_PATH = os.path.join(BASE_DIR, 'jarvis_offset.json')
AGENT_MEMORY_DIR = os.path.join(BASE_DIR, 'agent_memory')
MAX_MEMORY = 20
POLL_INTERVAL = 3

# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# AGENT ROUTER
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

AGENTS_DIR = os.path.join(os.path.expanduser('~'), '.claude', 'agents')

AGENT_KEYWORDS = {
    'st8-sales-strategist': [
        'дожим', 'follow-up', 'написать клиенту', 'касание', 'не отвечает',
        'переговоры', 'кристина', 'калинка', 'белый кролик', 'лаки груп',
        'атель', 'раппопорт', 'зарьков', 'панченко', 'сделка', 'закрыть',
    ],
    'st8-kp-architect': [
        'кп', 'коммерческое предложение', 'написать кп', 'предложение для', 'смета',
    ],
    'st8-horeca-consultant': [
        'ресторан', 'хорека', 'horeca', 'гость', 'банкет', 'хокку',
    ],
    'st8-backend-architect': [
        'fastapi', 'эндпоинт', 'архитектура бд', 'backend', 'celery', 'postgresql',
    ],
    'st8-bot-developer': [
        'хокку бот', 'доработать бота', 'новый бот', 'хендлер', 'webhook', 'aiogram',
    ],
    'st8-security-auditor': [
        'безопасность', 'уязвимость', 'аудит кода', 'security review',
    ],
    'st8-qa-engineer': [
        'протестировать', 'тестирование', 'баг', 'qa', 'чеклист теста',
    ],
    'st8-integration-engineer': [
        'интеграция', 'iiko', 'mcrm', 'r-keeper', '1с', 'подключить api',
    ],
    'st8-cv-vision-engineer': [
        'камера', 'cv модель', 'компьютерное зрение', 'скуд', 'дефектоскопия',
    ],
    'st8-ai-director': [
        'декомпозируй', 'расставь приоритеты', 'план проекта', 'кто делает', 'раздай задачи',
    ],
}

# Цепочки агентов: один запрос -> несколько агентов последовательно
AGENT_CHAINS = {
    'новый клиент кп':      ['st8-horeca-consultant', 'st8-kp-architect'],
    'подготовь кп':         ['st8-horeca-consultant', 'st8-kp-architect'],
    'кп для нового':        ['st8-horeca-consultant', 'st8-kp-architect'],
    'аудит и тест':         ['st8-security-auditor', 'st8-qa-engineer'],
    'проверь и задеплой':   ['st8-security-auditor', 'st8-qa-engineer'],
    'стратегия продаж':     ['st8-horeca-consultant', 'st8-sales-strategist'],
    'декомпозируй проект':  ['st8-ai-director', 'st8-backend-architect'],
}

# Карта клиентов для памяти агентов
CLIENT_SLUGS = {
    'калинка': 'kalinka', 'кристина': 'kalinka',
    'хокку': 'hokku', 'анастасия': 'hokku',
    'atelier': 'atelier', 'марк': 'atelier', 'ира': 'atelier',
    'рускимат': 'rusklimat', 'георгий': 'rusklimat',
    'лёгкий шаг': 'legkiishag', 'виктория': 'legkiishag',
    'белый кролик': 'white_rabbit', 'зарьков': 'white_rabbit',
    'лаки груп': 'lucky_group', 'панченко': 'lucky_group',
    'раппопорт': 'rapoport',
    'airi': 'airi', 'st8': 'st8_context', 'оселедец': 'airi', 'макаров': 'airi',
}


# в"Ђв"Ђв"Ђ Agent Memory в"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђ

def get_client_slug(text):
    msg_lower = text.lower()
    for key, slug in CLIENT_SLUGS.items():
        if key in msg_lower:
            return slug
    return None


def load_agent_memory(client_slug):
    """Load relevant memories for a client. Uses Mem0 semantic search if available,
    falls back to JSON file."""
    if not client_slug:
        return []

    mem = _get_mem0()
    if mem is not None:
        try:
            result = mem.get_all(user_id=client_slug)
            items = result.get('results', result) if isinstance(result, dict) else result
            # Convert Mem0 format to legacy [{ts, agent, user, response}] format
            entries = []
            for item in items[-30:]:
                memory_text = item.get('memory', '') if isinstance(item, dict) else str(item)
                ts = item.get('created_at', datetime.now().isoformat()) if isinstance(item, dict) else ''
                entries.append({
                    'ts': str(ts)[:19],
                    'agent': 'mem0',
                    'user': '',
                    'response': memory_text,
                })
            return entries
        except Exception:
            pass

    # Fallback: JSON file
    os.makedirs(AGENT_MEMORY_DIR, exist_ok=True)
    path = os.path.join(AGENT_MEMORY_DIR, f'{client_slug}.json')
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return []


def search_agent_memory(client_slug, query, limit=5):
    """Semantic search in client memories. Returns list of memory strings."""
    if not client_slug or not query:
        return []
    mem = _get_mem0()
    if mem is None:
        return []
    try:
        result = mem.search(query, user_id=client_slug, limit=limit)
        items = result.get('results', result) if isinstance(result, dict) else result
        return [item.get('memory', '') for item in items if isinstance(item, dict)]
    except Exception:
        return []


def save_agent_memory(client_slug, agent_name, user_msg, agent_response):
    """Save agent interaction to memory. Uses Mem0 if available, falls back to JSON."""
    if not client_slug:
        return

    mem = _get_mem0()
    if mem is not None:
        try:
            text = f"[{agent_name}] User: {user_msg[:200]} | Agent response: {agent_response[:400]}"
            mem.add(text, user_id=client_slug)
            return
        except Exception:
            pass

    # Fallback: JSON file
    os.makedirs(AGENT_MEMORY_DIR, exist_ok=True)
    path = os.path.join(AGENT_MEMORY_DIR, f'{client_slug}.json')
    memory = load_agent_memory(client_slug)
    memory.append({
        'ts': datetime.now().isoformat(timespec='seconds'),
        'agent': agent_name,
        'user': user_msg,
        'response': agent_response[:500],
    })
    memory = memory[-30:]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


# в"Ђв"Ђв"Ђ Agent Tools в"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђ

def tool_save_lead_status(company, status, comment=''):
    """Р—Р°РїРёСЃС‹РІР°РµС‚ СЃС‚Р°С‚СѓСЃ Р»РёРґР° РІ leads_status.md"""
    try:
        path = os.path.join(BASE_DIR, 'leads_status.md')
        date = datetime.now().strftime('%Y-%m-%d')
        line = f"| {date} | {company} | — | {status} | {comment} |\n"
        with open(path, 'a', encoding='utf-8') as f:
            f.write(line)
        return f"вњ… РЎС‚Р°С‚СѓСЃ СЃРѕС…СЂР°РЅС'РЅ: {company} в†' {status}"
    except Exception as exc:
        return f"вљ пёЏ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ СЃС‚Р°С‚СѓСЃР°: {exc}"


def tool_save_kp(company, content):
    """РЎРѕС…СЂР°РЅСЏРµС‚ РљРџ РІ РїР°РїРєСѓ kp/"""
    try:
        kp_dir = os.path.join(BASE_DIR, 'kp')
        os.makedirs(kp_dir, exist_ok=True)
        date = datetime.now().strftime('%Y%m%d')
        slug = re.sub(r'[^\w]', '_', company.lower())[:20]
        filename = f"KP_{slug}_{date}.md"
        path = os.path.join(kp_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# РљРџ — {company}\n\n{content}")
        return f"вњ… РљРџ СЃРѕС…СЂР°РЅРµРЅРѕ: kp/{filename}"
    except Exception as exc:
        return "Бот не настроен"


def tool_send_yulia(message):
    """РћС‚РїСЂР°РІР»СЏРµС‚ СЃРѕРѕР±С‰РµРЅРёРµ Р®Р»Рµ РІ Telegram"""
    if not JARVIS_BOT_TOKEN:
        return "Bot ne nastroyen"
    try:
        bot = Bot(token=JARVIS_BOT_TOKEN)
        full_msg = f"Jarvis -> Юля:\n\n{message}"
        return f"Ошибка отправки Юле: {exc}"
        data = urllib.parse.urlencode({"chat_id": YULIA_CHAT_ID, "text": full_msg}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{JARVIS_BOT_TOKEN}/sendMessage", data=data)
        urllib.request.urlopen(req, timeout=10)
        return "вњ… РЎРѕРѕР±С‰РµРЅРёРµ РѕС‚РїСЂР°РІР»РµРЅРѕ Р®Р»Рµ"
    except Exception as exc:
        return f"Oshibka otpravki Yule: {exc}"


def tool_save_task(task):
    """Р"РѕР±Р°РІР»СЏРµС‚ Р·Р°РґР°С‡Сѓ РІ activeContext.md"""
    try:
        path = os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md')
        date = datetime.now().strftime('%Y-%m-%d %H:%M')
        with open(path, 'a', encoding='utf-8') as f:
            f.write(f"\n- [ ] [{date}] {task}")
        return f"вњ… Р—Р°РґР°С‡Р° РґРѕР±Р°РІР»РµРЅР° РІ activeContext"
    except Exception as exc:
        return f"вљ пёЏ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ Р·Р°РґР°С‡Рё: {exc}"


def execute_actions(actions_text):
    """РџР°СЂСЃРёС‚ Рё РІС‹РїРѕР»РЅСЏРµС‚ РґРµР№СЃС‚РІРёСЏ РёР· С‚РµРєСЃС‚Р° Р°РіРµРЅС‚Р°"""
    results = []
    # [РЎРўРђРўРЈРЎ: РљР°Р»РёРЅРєР° | РґРѕР¶РёРј | РѕС‚РїСЂР°РІР»РµРЅ РІР°СЂРёР°РЅС‚ 3]
    for m in re.finditer(r'\[РЎРўРђРўРЈРЎ:\s*([^|]+)\|([^|]+)\|?([^\]]*)\]', actions_text):
        company, status, comment = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        results.append(tool_save_lead_status(company, status, comment))
    # [Р®Р›Р•: С‚РµРєСЃС‚ СЃРѕРѕР±С‰РµРЅРёСЏ]
    for m in re.finditer(r'\[Р®Р›Р•:\s*([^\]]+)\]', actions_text):
        results.append(tool_send_yulia(m.group(1).strip()))
    # [РљРџ: РљРѕРјРїР°РЅРёСЏ | С‚РµРєСЃС‚]
    for m in re.finditer(r'\[РљРџ:\s*([^|]+)\|([^\]]+)\]', actions_text):
        results.append(tool_save_kp(m.group(1).strip(), m.group(2).strip()))
    # [Р—РђР"РђР§Рђ: С‚РµРєСЃС‚]
    for m in re.finditer(r'\[Р—РђР"РђР§Рђ:\s*([^\]]+)\]', actions_text):
        results.append(tool_save_task(m.group(1).strip()))
    return results


# в"Ђв"Ђв"Ђ Agent Core в"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђ

def load_agent_prompt(agent_name):
    path = os.path.join(AGENTS_DIR, f'{agent_name}.md')
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def detect_agent(user_message):
    msg_lower = user_message.lower()
    for agent_name in AGENT_KEYWORDS:
        short = agent_name.replace('st8-', '')
        if f'@{agent_name}' in msg_lower or f'@{short}' in msg_lower:
            return agent_name
    for agent_name, keywords in AGENT_KEYWORDS.items():
        for kw in keywords:
            if kw in msg_lower:
                return agent_name
    return None


def detect_chain(user_message):
    msg_lower = user_message.lower()
    for trigger, chain in AGENT_CHAINS.items():
        if trigger in msg_lower:
            return chain
    return None


TOOLS_INSTRUCTION = """
Р•СЃР»Рё РЅСѓР¶РЅРѕ РІС‹РїРѕР»РЅРёС‚СЊ РґРµР№СЃС‚РІРёРµ — РґРѕР±Р°РІСЊ РІ РєРѕРЅРµС† РѕС‚РІРµС‚Р° РѕРґРёРЅ РёР· РјР°СЂРєРµСЂРѕРІ:
[РЎРўРђРўРЈРЎ: РљРѕРјРїР°РЅРёСЏ | СЃС‚Р°С‚СѓСЃ | РєРѕРјРјРµРЅС‚Р°СЂРёР№] — Р·Р°РїРёСЃР°С‚СЊ СЃС‚Р°С‚СѓСЃ РїРµСЂРµРіРѕРІРѕСЂРѕРІ
[Р®Р›Р•: С‚РµРєСЃС‚] — РѕС‚РїСЂР°РІРёС‚СЊ Р·Р°РґР°С‡Сѓ Р®Р»Рµ (СЂР°Р·СЂР°Р±РѕС‚С‡РёРєСѓ)
[РљРџ: РљРѕРјРїР°РЅРёСЏ | РєСЂР°С‚РєРѕРµ СЃРѕРґРµСЂР¶Р°РЅРёРµ РљРџ] — СЃРѕС…СЂР°РЅРёС‚СЊ РљРџ
[Р—РђР"РђР§Рђ: С‚РµРєСЃС‚] — РґРѕР±Р°РІРёС‚СЊ Р·Р°РґР°С‡Сѓ РІ РїР»Р°РЅ
РСЃРїРѕР»СЊР·СѓР№ РјР°СЂРєРµСЂС‹ С‚РѕР»СЊРєРѕ РµСЃР»Рё СЌС‚Рѕ СЂРµР°Р»СЊРЅРѕ РЅСѓР¶РЅРѕ РїРѕ РєРѕРЅС‚РµРєСЃС‚Сѓ.
"""


def call_agent(agent_name, user_message, history, client_memory=None, prefix='', client_slug=None):
    agent_prompt = load_agent_prompt(agent_name)
    if not agent_prompt:
        return None

    memory_bank = load_memory_bank()
    leads_summary = _leads_summary()

    # Client memory: use Mem0 semantic search if client_slug available
    client_memory_text = ''
    if client_slug:
        relevant = search_agent_memory(client_slug, user_message, limit=5)
        if relevant:
            client_memory_text = '\n\nRelevant client history (Mem0):\n' + '\n'.join(f'- {m}' for m in relevant)
    elif client_memory:
        lines = [f"[{e['ts']}] {e['agent']}: {e['response']}" for e in client_memory[-5:]]
        client_memory_text = '\n\nClient history:\n' + '\n'.join(lines)

    system = (
        f"{agent_prompt}\n\n"
        f"--- РљРѕРЅС‚РµРєСЃС‚ ST8-AI ---\n"
        f"Memory Bank:\n{memory_bank}\n\n"
        f"Р›РёРґС‹ РІ СЂР°Р±РѕС‚Рµ:\n{leads_summary}"
        f"{client_memory_text}\n\n"
        f"{TOOLS_INSTRUCTION}\n\n"
        f"РћС‚РІРµС‡Р°Р№ РєСЂР°С‚РєРѕ, РєРѕРЅРєСЂРµС‚РЅРѕ, РїРѕ РґРµР»Сѓ. Р'РµР· С€Р°Р±Р»РѕРЅРЅС‹С… С„СЂР°Р·."
    )

    messages = []
    for entry in history[-6:]:
        role = entry.get('role')
        content = entry.get('content', '')
        if role in ('user', 'assistant') and content:
            messages.append({"role": role, "content": content})
    user_content = f"{prefix}\n\n{user_message}" if prefix else user_message
    messages.append({"role": "user", "content": user_content})

    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=900,
            system=system,
            messages=messages,
        )
        result = response.content[0].text.strip()
        agent_short = agent_name.replace('st8-', '').replace('-', ' ').title()
        return agent_short, result
    except Exception as exc:
        return None, f"РћС€РёР±РєР° Р°РіРµРЅС‚Р° {agent_name}: {exc}"


def run_agent_or_chain(user_message, history):
    """Р—Р°РїСѓСЃРєР°РµС‚ РѕРґРЅРѕРіРѕ Р°РіРµРЅС‚Р° РёР»Рё С†РµРїРѕС‡РєСѓ, РІРѕР·РІСЂР°С‰Р°РµС‚ С„РёРЅР°Р»СЊРЅС‹Р№ РѕС‚РІРµС‚"""
    client_slug = get_client_slug(user_message)
    client_memory = load_agent_memory(client_slug) if client_slug else []

    # РџСЂРѕРІРµСЂСЏРµРј С†РµРїРѕС‡РєСѓ
    chain = detect_chain(user_message)
    if chain:
        outputs = []
        prev_output = ''
        for agent_name in chain:
            agent_short, result = call_agent(
                agent_name, user_message, history,
                client_memory=client_memory,
                prefix=prev_output,
                client_slug=client_slug,
            )
            if result:
                outputs.append(f"[{agent_short}]\n{result}")
                prev_output = result
                # Р'С‹РїРѕР»РЅСЏРµРј РґРµР№СЃС‚РІРёСЏ
                actions = execute_actions(result)
                if actions:
                    outputs.append('\n'.join(actions))
                # РЎРѕС…СЂР°РЅСЏРµРј РІ РїР°РјСЏС‚СЊ РєР»РёРµРЅС‚Р°
                if client_slug:
                    save_agent_memory(client_slug, agent_name, user_message, result)
        return '\n\n---\n\n'.join(outputs) if outputs else None

    # РћРґРёРЅРѕС‡РЅС‹Р№ Р°РіРµРЅС‚
    agent_name = detect_agent(user_message)
    if agent_name:
        agent_short, result = call_agent(
            agent_name, user_message, history,
            client_memory=client_memory,
            client_slug=client_slug,
        )
        if result:
            # Р'С‹РїРѕР»РЅСЏРµРј РґРµР№СЃС‚РІРёСЏ РёР· РѕС‚РІРµС‚Р°
            actions = execute_actions(result)
            action_text = '\n'.join(actions) if actions else ''
            # РЎРѕС…СЂР°РЅСЏРµРј РІ РїР°РјСЏС‚СЊ РєР»РёРµРЅС‚Р°
            if client_slug:
                save_agent_memory(client_slug, agent_name, user_message, result)
            full = f"[{agent_short}]\n{result}"
            if action_text:
                full += f"\n\n{action_text}"
            return full

    return None


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# CORE JARVIS
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

def now_moscow():
    return datetime.now(pytz.utc).astimezone(MOSCOW_TZ)


def load_memory():
    if not os.path.exists(MEMORY_PATH):
        return []
    with open(MEMORY_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_memory(messages):
    trimmed = messages[-MAX_MEMORY:]
    with open(MEMORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)


def load_offset():
    if not os.path.exists(OFFSET_PATH):
        return 0
    with open(OFFSET_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f).get('offset', 0)
        except Exception:
            return 0


def save_offset(offset):
    with open(OFFSET_PATH, 'w', encoding='utf-8') as f:
        json.dump({'offset': offset}, f)


def load_memory_bank():
    bank_dir = os.path.join(BASE_DIR, 'st8-memory-bank')
    files = ['activeContext.md', 'clientPipeline.md', 'productContext.md', 'systemPatterns.md']
    parts = []
    for fname in files:
        content = read_file(os.path.join(bank_dir, fname), max_chars=1000)
        if content:
            parts.append(f"=== {fname} ===\n{content}")
    return '\n\n'.join(parts)


def read_file(path, max_chars=1800):
    if not os.path.exists(path):
        return ''
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    return text[:max_chars]


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def load_markdown_table(path):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('|') and '|' in line[1:]:
                cols = [col.strip() for col in line.strip().split('|')[1:-1]]
                if len(cols) >= 5 and cols[0] != 'Р"Р°С‚Р°':
                    rows.append({
                        'date': cols[0], 'company': cols[1],
                        'lpr': cols[2], 'status': cols[3], 'comment': cols[4]
                    })
    return rows


def send_jarvis_message(text):
    if not JARVIS_BOT_TOKEN:
        print('JARVIS_BOT_TOKEN is not configured, skipping Jarvis message')
        return
    bot = Bot(token=JARVIS_BOT_TOKEN)
    try:
        asyncio.run(bot.send_message(chat_id=JARVIS_CHAT_ID, text=text, parse_mode='Markdown'))
    except TelegramError as exc:
        print(f'Jarvis failed to send message: {exc}')
    except Exception as exc:
        print(f'Jarvis unexpected error sending message: {exc}')


def generate_jarvis_text(prompt):
    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL, max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as exc:
        return f"Jarvis generation failed: {exc}"


def create_prompt(header, context, instruction):
    today = now_moscow().strftime('%d %B %Y')
    return (
        "Ты — личный секретарь директора ST8 AI. Тон: деловой, чёткий, как реальный помощник. Используй информацию из Memory Bank. Не пиши шаблонный текст."
        f" Сегодня: {today}. {header}\n\nКонтекст:\n{context}\n\nЗадача:\n{instruction}\n"
        "Сформулируй одно сообщение для Telegram без отметок типа 'Пока' или 'Привет'."
    )

WEATHER_CODE_MAP = {
    0: 'ясно ☀️', 1: 'преимущественно ясно ⛅', 2: 'переменная облачность ⛅', 3: 'пасмурно ⛅',
    45: 'туман 🌫️', 48: 'туман с инеем 🌫️',
    51: 'лёгкая морось 🌧️', 53: 'морось 🌧️', 55: 'сильная морось 🌧️',
    61: 'лёгкий дождь 🌧️', 63: 'дождь 🌧️', 65: 'сильный дождь 🌧️',
    71: 'лёгкий снег ❄️', 73: 'снег ❄️', 75: 'сильный снег ❄️', 77: 'снежная крупа ❄️',
    80: 'ливень 🌧️', 81: 'сильный ливень 🌧️', 82: 'очень сильный ливень 🌧️',
    95: 'гроза ⛈️', 96: 'гроза с градом ⛈️', 99: 'сильная гроза с градом ⛈️',
}


def get_moscow_weather():
    try:
        url = (
            'https://api.open-meteo.com/v1/forecast'
            '?latitude=55.75&longitude=37.62'
            '&current=temperature_2m,weathercode,windspeed_10m'
            '&timezone=Europe%2FMoscow'
        )
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        current = data.get('current', {})
        temp = current.get('temperature_2m')
        code = current.get('weathercode')
        wind = current.get('windspeed_10m')
        description = WEATHER_CODE_MAP.get(code, f'\u043a\u043e\u0434 {code}')
        if temp is None: clothing = '\u043d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445'
        elif temp < 0: clothing = '\u0437\u0438\u043c\u043d\u044f\u044f \u043a\u0443\u0440\u0442\u043a\u0430, \u0448\u0430\u043f\u043a\u0430, \u0448\u0430\u0440\u0444'
        elif temp < 10: clothing = '\u0442\u0451\u043f\u043b\u0430\u044f \u043a\u0443\u0440\u0442\u043a\u0430'
        elif temp < 18: clothing = '\u043b\u0451\u0433\u043a\u0430\u044f \u043a\u0443\u0440\u0442\u043a\u0430 \u0438\u043b\u0438 \u0434\u0436\u0435\u043c\u043f\u0435\u0440'
        else: clothing = '\u0431\u0435\u0437 \u043a\u0443\u0440\u0442\u043a\u0438'
        rain_codes = {51, 53, 55, 61, 63, 65, 80, 81, 82}
        umbrella = '\u0434\u0430 \u2602\ufe0f' if code in rain_codes else '\u043d\u0435\u0442'
        snow_codes = {71, 73, 75, 77}
        footwear = '\u0442\u0451\u043f\u043b\u0430\u044f \u043e\u0431\u0443\u0432\u044c' if (code in snow_codes or (temp is not None and temp < 0)) else '\u043e\u0431\u044b\u0447\u043d\u0430\u044f \u043e\u0431\u0443\u0432\u044c'
        return (
            f"🌤 Погода в Москве: {temp}°C, {description}, ветер {wind} км/ч\n"
            f"🧥 Одежда: {clothing}\n☂️ Зонт: {umbrella}\n👟 Обувь: {footwear}"
        )
    except Exception as exc:
        print(f'[Jarvis] \u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u0438\u044f \u043f\u043e\u0433\u043e\u0434\u044b: {exc}')
        return None

def _leads_summary():
    leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    if not leads:
        return 'Р›РёРґРѕРІ РЅРµС‚.'
    lines = []
    for lead in leads[:10]:
        name = lead.get('company_name', '—')
        seg = lead.get('segment', '—')
        lpr = lead.get('lpr', '—')
        phone = lead.get('phone', '—')
        lines.append(f"вЂў {name} [{seg}] Р›РџР : {lpr}, С‚РµР»: {phone}")
    return '\n'.join(lines)


def _find_lead_by_name(user_message):
    leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    msg_lower = user_message.lower()
    for lead in leads:
        name = lead.get('company_name', '')
        if len(name) > 3 and name.lower() in msg_lower:
            return lead
    return None


def _tavily_search(query):
    try:
        from tavily import TavilyClient
        tavily_key = os.getenv('TAVILY_API_KEY')
        if not tavily_key:
            return None
        tavily = TavilyClient(api_key=tavily_key)
        results = tavily.search(query=query[:100], max_results=3)
        snippets = []
        for r in results.get('results', []):
            snippets.append(f"- {r.get('title', '')}: {r.get('content', '')[:300]}")
        return '\n'.join(snippets) if snippets else None
    except Exception as exc:
        print(f'[Jarvis] РћС€РёР±РєР° Tavily: {exc}')
        return None


SEARCH_TRIGGER_WORDS = [
    'С‡С‚Рѕ С‚Р°РєРѕРµ', 'РєС‚Рѕ С‚Р°РєРѕР№', 'СЂР°СЃСЃРєР°Р¶Рё', 'РЅР°Р№РґРё', 'СѓР·РЅР°Р№',
    'РЅРѕРІРѕСЃС‚Рё', 'С‡С‚Рѕ РЅРѕРІРѕРіРѕ', 'РєРѕРЅС„РµСЂРµРЅС†РёСЏ', 'С„РѕСЂСѓРј', 'РІС‹СЃС‚Р°РІРєР°', 'Р°РєС‚СѓР°Р»СЊРЅРѕ',
]


def generate_smart_response(user_message, history):
    memory_bank = load_memory_bank()
    leads_summary = _leads_summary()
    found_lead = _find_lead_by_name(user_message)
    lead_card = ''
    if found_lead:
        lead_card = (
            f"\n\nРљР°СЂС‚РѕС‡РєР° Р»РёРґР°:\n"
            f"РљРѕРјРїР°РЅРёСЏ: {found_lead.get('company_name')}\n"
            f"РЎРµРіРјРµРЅС‚: {found_lead.get('segment')}\n"
            f"Р›РџР : {found_lead.get('lpr')}\n"
            f"РўРµР»РµС„РѕРЅ: {found_lead.get('phone')}\n"
            f"Р'РѕР»СЊ: {found_lead.get('pain')}\n"
            f"РЎС‚Р°С‚СѓСЃ: {found_lead.get('response')}"
        )
    search_context = ''
    if any(t in user_message.lower() for t in SEARCH_TRIGGER_WORDS):
        sr = _tavily_search(user_message)
        if sr:
            search_context = f"\n\nРђРєС‚СѓР°Р»СЊРЅР°СЏ РёРЅС„РѕСЂРјР°С†РёСЏ:\n{sr}"
    system_prompt = (
        "РўС‹ — Jarvis, СѓРјРЅС‹Р№ Р»РёС‡РЅС‹Р№ Р°СЃСЃРёСЃС‚РµРЅС‚ РґРёСЂРµРєС‚РѕСЂР° ST8-AI. "
        "РўРѕРЅ: РґРµР»РѕРІРѕР№, РєРѕРЅРєСЂРµС‚РЅС‹Р№, Р±РµР· РІРѕРґС‹. РќРµ РёСЃРїРѕР»СЊР·СѓР№ С€Р°Р±Р»РѕРЅРЅС‹Рµ С„СЂР°Р·С‹. "
        "РќРµ РїРѕРІС‚РѕСЂСЏР№ РІРѕРїСЂРѕСЃ. РџСЂРѕСЃС‚Рѕ РѕС‚РІРµС‡Р°Р№.\n\n"
        f"Memory Bank ST8-AI:\n{memory_bank}\n\n"
        f"Р›РёРґС‹:\n{leads_summary}{lead_card}{search_context}"
    )
    messages = []
    for entry in history:
        role = entry.get('role')
        content = entry.get('content', '')
        if role in ('user', 'assistant') and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})
    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL, max_tokens=600,
            system=system_prompt, messages=messages,
        )
        return response.content[0].text.strip()
    except Exception as exc:
        return f"РћС€РёР±РєР° Claude: {exc}"


# в"Ђв"Ђв"Ђ Scheduled tasks в"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђ

def make_good_morning():
    weather_block = get_moscow_weather()
    client_pipeline = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'clientPipeline.md'))
    active_context = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))
    context = f"clientPipeline:\n{client_pipeline}\n\nactiveContext:\n{active_context}"
    prompt = create_prompt('Р"РѕР±СЂРѕРµ СѓС‚СЂРѕ. РЎС„РѕСЂРјРёСЂСѓР№ РїР»Р°РЅ РґРЅСЏ.', context,
        'РџРѕРґРіРѕС‚РѕРІСЊ РєРѕСЂРѕС‚РєРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ СЃ РєРѕРЅРєСЂРµС‚РЅС‹Рј РїР»Р°РЅРѕРј РЅР° РґРµРЅСЊ: РєРѕРјСѓ РїРѕР·РІРѕРЅРёС‚СЊ, РєРѕРјСѓ РЅР°РїРёСЃР°С‚СЊ.')
    plan_text = generate_jarvis_text(prompt)
    text = f"{weather_block}\n\n{plan_text}" if weather_block else plan_text
    send_jarvis_message(text)

def make_call_reminder():
    active_context = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))
    pipeline = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'clientPipeline.md'))
    prompt = create_prompt('РќР°РїРѕРјРёРЅР°РЅРёРµ Рѕ Р·РІРѕРЅРєР°С….', f"activeContext:\n{active_context}\n\nclientPipeline:\n{pipeline}",
        'РљСЂР°С‚РєРѕРµ РЅР°РїРѕРјРёРЅР°РЅРёРµ Рѕ РєР»СЋС‡РµРІС‹С… Р·Р°РґР°С‡Р°С… Рё РІСЃС‚СЂРµС‡Р°С….')
    send_jarvis_message(generate_jarvis_text(prompt))

def make_motivation():
    active_context = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))
    prompt = create_prompt('РљРѕСЂРѕС‚РєР°СЏ РјРѕС‚РёРІР°С†РёСЏ РІ 11:00.', active_context,
        'РћРґРЅР° РєРѕРЅРєСЂРµС‚РЅР°СЏ С„СЂР°Р·Р° РјРѕС‚РёРІР°С†РёРё — РїСЂРѕ СЂРµР°Р»СЊРЅС‹С… РєР»РёРµРЅС‚РѕРІ РёР»Рё С†РµР»Рё ST8-AI.')
    send_jarvis_message(generate_jarvis_text(prompt))

def make_lead_digest():
    leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    sample = '\n'.join([f"- {l.get('company_name')} ({l.get('segment', '?')})" for l in leads[:8]])
    prompt = create_prompt('Р"Р°Р№РґР¶РµСЃС‚ Р»РёРґРѕРІ.', f"Р›РёРґС‹:\n{sample}\nР'СЃРµРіРѕ: {len(leads)}",
        'РљСЂР°С‚РєРёР№ РѕС‚С‡С\'С‚: С‡С‚Рѕ СЃС‚РѕРёС‚ РїСЂРѕРІРµСЂРёС‚СЊ СЃРµРіРѕРґРЅСЏ.')
    send_jarvis_message(generate_jarvis_text(prompt))

def make_lunch_tip():
    prompt = create_prompt('Р\'СЂРµРјСЏ РѕР±РµРґР° 13:00.', '',
        'РќР°РїРѕРјРЅРё РїРѕРѕР±РµРґР°С‚СЊ Рё РґР°Р№ РѕРґРёРЅ РєРѕРЅРєСЂРµС‚РЅС‹Р№ СЃРѕРІРµС‚ РЅР° РІС‚РѕСЂСѓСЋ РїРѕР»РѕРІРёРЅСѓ РґРЅСЏ. Р\'РµР· РІРѕРґС‹.')
    send_jarvis_message(generate_jarvis_text(prompt))

def _generate_followup_text(company_name, lpr):
    prompt = (f"РќР°РїРёС€Рё РєРѕСЂРѕС‚РєРёР№ follow-up РґР»СЏ {company_name} ({lpr}). "
              f"РџРµСЂРІРѕРµ РєР°СЃР°РЅРёРµ 3 РґРЅСЏ РЅР°Р·Р°Рґ. РўРѕРЅ: РґСЂСѓР¶РµР»СЋР±РЅС‹Р№, РѕРґРёРЅ РІРѕРїСЂРѕСЃ РІ РєРѕРЅС†Рµ. 2-3 РїСЂРµРґР»РѕР¶РµРЅРёСЏ.")
    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL, max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as exc:
        return f"(РѕС€РёР±РєР°: {exc})"

def make_no_response_reminder():
    status_rows = load_markdown_table(os.path.join(BASE_DIR, 'leads_status.md'))
    leads_db = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    leads_by_name = {l.get('company_name', '').lower(): l for l in leads_db}
    old = []
    today = now_moscow().date()
    for row in status_rows:
        try:
            row_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
        except Exception:
            continue
        if row['status'] == 'РЅР°РїРёСЃР°Р»Рё' and (today - row_date).days >= 3:
            old.append(row)
    if not old:
        send_jarvis_message('РќРµС‚ РєР»РёРµРЅС‚РѕРІ Р±РµР· РѕС‚РІРµС‚Р° 3+ РґРЅРµР№.')
        return
    messages = []
    for row in old[:5]:
        company, lpr = row['company'], row['lpr']
        phone = leads_by_name.get(company.lower(), {}).get('phone', '—')
        followup = _generate_followup_text(company, lpr)
        messages.append(f"[{company}]\nTel: {phone}\nFollow-up:\n{followup}")
    send_jarvis_message(f"вЏ° Follow-up РЅСѓР¶РµРЅ {len(old)} РєР»РёРµРЅС‚Р°Рј:\n\n" + '\n\n'.join(messages))

def make_day_summary():
    active_context = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))
    pipeline = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'clientPipeline.md'))
    status_rows = load_markdown_table(os.path.join(BASE_DIR, 'leads_status.md'))
    summary_rows = '\n'.join([f"- {r['company']}: {r['status']}" for r in status_rows[:8]])
    context = f"activeContext:\n{active_context}\n\nclientPipeline:\n{pipeline}\n\nleads:\n{summary_rows}"
    prompt = create_prompt('РС‚РѕРі РґРЅСЏ.', context, 'РљСЂР°С‚РєРѕРµ СЂРµР·СЋРјРµ РґРЅСЏ Рё С‡С‚Рѕ РїРµСЂРµРЅРµСЃС‚Рё РЅР° Р·Р°РІС‚СЂР°.')
    send_jarvis_message(generate_jarvis_text(prompt))

def make_weekly_report():
    active_context = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))
    pipeline = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'clientPipeline.md'))
    leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    sample = '\n'.join([f"- {l.get('company_name')} ({l.get('segment', '?')})" for l in leads[:10]])
    context = f"activeContext:\n{active_context}\n\nclientPipeline:\n{pipeline}\n\nР›РёРґС‹:\n{sample}\nР'СЃРµРіРѕ: {len(leads)}"
    prompt = create_prompt('РќРµРґРµР»СЊРЅС‹Р№ РѕС‚С‡С\'С‚.', context, 'Р"РµР»РѕРІРѕР№ РµР¶РµРЅРµРґРµР»СЊРЅС‹Р№ РѕС‚С‡С\'С‚ СЃ РІС‹РІРѕРґР°РјРё Рё СЂРµРєРѕРјРµРЅРґР°С†РёСЏРјРё.')
    send_jarvis_message(generate_jarvis_text(prompt))

def make_energy_boost():
    pipeline = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'clientPipeline.md'))
    prompt = create_prompt('Р­РЅРµСЂРіРёСЏ РІ 16:00.', pipeline,
        'Р§С‚Рѕ РµС‰С\' СѓСЃРїРµС‚СЊ РґРѕ РєРѕРЅС†Р° РґРЅСЏ РёР· РїР°Р№РїР»Р°Р№РЅР°. РљРѕРЅРєСЂРµС‚РЅРѕ, 2-3 РґРµР№СЃС‚РІРёСЏ.')
    send_jarvis_message(generate_jarvis_text(prompt))

def make_evening_summary():
    active_context = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))
    prompt = create_prompt('Р\'РµС‡РµСЂ 19:00.', active_context,
        'Р§С‚Рѕ С…РѕСЂРѕС€РµРіРѕ СЃР»СѓС‡РёР»РѕСЃСЊ СЃРµРіРѕРґРЅСЏ, РѕРґРЅРѕ РїРѕР¶РµР»Р°РЅРёРµ РЅР° РІРµС‡РµСЂ. РўРµРїР»Рѕ, Р±РµР· РѕС„РёС†РёРѕР·Р°.')
    send_jarvis_message(generate_jarvis_text(prompt))


# в"Ђв"Ђв"Ђ Commands в"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђ

def cmd_plan(history):
    client_pipeline = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'clientPipeline.md'))
    active_context = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))
    prompt = create_prompt('РЎРѕСЃС‚Р°РІСЊ РїР»Р°РЅ РґРЅСЏ.', f"clientPipeline:\n{client_pipeline}\n\nactiveContext:\n{active_context}",
        'РљРѕРјСѓ РїРѕР·РІРѕРЅРёС‚СЊ, РєРѕРјСѓ РЅР°РїРёСЃР°С‚СЊ, С‡С‚Рѕ РїСЂРёРѕСЂРёС‚РµС‚РЅРѕ СЃРµРіРѕРґРЅСЏ.')
    return generate_jarvis_text(prompt)

def cmd_leads(history):
    leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    lines = [f"{i}. {l.get('company_name', '?')} [{l.get('segment', '—')}]" for i, l in enumerate(leads[:10], 1)]
    context = f"Р›РёРґС‹ ({len(leads)} РІСЃРµРіРѕ):\n" + '\n'.join(lines)
    prompt = create_prompt('Р"Р°Р№РґР¶РµСЃС‚ Р»РёРґРѕРІ.', context, 'РљСЂР°С‚РєРёР№ РѕР±Р·РѕСЂ: РЅР° РєР°РєРёС… СЃРѕСЃСЂРµРґРѕС‚РѕС‡РёС‚СЊСЃСЏ.')
    return generate_jarvis_text(prompt)

def cmd_hub():
    import json as _json
    try:
        with open(os.path.join(BASE_DIR, 'st8hub', 'leads.json'), 'r', encoding='utf-8') as _f:
            _leads = _json.load(_f)
    except Exception:
        _leads = []
    total = len(_leads)
    new_count = sum(1 for l in _leads if l.get('status') == '\u043d\u043e\u0432\u044b\u0439')
    hot_count = sum(1 for l in _leads if l.get('score', 0) >= 8)
    last_date = max((l.get('date', '') for l in _leads), default='\u043d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445')
    lines = [
        '\U0001f4ca ST8 Hub \u0441\u0442\u0430\u0442\u0443\u0441:',
        f'\u0412\u0441\u0435\u0433\u043e \u043b\u0438\u0434\u043e\u0432: {total}',
        f'\u041d\u043e\u0432\u044b\u0445: {new_count}',
        f'\u0413\u043e\u0440\u044f\u0447\u0438\u0445 (score>=8): {hot_count}',
        f'\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0435 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435: {last_date}',
        '\U0001f449 https://kosmos686-bit.github.io/st8hub',
    ]
    return '\n'.join(lines)



JARVIS_MENU_TEXT = (
    '\U0001f916 *Jarvis \u2014 \u0433\u043b\u0430\u0432\u043d\u043e\u0435 \u043c\u0435\u043d\u044e*\n\n'
    '[A] \U0001f4cb \u041f\u043b\u0430\u043d \u0434\u043d\u044f \u2014 /\u043f\u043b\u0430\u043d\n'
    '[B] \U0001f465 \u041b\u0438\u0434\u044b \u2014 /\u043b\u0438\u0434\u044b\n'
    '[C] \U0001f4ca ST8 Hub \u2014 /\u0445\u0430\u0431\n'
    '[D] \U0001f916 \u0410\u0433\u0435\u043d\u0442 \u2014 /\u0430\u0433\u0435\u043d\u0442 <\u0438\u043c\u044f> <\u0437\u0430\u0434\u0430\u0447\u0430>\n'
    '[E] \U0001f4ac \u042e\u043b\u0435 \u2014 /\u044e\u043b\u0435 <\u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435>\n\n'
    '\u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u043a\u043e\u043c\u0430\u043d\u0434\u0443 \u0438\u043b\u0438 \u043f\u0440\u043e\u0441\u0442\u043e \u0437\u0430\u0434\u0430\u0447\u0443'
)

def cmd_menu():
    return JARVIS_MENU_TEXT


def cmd_client(client_name, history):
    leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    pipeline = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'clientPipeline.md'))
    found = [l for l in leads if client_name.lower() in l.get('company_name', '').lower()]
    if found:
        lead = found[0]
        context = (f"РљР»РёРµРЅС‚: {lead.get('company_name')}\nРЎРµРіРјРµРЅС‚: {lead.get('segment')}\n"
                   f"Р›РџР : {lead.get('lpr')}\nР'РѕР»СЊ: {lead.get('pain')}\n"
                   f"РљРѕРЅС‚Р°РєС‚: {lead.get('telegram_social') or lead.get('email') or 'РЅРµ СѓРєР°Р·Р°РЅ'}\n\nPipeline:\n{pipeline[:800]}")
    else:
        context = f"РљР»РёРµРЅС‚ '{client_name}' РЅРµ РЅР°Р№РґРµРЅ.\n\nPipeline:\n{pipeline[:1000]}"
    prompt = create_prompt(f'РРЅС„РѕСЂРјР°С†РёСЏ РїРѕ РєР»РёРµРЅС‚Сѓ: {client_name}', context, 'РЎРІРѕРґРєР°: С‡С‚Рѕ РёР·РІРµСЃС‚РЅРѕ, СЃС‚Р°С‚СѓСЃ, СЃР»РµРґСѓСЋС‰РёР№ С€Р°Рі.')
    return generate_jarvis_text(prompt)

def cmd_memory(client_name):
    slug = None
    for key, s in CLIENT_SLUGS.items():
        if key in client_name.lower():
            slug = s
            break
    if not slug:
        return f"РљР»РёРµРЅС‚ '{client_name}' РЅРµ РЅР°Р№РґРµРЅ РІ Р±Р°Р·Рµ РїР°РјСЏС‚Рё."
    memory = load_agent_memory(slug)
    if not memory:
        return f"РџРѕ РєР»РёРµРЅС‚Сѓ '{client_name}' РїРѕРєР° РЅРµС‚ СЃРѕС…СЂР°РЅС'РЅРЅРѕР№ РёСЃС‚РѕСЂРёРё Р°РіРµРЅС‚РѕРІ."
    lines = [f"[{e['ts']}] [{e['agent']}] {e['response'][:200]}" for e in memory[-5:]]
    return f"рџ\"‹ РСЃС‚РѕСЂРёСЏ Р°РіРµРЅС‚РѕРІ — {client_name}:\n\n" + '\n\n'.join(lines)

_CALL_TRIGGERS = ('Р·РІРѕРЅСЋ', 'Р·РІРѕРЅРѕРє', 'СЃРѕР·РІРѕРЅ')

def cmd_call_prep(user_message):
    leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    found_lead = None
    msg_lower = user_message.lower()
    for lead in leads:
        name = lead.get('company_name', '')
        if len(name) > 3 and name.lower() in msg_lower:
            found_lead = lead
            break
    if not found_lead:
        return generate_smart_response(user_message, [])
    company_name = found_lead.get('company_name', '')
    lpr = found_lead.get('lpr', 'Р"РёСЂРµРєС‚РѕСЂ')
    segment = found_lead.get('segment', '')
    pain = found_lead.get('pain', '')
    tavily_results = ''
    try:
        sr = _tavily_search(f"{company_name} РЅРѕРІРѕСЃС‚Рё РїСЂРѕР±Р»РµРјС‹ РѕС‚Р·С‹РІС‹")
        if sr:
            tavily_results = sr
    except Exception:
        pass
    prompt = (
        f"РџРѕРґРіРѕС‚РѕРІСЊ СЃРєСЂРёРїС‚ Р·РІРѕРЅРєР° РґР»СЏ ST8-AI. "
        f"РљРѕРјРїР°РЅРёСЏ: {company_name}, Р›РџР : {lpr}, СЃРµРіРјРµРЅС‚: {segment}, Р±РѕР»СЊ: {pain}. "
        f"РРЅС„РѕСЂРјР°С†РёСЏ: {tavily_results or 'РЅРµС‚ РґР°РЅРЅС‹С…'}. "
        f"РЎРєСЂРёРїС‚: РїСЂРёРІРµС‚СЃС‚РІРёРµ в†' Р±РѕР»СЊ в†' СЂРµС€РµРЅРёРµ в†' РІРѕРїСЂРѕСЃ в†' РІРѕР·СЂР°Р¶РµРЅРёСЏ 'РґРѕСЂРѕРіРѕ' Рё 'СѓР¶Рµ РµСЃС‚СЊ СЃРёСЃС‚РµРјР°'."
    )
    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL, max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        script = response.content[0].text.strip()
    except Exception as exc:
        script = f"РћС€РёР±РєР°: {exc}"
    return f"рџ\"ћ РЎРєСЂРёРїС‚ Р·РІРѕРЅРєР° — {company_name}\nР›РџР : {lpr} | {segment}\n\n{script}"


def process_incoming_message(text, history):
    text = text.strip()

    if text.strip() in ('/start', '/\u043c\u0435\u043d\u044e', '/menu'):
        return cmd_menu()
    if text.strip().upper() in ('A', '[A]'):
        return cmd_plan(history)
    if text.strip().upper() in ('B', '[B]'):
        return cmd_leads(history)
    if text.strip().upper() in ('C', '[C]'):
        return cmd_hub()
    if text.strip().upper() in ('D', '[D]'):
        parts = text.split(maxsplit=1)
        return ('Format: /agent <name> <task>')
    if text.strip().upper() in ('E', '[E]'):
        parts = text.split(maxsplit=1)
        return ('Format: /\u044e\u043b\u0435 <message>')
    if text.lower().startswith('/\u0445\u0430\u0431'):
        return cmd_hub()
    if text.startswith('/\u043f\u043b\u0430\u043d'):
        return cmd_plan(history)
    if text.startswith('/\u043b\u0438\u0434\u044b'):
        return cmd_leads(history)
    if text.lower().startswith('/\u043a\u043b\u0438\u0435\u043d\u0442'):
        parts = text.split(maxsplit=1)
        client_name = parts[1].strip() if len(parts) > 1 else ''
        return cmd_client(client_name, history) if client_name else 'РЈРєР°Р¶Рё: /\u043a\u043b\u0438\u0435\u043d\u0442 <РќР°Р·РІР°РЅРёРµ>'
    if text.lower().startswith('/\u043f\u0430\u043c\u044f\u0442\u044c'):
        parts = text.split(maxsplit=1)
        client_name = parts[1].strip() if len(parts) > 1 else ''
        return cmd_memory(client_name) if client_name else 'РЈРєР°Р¶Рё: /\u043f\u0430\u043c\u044f\u0442\u044c <РљР»РёРµРЅС‚>'
    if text.lower().startswith('/\u0430\u0433\u0435\u043d\u0442'):
        parts = text.split(maxsplit=2)
        if len(parts) >= 3:
            agent_name = parts[1].strip().lower()
            task = parts[2].strip()
            if not agent_name.startswith('st8-'):
                agent_name = 'st8-' + agent_name
            client_slug = get_client_slug(task)
            client_memory = load_agent_memory(client_slug)
            agent_short, result = call_agent(agent_name, task, history, client_memory=client_memory)
            if result:
                actions = execute_actions(result)
                if client_slug:
                    save_agent_memory(client_slug, agent_name, task, result)
                full = f"[{agent_short}]\n{result}"
                if actions:
                    full += '\n\n' + '\n'.join(actions)
                return full
            return f"РђРіРµРЅС‚ '{agent_name}' РЅРµ РЅР°Р№РґРµРЅ."
        return (
            "Р¤РѕСЂРјР°С‚: /\u0430\u0433\u0435\u043d\u0442 <РёРјСЏ> <Р·Р°РґР°С‡Р°>\n"
            "РђРіРµРЅС‚С‹: sales-strategist, kp-architect, horeca-consultant,\n"
            "backend-architect, bot-developer, security-auditor,\n"
            "qa-engineer, integration-engineer, cv-vision-engineer, ai-director"
        )
    if text.lower().startswith('/\u044e\u043b\u0435'):
        parts = text.split(maxsplit=1)
        msg = parts[1].strip() if len(parts) > 1 else ''
        return tool_send_yulia(msg) if msg else 'РЈРєР°Р¶Рё: /\u044e\u043b\u0435 <СЃРѕРѕР±С‰РµРЅРёРµ>'
    if text.lower().startswith('/\u0441\u0442\u0430\u0442\u0443\u0441'):
        parts = text.split(maxsplit=3)
        if len(parts) >= 3:
            company, status = parts[1], parts[2]
            comment = parts[3] if len(parts) > 3 else ''
            return tool_save_lead_status(company, status, comment)
        return 'Р¤РѕСЂРјР°С‚: /\u0441\u0442\u0430\u0442\u0443\u0441 <РљРѕРјРїР°РЅРёСЏ> <СЃС‚Р°С‚СѓСЃ> [РєРѕРјРјРµРЅС‚Р°СЂРёР№]'

    if any(t in text.lower() for t in _CALL_TRIGGERS):
        return cmd_call_prep(text)

    # РђРІС‚РѕСЂРѕСѓС‚РёРЅРі Р°РіРµРЅС‚РѕРІ Рё С†РµРїРѕС‡РµРє
    result = run_agent_or_chain(text, history)
    if result:
        return result

    return generate_smart_response(text, history)


async def extract_file_text(bot, message):
    """Извлекает текст из PDF или docx присланного в Telegram"""
    import tempfile, fitz, docx as dx
    doc = message.document
    if not doc:
        return None
    fname = doc.file_name or ""
    tg_file = await bot.get_file(doc.file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(fname)[1]) as tmp:
        await tg_file.download_to_drive(tmp.name)
        path = tmp.name
    try:
        if fname.lower().endswith(".pdf"):
            pdf = fitz.open(path)
            return "\n".join(p.get_text() for p in pdf)
        elif fname.lower().endswith(".docx"):
            d = dx.Document(path)
            return "\n".join(p.text for p in d.paragraphs if p.text.strip())
        else:
            return f"[Файл {fname} — не PDF и не docx, не могу прочитать]"
    finally:
        os.unlink(path)


# в"Ђв"Ђв"Ђ Polling в"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђ

async def poll_jarvis():
    if not JARVIS_BOT_TOKEN:
        print('JARVIS_BOT_TOKEN РЅРµ Р·Р°РґР°РЅ — polling РѕС‚РєР»СЋС‡С\'РЅ')
        return
    bot = Bot(token=JARVIS_BOT_TOKEN)
    offset = load_offset()
    print(f'[Jarvis] Polling Р·Р°РїСѓС‰РµРЅ. Offset: {offset}')
    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=10, allowed_updates=['message', 'channel_post'])
            for update in updates:
                offset = update.update_id + 1
                save_offset(offset)
                msg = update.message
                if not msg:
                    continue
                if msg.chat.id != JARVIS_CHAT_ID:
                    continue
                if msg.document:
                    file_text = await extract_file_text(bot, msg)
                    user_text = f'[Файл: {msg.document.file_name}]\n{file_text}' if file_text else '[Не удалось прочитать файл]'
                elif msg.text:
                    user_text = msg.text
                else:
                    continue
                history = load_memory()
                reply = process_with_agent(user_text, history, claude_client, CLAUDE_MODEL)
                ts = datetime.now().isoformat(timespec='seconds')
                history.append({"role": "user", "content": user_text, "ts": ts})
                history.append({"role": "assistant", "content": reply, "ts": ts})
                save_memory(history)
                await bot.send_message(chat_id=JARVIS_CHAT_ID, text=reply, parse_mode='Markdown')
        except TelegramError as exc:
            print(f'[Jarvis] РћС€РёР±РєР° Telegram: {exc}')
        except Exception as exc:
            print(f'[Jarvis] РќРµРѕР¶РёРґР°РЅРЅР°СЏ РѕС€РёР±РєР°: {exc}')
        await asyncio.sleep(POLL_INTERVAL)


def run_polling():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(poll_jarvis())


def check_moscow_jarvis_tasks():
    now = now_moscow()
    current = now.strftime('%H:%M')
    weekday = now.weekday()

    # Одноразовые напоминания по дате
    today = now.date()
    if today == datetime(2026, 4, 21).date() and current == '09:00':
        key = 'oneshot:2026-04-21:09:00'
        if LAST_JARVIS_RUN.get(key) != today:
            try:
                send_jarvis_message(
                    "📅 Напоминание: сегодня истекают 10 дней паузы по лидам.\n\n"
                    "Чтобы возобновить поиск лидов — раскомментировать 4 строки в scheduler.py (job_horeca, job_retail, job_production_logistics, job_all) и перезапустить scheduler."
                )
                LAST_JARVIS_RUN[key] = today
            except Exception as exc:
                print(f"[Jarvis] reminder send failed: {exc}")

    tasks = [
        ('07:30', None, make_good_morning),
        ('10:00', None, make_call_reminder),
        ('11:00', None, make_motivation),
        ('12:00', None, make_lead_digest),
        ('13:00', None, make_lunch_tip),
        ('15:00', None, make_no_response_reminder),
        ('16:00', None, make_energy_boost),
        ('17:00', None, make_day_summary),
        ('17:30', 4, make_weekly_report),
        ('19:00', None, make_evening_summary),
    ]
    for schedule_time, day_filter, func in tasks:
        key = f"{schedule_time}:{day_filter}"
        if current == schedule_time and (day_filter is None or day_filter == weekday):
            last_run = LAST_JARVIS_RUN.get(key)
            if last_run == now.date():
                continue
            try:
                func()
                LAST_JARVIS_RUN[key] = now.date()
            except Exception as exc:
                send_jarvis_message(f"Jarvis failed {schedule_time}: {exc}")


if __name__ == '__main__':
    asyncio.run(poll_jarvis())


def safe_claude_call(messages, system='', max_tokens=1000):
    import time
    for attempt in range(3):
        try:
            return claude_client.messages.create(model=CLAUDE_MODEL, max_tokens=max_tokens, system=system, messages=messages)
        except Exception as e:
            if '529' in str(e) or 'overloaded' in str(e).lower():
                time.sleep(10 * (attempt + 1))
            else:
                raise
    return None
