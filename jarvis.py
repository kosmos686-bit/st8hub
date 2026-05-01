try:
    from agents_jarvis_integration import handle_agents_command, is_agent_command
except Exception as _e:
    is_agent_command = lambda x: False
    handle_agents_command = None

is_auto_hunt_command = lambda x: False
handle_auto_hunt_command = None

try:
    from max_agent import MaxAgent
    from dima_agent import DimaAgent
except:
    MaxAgent = None
    DimaAgent = None

import asyncio
import hashlib
import json
import os
import re
import time
import urllib.request
import warnings
import logging
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')
logging.disable(logging.CRITICAL)

# Live log — separate handler, not affected by logging.disable above
_live_log = logging.getLogger('jarvis_live')
_live_log.setLevel(logging.INFO)
_live_log.disabled = False
if not _live_log.handlers:
    _lh = logging.FileHandler(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarvis_live.log'),
        encoding='utf-8',
    )
    _lh.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    _live_log.addHandler(_lh)

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
    except Exception as _exc:
        _live_log.exception("[_get_mem0] unhandled exception")
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
            except Exception as _exc:
                _live_log.exception("[load_external_agents] unhandled exception")
                pass
    return agents

ALL_AGENTS = {**BUILTIN_AGENTS}
ALL_AGENTS.update(load_external_agents())

AGENT_ROUTER_PROMPT = """Ты роутер агентов ST8-AI. Определи какой агент нужен для ответа на сообщение.

Доступные агенты:

# ПРОДАЖИ — холодные
- sales-hunter: холодный лид, первый контакт, как написать/позвонить, квалификация, follow-up серия
- sales-outbound-strategist: ICP, сигналы для outreach, база для холодного обхода, найти клиентов в сегменте/регионе
- sales-discovery-coach: как провести первый звонок/встречу, какие вопросы задать, выявление боли

# ПРОДАЖИ — сделка
- sales-closer: клиент говорит дорого/подумаю/не сейчас/есть другие — скрипт закрытия прямо сейчас
- objection-handler: нужны варианты ответов на конкретное возражение (3 стиля)
- deal-analyst: что происходит с этой сделкой, почему зависла, что делать дальше, OODA
- sales-deal-strategist: план победы в сделке, MEDDPICC, конкурентное позиционирование
- sales-account-strategist: развитие текущего клиента, upsell, удержание, QBR

# ПРОДАЖИ — инструменты
- kp-writer: написать готовое КП, питч, предложение для конкретного клиента
- st8-kp-architect: структура КП, воронка убеждения, что включить в документ
- sales-proposal-strategist: стратегия под тендер/RFP, win-тема, executive summary
- sales-pipeline-analyst: анализ пайплайна, скорость сделок, прогноз, где застряло

# СТРАТЕГИЯ
- st8-sales-strategist: стратегия продаж AI-решений, MEDDIC/Sandler/Challenger, от outreach до подписания
- st8-ai-director: стратегия ST8-AI как продукта, roadmap, монетизация, партнёрства, рынок

# ОТРАСЛЬ
- st8-horeca-consultant: рестораны, кафе, отели, iiko, R-Keeper, фудкост, HoReCa-боли

# КОД И РАЗРАБОТКА
- st8-bot-developer: написать бот, скрипт, код на Python, Telegram API, интеграции, баги
- st8-backend-architect: архитектура, API-дизайн, БД, масштабирование, деплой, Windows Server
- engineering-rapid-prototyper: быстро сделать MVP, прототип, работающий пример за час
- engineering-ai-engineer: ML-модели, AI-пайплайны, embeddings, fine-tuning, RAG
- engineering-code-reviewer: проверь этот код, найди баги, code review, что не так

# БЕЗОПАСНОСТЬ
- st8-security-auditor: безопасность кода, утечки ключей, OWASP, уязвимости, права доступа

- none: общий вопрос, личное, погода, питание, напоминания, что-то не про бизнес и не про код

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
        _log_token_usage(response, model)
        return agent_name if agent_name in ALL_AGENTS else "none"
    except Exception as _exc:
        _live_log.exception("[route_to_agent] unhandled exception")
        return "none"


_JARVIS_PROMPT_CACHE = {'prompt': None, 'hub_block': None, 'mtime': None}


def _load_agent_memory_md(query=None):
    """Семантическая загрузка памяти через mempalace или fallback на все файлы."""
    # Семантический поиск если есть запрос
    if query:
        try:
            import subprocess, json as _json
            result = subprocess.run(
                ['python', '-m', 'mempalace', 'search', query, '--limit', '5', '--json'],
                capture_output=True, text=True, cwd=BASE_DIR
            )
            if result.returncode == 0 and result.stdout.strip():
                data = _json.loads(result.stdout)
                parts = []
                for item in data:
                    parts.append('[memory]\n' + item.get('text', '')[:800])
                if parts:
                    return '\n\n'.join(parts)
        except Exception:
            pass
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
            except Exception as _exc:
                _live_log.exception("[_load_agent_memory_md] unhandled exception")
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
        except Exception as _exc:
            _live_log.exception("[_load_agent_memory_md] unhandled exception")
            pass

    return '\n\n'.join(parts)


# ─── AGENT SESSION LOG ───────────────────────────────────────────────────────
_SESSION_LOG_PATH = os.path.join(os.path.dirname(__file__), 'jarvis_session_log.json')
_MAX_SESSION_ENTRIES = 5


def _load_session_log():
    try:
        with open(_SESSION_LOG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as _exc:
        _live_log.exception("[_load_session_log] unhandled exception")
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
    except Exception as _exc:
        _live_log.exception("[_save_session_entry] unhandled exception")
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
    except Exception as _exc:
        _live_log.exception("[_mempalace_search] unhandled exception")
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

    context_md = _load_agent_memory_md(query=user_message if "user_message" in dir() else None)
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

Отвечай коротко, конкретно, по-деловому.

ФОРМАТ TELEGRAM — СТРОГО:
- без Markdown: нет **, нет ##, нет ```, нет таблиц, нет ---
- один эмодзи в начале строки, больше нигде
- строчные буквы в заголовках
- максимум 7-10 строк на ответ
- без приветствий ("Привет!", "Погнали! 🚀") и прощаний

## ПИТАНИЕ АЛЕКСЕЯ
- Лимит: 1400 ккал/день — всё разрешено, главное вписаться в калории
- Цель: минус 5-6 кг
- Тренировки: пока нельзя (колено)
- Meal_scheduler ведёт меню и учёт — не генерируй своё меню"""

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

    # Если упомянут клиент — читаем его .md из agent_memory/
    client_md_block = ""
    client_slug = get_client_slug(user_text)
    if client_slug:
        md_path = os.path.join(AGENT_MEMORY_DIR, f'{client_slug}.md')
        if os.path.exists(md_path):
            try:
                client_md_block = f"\n\n=== КОНТЕКСТ КЛИЕНТА ({client_slug}) ===\n" + open(md_path, encoding='utf-8').read()[:1500]
            except Exception:
                pass

    _now = now_moscow()
    _date_line = f"\nСегодня: {_now.strftime('%A, %d %B %Y')}, {_now.strftime('%H:%M')} МСК.\n"

    if agent_name == "none":
        system_prompt = jarvis_prompt + _date_line + session_block + palace_block + client_md_block
    else:
        agent_prompt = ALL_AGENTS.get(agent_name, "")
        base = f"{agent_prompt}\n\n---\n\n{hub_block}" if agent_prompt else jarvis_prompt
        system_prompt = base + _date_line + session_block + palace_block + client_md_block

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
        _log_token_usage(response, kwargs.get('model', model))

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
                _log_token_usage(response, kwargs.get('model', model))
                _save_session_entry(agent_name, user_text, reply)
                return reply + _detect_chain_hint(agent_name, reply)
            except Exception as _exc:
                _live_log.exception("[process_with_agent] unhandled exception")
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

# ── ST8ModelRouter ─────────────────────────────────────────────────────────────
_HAIKU_MODEL  = 'claude-haiku-4-5-20251001'
_SONNET_MODEL = 'claude-sonnet-4-6'
_MODEL_COST   = {
    _HAIKU_MODEL:  {'in': 0.80e-6, 'out': 4.00e-6},
    _SONNET_MODEL: {'in': 3.00e-6, 'out': 15.00e-6},
}

def _log_token_usage(response, model_name: str) -> None:
    """Log token usage and cost for a single API call to jarvis_live.log."""
    try:
        if response is None or not hasattr(response, 'usage') or response.usage is None:
            return
        inp = response.usage.input_tokens
        out = response.usage.output_tokens
        cost_info = _MODEL_COST.get(model_name, {'in': 3.00e-6, 'out': 15.00e-6})
        cost = inp * cost_info['in'] + out * cost_info['out']
        _live_log.info(
            '[TOKEN] model=%s input=%d output=%d cost=$%.6f',
            model_name, inp, out, cost,
        )
    except Exception:
        pass

_RESPONSE_CACHE: dict = {}
_CACHE_MAX = 256


def _truncate_context(text: str, max_tokens: int = 4000) -> str:
    """Trim to ~max_tokens (4 chars ≈ 1 token), keeping the tail."""
    limit = max_tokens * 4
    return text[-limit:] if len(text) > limit else text


def _cache_md5(messages: list, system: str) -> str:
    raw = json.dumps(messages, ensure_ascii=False, sort_keys=True) + system
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


def _cache_get(key: str):
    return _RESPONSE_CACHE.get(key)


def _cache_set(key: str, value) -> None:
    if len(_RESPONSE_CACHE) >= _CACHE_MAX:
        del _RESPONSE_CACHE[next(iter(_RESPONSE_CACHE))]
    _RESPONSE_CACHE[key] = value


def _is_low_quality(text: str) -> bool:
    if len(text.strip()) < 60:
        return True
    low_q = ('не могу', 'не знаю', "i don't know", "i can't", 'unable to', 'sorry, ')
    return any(p in text.lower() for p in low_q)


class ST8ModelRouter:
    """Cascade router Haiku→Sonnet with LRU cache, prompt caching, and cost logging."""

    _HAIKU_KEYWORDS  = ('classify', 'search', 'summarize', 'route',
                        'категор', 'краткое', 'поиск', 'кратко')
    _SONNET_KEYWORDS = ('code', 'debug', 'architect', 'анализ', 'агент',
                        'код', 'архитект', 'разработ')

    def __init__(self, client: anthropic.Anthropic) -> None:
        self._client = client

    def select_model_by_task(self, system: str = '') -> str:
        low = system.lower()
        if any(k in low for k in self._SONNET_KEYWORDS):
            return _SONNET_MODEL
        return _HAIKU_MODEL  # default: cheap Haiku

    def call(self, messages: list, system: str = '', max_tokens: int = 1000):
        # 1. Truncate context
        system_t = _truncate_context(system)
        msgs = list(messages)
        if msgs and msgs[-1].get('role') == 'user':
            c = msgs[-1].get('content', '')
            if isinstance(c, str):
                msgs[-1] = {**msgs[-1], 'content': _truncate_context(c)}

        # 2. Cache check
        cache_key = _cache_md5(msgs, system_t)
        cached = _cache_get(cache_key)
        if cached is not None:
            _live_log.info('cache_hit=True key=%s', cache_key[:8])
            return cached

        # 3. Cascade: start model → optionally escalate
        start_model = self.select_model_by_task(system_t)
        cascade = [start_model]
        if start_model == _HAIKU_MODEL:
            cascade.append(_SONNET_MODEL)

        for model in cascade:
            resp = self._call_with_retry(model, msgs, system_t, max_tokens)
            if resp is None:
                continue
            text = resp.content[0].text if resp.content else ''
            if model == _HAIKU_MODEL and _is_low_quality(text):
                _live_log.info('quality_escalate haiku→sonnet')
                continue
            # 4. Log & cache
            tokens_in  = resp.usage.input_tokens  if resp.usage else 0
            tokens_out = resp.usage.output_tokens if resp.usage else 0
            cost = tokens_in * _MODEL_COST[model]['in'] + tokens_out * _MODEL_COST[model]['out']
            _live_log.info(
                'model=%s tokens_in=%d tokens_out=%d estimated_cost=$%.5f cache_hit=False',
                model, tokens_in, tokens_out, cost,
            )
            _cache_set(cache_key, resp)
            _log_token_usage(resp, model)
            return resp
        return None

    def _call_with_retry(self, model: str, messages: list, system: str, max_tokens: int):
        for attempt in range(3):
            try:
                kwargs: dict = {'model': model, 'max_tokens': max_tokens, 'messages': messages}
                if system:
                    # Prompt caching on the system block
                    kwargs['system'] = [
                        {'type': 'text', 'text': system,
                         'cache_control': {'type': 'ephemeral'}}
                    ]
                return self._client.messages.create(**kwargs)
            except Exception as e:
                if '529' in str(e) or 'overloaded' in str(e).lower():
                    time.sleep(10 * (attempt + 1))
                else:
                    raise
        return None


_router = ST8ModelRouter(claude_client)

# ── Smart Route (proactive model selection) ───────────────────────────────────

_ROUTING_HAIKU_MAX  = int(os.getenv('ROUTING_HAIKU_MAX_TOKENS', '100'))
_ROUTING_SONNET_MIN = int(os.getenv('ROUTING_SONNET_MIN_TOKENS', '500'))
_ROUTING_COMPLEX_KW = [
    kw.strip() for kw in os.getenv(
        'ROUTING_COMPLEX_KEYWORDS',
        '```code,\u0430\u043d\u0430\u043b\u0438\u0437,\u0430\u0440\u0445\u0438\u0442\u0435\u043a\u0442\u0443\u0440,\u0441\u0433\u0435\u043d\u0435\u0440,\u043d\u0430\u043f\u0438\u0448'
    ).split(',')
    if kw.strip()
]


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ~ 4 chars for mixed RU/EN text."""
    return len(text) // 4


def _has_complexity_signal(text: str) -> bool:
    """Check for code blocks or configured complex keywords."""
    low = text.lower()
    if '```' in text:
        return True
    return any(kw in low for kw in _ROUTING_COMPLEX_KW)


def _pick_model(user_text: str, system_prompt: str = '') -> str:
    """Proactive model selection BEFORE API call.

    Returns:
        _HAIKU_MODEL  -- simple / short request
        _SONNET_MODEL -- complex / long request
        None          -- ambiguous, let ST8ModelRouter cascade decide
    """
    combined = user_text + (system_prompt or '')
    token_est = _estimate_tokens(combined)

    # Rule 1: complexity keywords or code blocks -> Sonnet always
    if _has_complexity_signal(user_text):
        _live_log.info(
            'smart_route decision=sonnet reason=complexity_signal tokens_est=%d',
            token_est,
        )
        return _SONNET_MODEL

    # Rule 2: long request -> Sonnet
    if token_est >= _ROUTING_SONNET_MIN:
        _live_log.info(
            'smart_route decision=sonnet reason=high_tokens tokens_est=%d threshold=%d',
            token_est, _ROUTING_SONNET_MIN,
        )
        return _SONNET_MODEL

    # Rule 3: short + no complexity -> Haiku
    if token_est <= _ROUTING_HAIKU_MAX:
        _live_log.info(
            'smart_route decision=haiku reason=short_simple tokens_est=%d threshold=%d',
            token_est, _ROUTING_HAIKU_MAX,
        )
        return _HAIKU_MODEL

    # Rule 4: ambiguous (between thresholds, no complexity) -> None (fallback)
    _live_log.info(
        'smart_route decision=fallback reason=ambiguous tokens_est=%d',
        token_est,
    )
    return None


def smart_route(func):
    """Decorator: pick model proactively before calling the wrapped function.

    The wrapped function MUST accept ``model`` as a positional or keyword arg.
    If _pick_model returns a model string, it overrides ``model``.
    If _pick_model returns None, the original model is kept (ST8ModelRouter
    cascade will handle quality fallback downstream).
    """
    import functools

    @functools.wraps(func)
    def wrapper(user_text, *args, **kwargs):
        model_override = _pick_model(user_text)
        if model_override is not None:
            # Override the model parameter (3rd positional after user_text, history)
            # or keyword argument
            if 'model' in kwargs:
                kwargs['model'] = model_override
            elif len(args) >= 3:
                # args = (history, claude_client, model, ...)
                args = list(args)
                args[2] = model_override
                args = tuple(args)
            else:
                kwargs['model'] = model_override
        return func(user_text, *args, **kwargs)
    return wrapper

# ── end Smart Route ───────────────────────────────────────────────────────────
process_with_agent = smart_route(process_with_agent)

# ── end ST8ModelRouter ─────────────────────────────────────────────────────────

MOSCOW_TZ = pytz.timezone('Europe/Moscow')
LAST_JARVIS_RUN = {}

BASE_DIR = os.path.dirname(__file__)
MEMORY_PATH = os.path.join(BASE_DIR, 'jarvis_memory.json')
OFFSET_PATH = os.path.join(BASE_DIR, 'jarvis_offset.json')
AGENT_MEMORY_DIR = os.path.join(BASE_DIR, 'agent_memory')
MAX_MEMORY = 20


POLL_INTERVAL = 3


def _append_agent_memory(filename: str, event: str, details: str):
    """Дописывает строку в agent_memory/<filename> в формате: дата | событие | детали"""
    try:
        os.makedirs(AGENT_MEMORY_DIR, exist_ok=True)
        path = os.path.join(AGENT_MEMORY_DIR, filename)
        ts = datetime.now().strftime('%Y-%m-%d %H:%M')
        line = f"{ts} | {event} | {details}\n"
        with open(path, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception as exc:
        print(f"[agent_memory] ошибка записи {filename}: {exc}")

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
    'большакова': 'bolshakova', 'юлия': 'bolshakova', 'путь лидера': 'bolshakova',
    'unik': 'unik_food', 'уник': 'unik_food', 'антон': 'unik_food',
}


# в"Ђв"Ђв"Ђ Agent Memory в"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђ

def get_client_slug(text):
    msg_lower = text.lower()
    for key, slug in CLIENT_SLUGS.items():
        if key in msg_lower:
            return slug
    return None


def _auto_learn(user_text: str, claude_client) -> None:
    """Extract facts from what Alexey writes and persist to agent_memory."""
    try:
        t = user_text.strip()
        if not t or len(t) < 20 or t.startswith('/'):
            return
        _skip = ('завтрак ок', 'обед ок', 'ужин ок', 'нет ', 'замени ', 'переведи')
        if any(t.lower().startswith(p) for p in _skip):
            return

        resp = claude_client.messages.create(
            model=_HAIKU_MODEL,
            max_tokens=250,
            messages=[{"role": "user", "content": (
                f"Из сообщения извлеки важные факты для долгосрочной памяти.\n"
                f"Сообщение: {t}\n\n"
                f'Ответь строго JSON: {{"facts": ["факт 1"], "client": "имя или null"}}\n'
                f"facts — только конкретные данные (встречи, решения, цифры, планы). "
                f"Пустой список если нечего. Не извлекай вопросы и общие фразы."
            )}]
        )
        import json as _j
        raw = resp.content[0].text.strip()
        if '```' in raw:
            raw = raw.split('```')[1].lstrip('json').strip()
        data = _j.loads(raw)
        facts = data.get("facts", [])
        if not facts:
            return

        slug = get_client_slug(t)
        if not slug and data.get("client"):
            slug = str(data["client"]).lower().replace(' ', '_')[:20]
        target = (
            f"c:/st8-workspace/agent_memory/{slug}.md"
            if slug else
            "c:/st8-workspace/agent_memory/alexey_notes.md"
        )
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(target, 'a', encoding='utf-8') as fh:
            fh.write(f"\n## [auto] {date_str}\n")
            for f in facts:
                fh.write(f"- {f}\n")
    except Exception:
        pass


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
        except Exception as _exc:
            _live_log.exception("[load_agent_memory] unhandled exception")
            pass

    # Fallback: JSON file
    os.makedirs(AGENT_MEMORY_DIR, exist_ok=True)
    path = os.path.join(AGENT_MEMORY_DIR, f'{client_slug}.json')
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception as _exc:
            _live_log.exception("[load_agent_memory] unhandled exception")
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
    except Exception as _exc:
        _live_log.exception("[search_agent_memory] unhandled exception")
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
        except Exception as _exc:
            _live_log.exception("[save_agent_memory] unhandled exception")
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
    # Sync to Obsidian
    try:
        import os as _os
        obs_dir = r'C:\Users\user\Documents\Obsidian Vault\agent_memory'
        _os.makedirs(obs_dir, exist_ok=True)
        obs_path = _os.path.join(obs_dir, client_slug + '.md')
        with open(obs_path, 'w', encoding='utf-8') as _f:
            _f.write('# Memory: ' + client_slug + '\n\n')
            for m in memory[-10:]:
                _f.write('## ' + m['ts'] + '\n**Agent:** ' + m['agent'] + '\n**User:** ' + m['user'] + '\n**Response:** ' + m['response'] + '\n\n')
    except Exception:
        pass


# в"Ђв"Ђв"Ђ Agent Tools в"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђ

def tool_save_lead_status(company, status, comment=''):
    """Записывает статус лида в leads_status.md"""
    try:
        path = os.path.join(BASE_DIR, 'leads_status.md')
        date = datetime.now().strftime('%Y-%m-%d')
        line = f"| {date} | {company} | — | {status} | {comment} |\n"
        with open(path, 'a', encoding='utf-8') as f:
            f.write(line)
        _append_agent_memory('leads_log.md', 'лид', f'{company} | {status} | {comment}')
        return f"вњ… РЎС‚Р°С‚СѓСЃ СЃРѕС…СЂР°РЅС'РЅ: {company} в†' {status}"
    except Exception as exc:
        return f"⚠️ Ошибка сохранения статуса: {exc}"


def tool_save_kp(company, content):
    """Сохраняет КП в папку kp/"""
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
    """Отправляет сообщение Юле в Telegram"""
    if not JARVIS_BOT_TOKEN:
        return "Bot ne nastroyen"
    try:
        full_msg = f"Jarvis -> Юля:\n\n{message}"
        data = urllib.parse.urlencode({"chat_id": YULIA_CHAT_ID, "text": full_msg}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{JARVIS_BOT_TOKEN}/sendMessage", data=data)
        urllib.request.urlopen(req, timeout=10)
        return "✅ Сообщение отправлено Юле"
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
        return f"⚠️ Ошибка сохранения задачи: {exc}"


def execute_actions(actions_text):
    """Парсит и выполняет действия из текста агента"""
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
        _log_token_usage(response, CLAUDE_MODEL)
        agent_short = agent_name.replace('st8-', '').replace('-', ' ').title()
        return agent_short, result
    except Exception as exc:
        return None, f"РћС€РёР±РєР° Р°РіРµРЅС‚Р° {agent_name}: {exc}"


def run_agent_or_chain(user_message, history):
    """Запускает одного агента или цепочку, возвращает финальный ответ"""
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
        except Exception as _exc:
            _live_log.exception("[load_offset] unhandled exception")
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
                if len(cols) >= 5 and cols[0] != 'Дата':
                    rows.append({
                        'date': cols[0], 'company': cols[1],
                        'lpr': cols[2], 'status': cols[3], 'comment': cols[4]
                    })
    return rows


def format_reply(text: str) -> str:
    """Убирает Markdown-мусор перед отправкой в Telegram."""
    # Remove ``` code fences
    text = re.sub(r'```[a-zA-Z]*\n?', '', text)
    # Remove ## / ### headers
    text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)
    # Remove **bold** and *italic* (keep content)
    text = re.sub(r'\*{1,3}([^*\n]+)\*{1,3}', r'\1', text)
    # Remove --- dividers
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
    # Remove | table | rows
    text = re.sub(r'^\|.*\|$', '', text, flags=re.MULTILINE)
    # Lowercase ALL-CAPS Cyrillic words (2+ chars), skip ASCII abbreviations
    text = re.sub(r'\b([А-ЯЁ]{2,})\b', lambda m: m.group(1).lower(), text)
    # Remove [ ] and [x] checkboxes
    text = re.sub(r'\[[ xXvV✓]\]', '', text)
    # Collapse 3+ blank lines → 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


async def _tg_send(bot, chat_id: int, text: str):
    """Единая точка отправки: format_reply → bot.send_message."""
    await bot.send_message(chat_id=chat_id, text=format_reply(text))


def send_jarvis_message(text):
    if not JARVIS_BOT_TOKEN:
        print('JARVIS_BOT_TOKEN is not configured, skipping Jarvis message')
        return
    bot = Bot(token=JARVIS_BOT_TOKEN)
    try:
        asyncio.run(_tg_send(bot, JARVIS_CHAT_ID, text))
    except TelegramError as exc:
        print(f'Jarvis failed to send message: {exc}')
    except Exception as exc:
        print(f'Jarvis unexpected error sending message: {exc}')


def generate_jarvis_text(prompt):
    try:
        response = claude_client.messages.create(
            model=_HAIKU_MODEL, max_tokens=350,
            messages=[{"role": "user", "content": prompt}],
        )
        _text = response.content[0].text.strip()
        _log_token_usage(response, _HAIKU_MODEL)
        return _text
    except Exception as exc:
        return f"Jarvis generation failed: {exc}"


def create_prompt(header, context, instruction):
    today = now_moscow().strftime('%d %B %Y')
    return (
        "Ты — личный секретарь директора ST8 AI. Тон: деловой, чёткий, как реальный помощник. Используй информацию из Memory Bank. Не пиши шаблонный текст."
        f" Сегодня: {today}. {header}\n\nКонтекст:\n{context}\n\nЗадача:\n{instruction}\n"
        "Сформулируй одно сообщение для Telegram. "
        "СТРОГО: без Markdown (без **, без ##, без ```, без таблиц, без ---). "
        "Один эмодзи в начале строки. Строчные буквы в заголовках. Максимум 7 строк. "
        "Без приветствий и прощаний."
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
            f"🌤 {temp}°C, {description}, ветер {wind} км/ч\n"
            f"🧥 {clothing}\n☂️ зонт: {umbrella}\n👟 {footwear}"
        )
    except Exception as exc:
        print(f'[Jarvis] \u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u0438\u044f \u043f\u043e\u0433\u043e\u0434\u044b: {exc}')
        return None

def _leads_summary():
    leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    if not leads:
        return 'Лидов нет.'
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
        print(f'[Jarvis] Ошибка Tavily: {exc}')
        return None


SEARCH_TRIGGER_WORDS = [
    'что такое', 'кто такой', 'расскажи', 'найди', 'узнай',
    'новости', 'что нового', 'конференция', 'форум', 'выставка', 'актуально',
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
        _text = response.content[0].text.strip()
        _log_token_usage(response, CLAUDE_MODEL)
        return _text
    except Exception as exc:
        return f"Ошибка Claude: {exc}"


# в"Ђв"Ђв"Ђ Scheduled tasks в"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђ


def _weekly_weight_summary():
    wf = os.path.join(BASE_DIR, 'data', 'weight_log.json')
    if not os.path.exists(wf):
        return None
    try:
        wlog = json.loads(open(wf, encoding='utf-8').read())
    except Exception:
        return None
    if not wlog:
        return None
    today = now_moscow().date()
    week_data = []
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        if d in wlog:
            week_data.append((d, wlog[d]))
    if not week_data:
        return None
    lines = ['⚖️ вес за неделю:']
    for d, kg in week_data:
        lines.append(f'• {d}: {kg} кг')
    if len(week_data) >= 2:
        delta = week_data[-1][1] - week_data[0][1]
        sign = '+' if delta > 0 else ''
        lines.append(f'динамика: {sign}{delta:.1f} кг')
    return '\n'.join(lines)


def make_good_morning():
    weather_block = get_moscow_weather()
    now = now_moscow()
    today = now.date()
    weekday = now.weekday()  # 0=пн … 4=пт, 5=сб, 6=вс
    date_str = now.strftime('%d.%m.%Y')

    parts = ['☀️ Доброе утро, Алексей!\n']
    if weather_block:
        parts.append(weather_block)

    if weekday < 5:
        # ── будни: план по клиентам ──────────────────────────────────
        parts.append(f'\n📅 план дня — {date_str}\n')

        client_pipeline = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'clientPipeline.md'))
        active_context  = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))
        all_leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json')) or []

        _COLD   = {'новый', 'архив', 'холодный', ''}
        _URGENT = ('договор', 'подпис', 'срочно', 'дедлайн', 'горячий')
        p0, p1, p2 = [], [], []
        for lead in all_leads:
            status = (lead.get('status') or '').strip().lower()
            if status in _COLD:
                continue
            company = (lead.get('company_name') or '').strip()
            lpr     = (lead.get('lpr') or '—').strip()
            comment = (lead.get('comment') or '').strip()
            label   = comment or status
            entry   = f"{company} ({lpr})" + (f" — {label}" if label else '')
            try:
                days_ago = (today - datetime.strptime(lead['date'], '%Y-%m-%d').date()).days
            except Exception:
                days_ago = 0
            note_low = (comment + ' ' + status).lower()
            if any(kw in note_low for kw in _URGENT):
                p0.append(entry)
            elif days_ago >= 1:
                p1.append(entry)
            else:
                p2.append(entry)

        if p0:
            parts.append('🔴 P0 — срочно:')
            parts.extend(f'• {x}' for x in p0[:5])
        if p1:
            parts.append('\n🟡 P1 — важно:')
            parts.extend(f'• {x}' for x in p1[:5])
        if p2:
            parts.append('\n🟢 P2 — в работе:')
            parts.extend(f'• {x}' for x in p2[:5])

        if not (p0 or p1 or p2):
            context = f'clientPipeline:\n{client_pipeline}\n\nactiveContext:\n{active_context}'
            prompt  = create_prompt(
                'Доброе утро. Сформируй план дня.',
                context,
                'Топ-3 задачи на сегодня: кому позвонить/написать, '
                'что закрыть. Без воды, только конкретика. 3-5 строк.',
            )
            parts.append(generate_jarvis_text(prompt))

        known_clients = [
            ('AIRI',           'ждут договор / правки соглашения'),
            ('Unik Food',      'тест amoCRM — Антон'),
            ('Atelier Family', 'app v3, митап Марк/Ира'),
            ('Большакова',     'договор 200к — ждём подписания'),
            ('Лог. хаб',       '481 лид, топ: CDEK, Вэд партнер, Восточный путь'),
        ]
        parts.append('\n📋 клиенты:')
        parts.extend(f'• {name}: {st}' for name, st in known_clients)

    else:
        # ── выходные: отдых, без деловых задач ──────────────────────
        day_name = 'суббота' if weekday == 5 else 'воскресенье'
        parts.append(f'\n📅 {date_str} — {day_name}\n')
        parts.append('🏠 выходной — деловые задачи не планируем.')
        parts.append('Хороший день для личных дел, отдыха, саморазвития.')

        # воскресенье: недельная сводка по весу
        if weekday == 6:
            weight_block = _weekly_weight_summary()
            if weight_block:
                parts.append(f'\n{weight_block}')

    send_jarvis_message('\n'.join(parts))

def make_call_reminder():
    active_context = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))[:600]
    pipeline = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'clientPipeline.md'))[:400]
    prompt = create_prompt('Напоминание о звонках.', f"activeContext:\n{active_context}\n\nclientPipeline:\n{pipeline}",
        'Краткое напоминание о ключевых задачах и встречах.')
    send_jarvis_message(generate_jarvis_text(prompt))

def make_motivation():
    active_context = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))[:400]
    prompt = create_prompt('Короткая мотивация в 11:00.', active_context,
        'Одна конкретная фраза мотивации — про реальных клиентов или цели ST8-AI.')
    send_jarvis_message(generate_jarvis_text(prompt))

def make_lead_digest():
    leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    sample = '\n'.join([f"- {l.get('company_name')} ({l.get('segment', '?')})" for l in leads[:8]])
    prompt = create_prompt('Р"Р°Р№РґР¶РµСЃС‚ Р»РёРґРѕРІ.', f"Р›РёРґС‹:\n{sample}\nР'СЃРµРіРѕ: {len(leads)}",
        'РљСЂР°С‚РєРёР№ РѕС‚С‡С\'т: что стоит проверить сегодня.')
    send_jarvis_message(generate_jarvis_text(prompt))

def make_lunch_tip():
    prompt = create_prompt('Р\'ремя обеда 13:00.', '',
        'РќР°РїРѕРјРЅРё РїРѕРѕР±РµРґР°С‚СЊ Рё РґР°Р№ РѕРґРёРЅ РєРѕРЅРєСЂРµС‚РЅС‹Р№ СЃРѕРІРµС‚ РЅР° РІС‚РѕСЂСѓСЋ РїРѕР»РѕРІРёРЅСѓ РґРЅСЏ. Р\'ез воды.')
    send_jarvis_message(generate_jarvis_text(prompt))

def _generate_followup_text(company_name, lpr):
    prompt = (f"Напиши короткий follow-up для {company_name} ({lpr}). "
              f"Первое касание 3 дня назад. Тон: дружелюбный, один вопрос в конце. 2-3 предложения. "
              f"Без markdown, без звёздочек, без заголовков.")
    try:
        response = claude_client.messages.create(
            model=_HAIKU_MODEL, max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        _text = response.content[0].text.strip()
        _log_token_usage(response, _HAIKU_MODEL)
        return _text
    except Exception as exc:
        return f"(ошибка: {exc})"

def make_no_response_reminder():
    status_rows = load_markdown_table(os.path.join(BASE_DIR, 'leads_status.md'))
    leads_db = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    leads_by_name = {l.get('company_name', '').lower(): l for l in leads_db}
    old = []
    today = now_moscow().date()
    for row in status_rows:
        try:
            row_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
        except Exception as _exc:
            _live_log.exception("[make_no_response_reminder] unhandled exception")
            continue
        if row['status'] == 'написали' and (today - row_date).days >= 3:
            old.append(row)
    if not old:
        send_jarvis_message('Нет клиентов без ответа 3+ дней.')
        return
    messages = []
    for row in old[:5]:
        company, lpr = row['company'], row['lpr']
        phone = leads_by_name.get(company.lower(), {}).get('phone', '—')
        followup = _generate_followup_text(company, lpr)
        messages.append(f"📌 {company}\n📞 {phone}\n{followup}")
    send_jarvis_message(f"⏰ перезвон нужен {len(old)} клиентам:\n\n" + '\n\n'.join(messages))

def make_day_summary():
    active_context = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))[:600]
    pipeline = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'clientPipeline.md'))[:400]
    status_rows = load_markdown_table(os.path.join(BASE_DIR, 'leads_status.md'))
    summary_rows = '\n'.join([f"- {r['company']}: {r['status']}" for r in status_rows[:6]])
    context = f"activeContext:\n{active_context}\n\nclientPipeline:\n{pipeline}\n\nleads:\n{summary_rows}"
    prompt = create_prompt('Итог дня.', context, 'Краткое резюме дня и что перенести на завтра.')
    send_jarvis_message(generate_jarvis_text(prompt))

def make_weekly_report():
    active_context = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))[:800]
    pipeline = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'clientPipeline.md'))[:500]
    leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    sample = '\n'.join([f"- {l.get('company_name')} ({l.get('segment', '?')})" for l in leads[:10]])
    context = f"activeContext:\n{active_context}\n\nclientPipeline:\n{pipeline}\n\nЛиды:\n{sample}\nВсего: {len(leads)}"
    prompt = create_prompt('Недельный отчёт.', context, 'Деловой еженедельный отчёт с выводами и рекомендациями.')
    send_jarvis_message(generate_jarvis_text(prompt))

def make_energy_boost():
    pipeline = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'clientPipeline.md'))[:400]
    prompt = create_prompt('Энергия в 16:00.', pipeline,
        'Что ещё успеть до конца дня из пайплайна. Конкретно, 2-3 действия.')
    send_jarvis_message(generate_jarvis_text(prompt))

def make_evening_summary():
    active_context = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))[:400]
    prompt = create_prompt('Вечер 19:00.', active_context,
        'Что хорошего случилось сегодня, одно пожелание на вечер. Тепло, без официоза.')
    send_jarvis_message(generate_jarvis_text(prompt))


_ALIVE_TYPES = [
    "интересный факт из бизнеса, психологии или науки — одна строка, неожиданно",
    "короткая мысль про продажи или переговоры — что-то нестандартное",
    "случайное наблюдение про жизнь предпринимателя — честно и без пафоса",
    "странный но полезный лайфхак — коротко",
    "вопрос для размышления — один, без ответа",
    "цитата которую ты сам бы не нашёл — не банальная",
]

def make_alive_message():
    import random
    msg_type = random.choice(_ALIVE_TYPES)
    claude_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY', ''))
    try:
        resp = claude_client.messages.create(
            model=_HAIKU_MODEL,
            max_tokens=120,
            messages=[{"role": "user", "content": (
                f"Ты Джарвис — AI-ассистент Алексея. Напиши сообщение: {msg_type}.\n"
                "Стиль: разговорный, живой, без Markdown, без эмодзи кроме одного в начале. "
                "Максимум 2-3 строки. Не представляйся."
            )}]
        )
        text = resp.content[0].text.strip()
        send_jarvis_message(text)
    except Exception:
        pass


# в"Ђв"Ђв"Ђ Commands в"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђ

def cmd_plan(history):
    client_pipeline = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'clientPipeline.md'))
    active_context = read_file(os.path.join(BASE_DIR, 'st8-memory-bank', 'activeContext.md'))
    prompt = create_prompt('РЎРѕСЃС‚Р°РІСЊ РїР»Р°РЅ РґРЅСЏ.', f"clientPipeline:\n{client_pipeline}\n\nactiveContext:\n{active_context}",
        'Кому позвонить, кому написать, что приоритетно сегодня.')
    return generate_jarvis_text(prompt)

def cmd_leads(history):
    leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
    lines = [f"{i}. {l.get('company_name', '?')} [{l.get('segment', '—')}]" for i, l in enumerate(leads[:10], 1)]
    context = f"Р›РёРґС‹ ({len(leads)} РІСЃРµРіРѕ):\n" + '\n'.join(lines)
    prompt = create_prompt('Р"Р°Р№РґР¶РµСЃС‚ Р»РёРґРѕРІ.', context, 'Краткий обзор: на каких сосредоточиться.')
    return generate_jarvis_text(prompt)

def cmd_hub():
    import json as _json
    try:
        with open(os.path.join(BASE_DIR, 'st8hub', 'leads.json'), 'r', encoding='utf-8') as _f:
            _leads = _json.load(_f)
    except Exception as _exc:
        _live_log.exception("[cmd_hub] unhandled exception")
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
                   f"Р›РџР : {lead.get('lpr')}\nР'оль: {lead.get('pain')}\n"
                   f"РљРѕРЅС‚Р°РєС‚: {lead.get('telegram_social') or lead.get('email') or 'не указан'}\n\nPipeline:\n{pipeline[:800]}")
    else:
        context = f"РљР»РёРµРЅС‚ '{client_name}' РЅРµ РЅР°Р№РґРµРЅ.\n\nPipeline:\n{pipeline[:1000]}"
    prompt = create_prompt(f'РРЅС„РѕСЂРјР°С†РёСЏ РїРѕ РєР»РёРµРЅС‚Сѓ: {client_name}', context, 'Сводка: что известно, статус, следующий шаг.')
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

_CALL_TRIGGERS = ('звоню', 'звонок', 'созвон')

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
    except Exception as _exc:
        _live_log.exception("[cmd_call_prep] unhandled exception")
        pass
    prompt = (
        f"РџРѕРґРіРѕС‚РѕРІСЊ СЃРєСЂРёРїС‚ Р·РІРѕРЅРєР° РґР»СЏ ST8-AI. "
        f"РљРѕРјРїР°РЅРёСЏ: {company_name}, Р›РџР : {lpr}, СЃРµРіРјРµРЅС‚: {segment}, Р±РѕР»СЊ: {pain}. "
        f"РРЅС„РѕСЂРјР°С†РёСЏ: {tavily_results or 'нет данных'}. "
        f"РЎРєСЂРёРїС‚: РїСЂРёРІРµС‚СЃС‚РІРёРµ в†' Р±РѕР»СЊ в†' СЂРµС€РµРЅРёРµ в†' РІРѕРїСЂРѕСЃ в†' РІРѕР·СЂР°Р¶РµРЅРёСЏ 'дорого' Рё 'уже есть система'."
    )
    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL, max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        script = response.content[0].text.strip()
        _log_token_usage(response, CLAUDE_MODEL)
    except Exception as exc:
        script = f"Ошибка: {exc}"
    return f"рџ\"ћ РЎРєСЂРёРїС‚ Р·РІРѕРЅРєР° — {company_name}\nР›РџР : {lpr} | {segment}\n\n{script}"


# ── Умное добавление лидов (естественный язык) ───────────────────────────────

def is_add_lead_intent(text: str) -> bool:
    triggers = [
        r'добавь.*(клиент|лид|компанию|контакт)',
        r'новый\s+(клиент|лид|контакт|потенциальный)',
        r'запиши\s+(компанию|клиента|контакт|лид)',
        r'вот\s+(новый\s+)?(контакт|лид|клиент)',
        r'сохрани\s+(компанию|клиента|контакт)',
        r'занеси\s+в\s+(хаб|базу|crm)',
        r'добавь\s+в\s+список',
        r'позвонил\s+([A-ZА-Я][a-zа-я]+)',
        r'нашел\s+(клиента|контакт)',
    ]
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in triggers)


def extract_lead_data(text: str) -> dict:
    prompt = (
        f'Извлечи из текста данные о клиенте/компании. Верни ТОЛЬКО JSON, без пояснений.'
        f'\n\nТекст: "{text}"\n\n'
        'Поля: company_name, lpr, phone, '
        'segment (логистика/хорека/ритейл/производство/IT/банк), pain, '
        'status (новый/переговоры/встреча назначена/думает), '
        'source (телеграм/звонок/рекомендация). '
        'Если данных нет — "—" или null.'
    )
    try:
        response = claude_client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.content[0].text.strip()
        _log_token_usage(response, 'claude-haiku-4-5-20251001')
        if result.startswith('```'):
            result = result.split('```')[1]
            if result.startswith('json'): result = result[4:]
        data = json.loads(result.strip())
        if not data.get('company_name') or data['company_name'] == '—':
            return None
        data.setdefault('segment', '—')
        data.setdefault('pain',    '—')
        data.setdefault('status',  'новый')
        data.setdefault('source',  'telegram')
        data.setdefault('lpr',     '—')
        data.setdefault('phone',   '—')
        data['date']       = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        return data
    except Exception as exc:
        print(f'[Jarvis] Ошибка извлечения лида: {exc}')
        return None


def _find_lead_by_company(name: str) -> dict:
    """Search leads.json by partial company name (case-insensitive)."""
    try:
        leads = load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json'))
        name_low = name.lower()
        for lead in leads:
            if name_low in lead.get('company_name', '').lower():
                return lead
        return None
    except Exception as _exc:
        _live_log.exception("[_find_lead_by_company] unhandled exception")
        return None


def _update_lead(company_name: str, new_data: dict) -> None:
    path = os.path.join(BASE_DIR, 'st8hub', 'leads.json')
    leads = load_json(path)
    for lead in leads:
        if company_name.lower() in lead.get('company_name', '').lower():
            lead.update(new_data)
            lead['updated_at'] = datetime.now().isoformat()
            break
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)


def _save_lead_to_hub(lead_data: dict) -> None:
    path = os.path.join(BASE_DIR, 'st8hub', 'leads.json')
    leads = load_json(path)
    leads.append(lead_data)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)


def _count_total_leads() -> int:
    try:
        return len(load_json(os.path.join(BASE_DIR, 'st8hub', 'leads.json')))
    except Exception as _exc:
        _live_log.exception("[_count_total_leads] unhandled exception")
        return 0


def smart_add_lead(user_text: str):
    """Умное добавление лида без команд — просто текст (Haiku, дешево)."""
    if not is_add_lead_intent(user_text):
        return None
    lead_data = extract_lead_data(user_text)
    if not lead_data:
        return '🤔 Не смог разобрать данные. Уточни название компании и телефон.'
    existing = _find_lead_by_company(lead_data['company_name'])
    if existing:
        _update_lead(lead_data['company_name'], lead_data)
        return (
            f'✅ обновил: {lead_data["company_name"]}\n'
            f'📞 {lead_data.get("phone", "—")} | '
            f'👤 {lead_data.get("lpr", "—")} | '
            f'📊 {lead_data.get("status", "новый")}'
        )
    _save_lead_to_hub(lead_data)
    msg = f'✅ добавил в хаб: {lead_data["company_name"]}\n'
    if lead_data.get('lpr')     and lead_data['lpr']     != '—': msg += f'👤 {lead_data["lpr"]}\n'
    if lead_data.get('phone')   and lead_data['phone']   != '—': msg += f'📞 {lead_data["phone"]}\n'
    if lead_data.get('segment') and lead_data['segment'] != '—': msg += f'🏢 {lead_data["segment"]}\n'
    if lead_data.get('pain')    and lead_data['pain']    != '—': msg += f'💡 {lead_data["pain"]}\n'
    msg += f'\n📊 Всего в хабе: {_count_total_leads()} лидов'
    return msg


# ─── SYSTEM STATUS / SERVICE CONTROL ─────────────────────────────────────────

_SVC_ALIASES = {
    'jarvis': 'jarvis', 'бот': 'jarvis', 'джарвис': 'jarvis',
    'meal': 'meal', 'питание': 'meal', 'еда': 'meal',
    'n8n': 'n8n',
    'errwatch': 'errwatch', 'watcher': 'errwatch', 'монитор': 'errwatch',
    'dashboard': 'dashboard', 'дашборд': 'dashboard', 'статус демон': 'dashboard',
}


def _cmd_system_status() -> str:
    import psutil, socket

    def _py_running(script: str):
        for p in psutil.process_iter(['pid', 'cmdline']):
            try:
                args = p.info['cmdline'] or []
                if any(
                    arg == script or arg.endswith('/' + script) or arg.endswith('\\' + script)
                    for arg in args
                ):
                    return p.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return None

    def _port_listening(port: int) -> bool:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.5):
                return True
        except OSError:
            return False

    checks = [
        ('Jarvis bot',       _py_running('jarvis.py')),
        ('Watchdog',         _py_running('jarvis_watchdog.py')),
        ('Scheduler',        _py_running('scheduler.py') or _py_running('meal_scheduler.py')),
        ('Dashboard daemon', _py_running('st8_status_daemon.py')),
        ('n8n',              _port_listening(5678)),
    ]

    lines = ["🖥 ST8-AI СЕРВИСЫ\n"]
    for name, result in checks:
        if result is True or (result and result is not False):
            pid_str = f" (PID {result})" if isinstance(result, int) else ""
            lines.append(f"✅ {name} — работает{pid_str}")
        else:
            lines.append(f"🔴 {name} — остановлен")

    return "\n".join(lines)


def _is_service_control(text: str) -> bool:
    t = text.strip().lower()
    return any(t.startswith(p) for p in (
        'включи ', 'запусти ', 'выключи ', 'останови ', 'перезапусти ',
    ))


def _handle_service_control(text: str) -> str:
    t = text.strip().lower()
    if t.startswith(('включи ', 'запусти ')):
        action, rest = 'start', t.split(' ', 1)[1].strip()
    elif t.startswith(('выключи ', 'останови ')):
        action, rest = 'stop', t.split(' ', 1)[1].strip()
    elif t.startswith('перезапусти '):
        action, rest = 'restart', t.split(' ', 1)[1].strip()
    else:
        return "❓ не понял команду"

    key = _SVC_ALIASES.get(rest)
    if not key:
        available = ', '.join(_SVC_ALIASES.keys())
        return f"❓ сервис '{rest}' не найден.\nДоступные: {available}"

    try:
        from service_manager import start_service, stop_service
    except ImportError:
        return "❌ service_manager недоступен"

    if action == 'start':
        ok, msg = start_service(key)
    elif action == 'stop':
        ok, msg = stop_service(key)
    else:
        stop_service(key)
        import time as _t; _t.sleep(2)
        ok, msg = start_service(key)
        msg = "перезапущен: " + msg

    icon = "✅" if ok else "❌"
    return f"{icon} {key}: {msg}"


# ─── HUB COMMAND HANDLERS ────────────────────────────────────────────────────

def _is_hub_archive_command(text: str) -> bool:
    low = text.lower()
    return bool(re.search(r'(^|\s)(архив|архивируй|в\s+архив)\s+\S', low))

def _is_hub_update_command(text: str) -> bool:
    low = text.lower()
    return bool(re.search(r'(обнови|измени\s+статус|поменяй\s+статус)\s+\S', low))

def _handle_hub_update(text: str) -> str:
    low = text.lower()
    m = (
        re.search(r'обнови\s+(.+?)\s+[-—]\s*(?:статус\s+)?(.+)', low) or
        re.search(r'обнови\s+(.+?)\s+статус\s+(.+)', low) or
        re.search(r'(?:измени|поменяй)\s+статус\s+(.+?)\s+на\s+(.+)', low)
    )
    if not m:
        return "не понял команду. формат: обнови Компания — статус горячий"
    company_raw = m.group(1).strip().rstrip('-— ')
    new_status  = m.group(2).strip()
    lead = _find_lead_by_company(company_raw)
    if not lead:
        return f"компания не найдена в хабе: {company_raw}"
    _update_lead(company_raw, {"status": new_status, "comment": new_status})
    return f"✅ обновил {lead['company_name']}\n📊 статус: {new_status}"

def _handle_hub_archive(text: str) -> str:
    m = re.search(r'(?:архив|архивируй|в\s+архив)\s+(.+)', text.lower())
    if not m:
        return "формат: архив Название компании"
    company_raw = m.group(1).strip()
    lead = _find_lead_by_company(company_raw)
    if not lead:
        return f"компания не найдена в хабе: {company_raw}"
    _update_lead(company_raw, {"status": "архив"})
    return f"📦 {lead['company_name']} — перемещено в архив"


_WEATHER_PATTERNS = (
    'погода', 'weather', 'температур', 'дождь', 'зонт', 'одеть', 'одето',
    'тепло', 'холодно', 'ветер', 'за окном', 'на улице', 'выглян',
)

def _is_weather_question(text: str) -> bool:
    low = text.lower()
    return any(p in low for p in _WEATHER_PATTERNS)


# ─── MEAL HANDLERS ────────────────────────────────────────────────────────────

_MEAL_CONFIRM_PHRASES = ("завтрак ок", "обед ок", "ужин ок")

def _is_meal_confirm(text: str) -> bool:
    low = text.strip().lower()
    return any(p in low for p in _MEAL_CONFIRM_PHRASES)

def _is_meal_substitute(text: str) -> bool:
    low = text.strip().lower()
    return (low.startswith("нет ") or low.endswith(" нет") or
            low.startswith("замени ") or low.startswith("заменить "))

import re as _re
_WEIGHT_RE = _re.compile(r'(?:^|мой\s+)?(?:вес|весит|вешу)\s+(\d{2,3}(?:[.,]\d{1,2})?)\s*(?:кг|kg)?', _re.IGNORECASE)

def _parse_weight_from_text(text: str):
    """Return float kg if text is a natural-language weight report, else None."""
    m = _WEIGHT_RE.search(text.strip())
    if m:
        try:
            return float(m.group(1).replace(',', '.'))
        except ValueError:
            pass
    return None

_DAILY_KCAL_LIMIT = 1900
_FOOD_LOG_FILE = os.path.join(BASE_DIR, 'data', 'food_log.json')

_FOOD_INTAKE_WORDS = ('съел', 'съела', 'поел', 'поела', 'выпил', 'выпила',
                      'перекусил', 'перекусила', 'покушал', 'покушала',
                      'скушал', 'скушала', 'позавтракал', 'пообедал', 'поужинал',
                      'позавтракала', 'пообедала', 'поужинала')

def _is_food_intake(text: str) -> bool:
    low = text.lower()
    return any(w in low for w in _FOOD_INTAKE_WORDS)

def _estimate_kcal(food_text: str) -> tuple[int, str]:
    """Return (kcal, food_name) via Haiku."""
    try:
        resp = claude_client.messages.create(
            model=_HAIKU_MODEL,
            max_tokens=80,
            messages=[{"role": "user", "content": (
                f"Оцени калорийность: «{food_text}»\n"
                f"Ответь строго JSON: {{\"kcal\": 250, \"food\": \"краткое название\"}}\n"
                f"kcal — целое число, без текста вокруг."
            )}]
        )
        import json as _j
        raw = resp.content[0].text.strip()
        if '```' in raw:
            raw = raw.split('```')[1].lstrip('json').strip()
        data = _j.loads(raw)
        return int(data['kcal']), str(data.get('food', food_text[:40]))
    except Exception:
        return 0, food_text[:40]

def _get_today_food_log() -> list:
    today = now_moscow().date().isoformat()
    try:
        log = json.loads(open(_FOOD_LOG_FILE, encoding='utf-8').read()) if os.path.exists(_FOOD_LOG_FILE) else {}
    except Exception:
        log = {}
    return log.get(today, [])

def _append_food_log(food: str, kcal: int):
    today = now_moscow().date().isoformat()
    try:
        log = json.loads(open(_FOOD_LOG_FILE, encoding='utf-8').read()) if os.path.exists(_FOOD_LOG_FILE) else {}
    except Exception:
        log = {}
    if today not in log:
        log[today] = []
    log[today].append({'food': food, 'kcal': kcal, 'ts': now_moscow().strftime('%H:%M')})
    os.makedirs(os.path.dirname(_FOOD_LOG_FILE), exist_ok=True)
    open(_FOOD_LOG_FILE, 'w', encoding='utf-8').write(json.dumps(log, ensure_ascii=False, indent=2))

def _handle_food_intake(user_text: str) -> str:
    kcal, food = _estimate_kcal(user_text)
    if kcal > 0:
        _append_food_log(food, kcal)
    today_log = _get_today_food_log()
    total = sum(e['kcal'] for e in today_log)
    remaining = _DAILY_KCAL_LIMIT - total
    lines = [f"🍽 {food} — ~{kcal} ккал", f"сегодня итого: {total} / {_DAILY_KCAL_LIMIT} ккал"]
    if remaining < 0:
        lines.append(f"⚠️ перебор на {abs(remaining)} ккал — полегче вечером.")
    elif remaining < 200:
        lines.append(f"⚡ осталось {remaining} ккал — почти лимит.")
    else:
        lines.append(f"✅ остаток: {remaining} ккал")
    return '\n'.join(lines)


def _save_weight_and_reply(kg: float) -> str:
    """Save weight to weight_log.json and return a concise reply with delta."""
    _wf = os.path.join(BASE_DIR, 'data', 'weight_log.json')
    try:
        _wlog = json.loads(open(_wf, encoding='utf-8').read()) if os.path.exists(_wf) else {}
    except Exception:
        _wlog = {}
    today_key = now_moscow().date().isoformat()
    prev_kg, prev_date = None, None
    for d in sorted(_wlog.keys(), reverse=True):
        if d != today_key:
            prev_kg, prev_date = _wlog[d], d
            break
    _wlog[today_key] = kg
    os.makedirs(os.path.dirname(_wf), exist_ok=True)
    open(_wf, 'w', encoding='utf-8').write(json.dumps(_wlog, ensure_ascii=False, indent=2))
    _append_agent_memory('health.md', 'вес записан', f'{kg} кг')
    if prev_kg is not None:
        delta = kg - prev_kg
        sign = '+' if delta > 0 else ''
        lines = [f"⚖️ {kg} кг записан.", f"предыдущий замер {prev_date}: {prev_kg} кг", f"динамика: {sign}{delta:.1f} кг"]
        if delta < 0:
            lines.append("💪 Молодец, продолжай в том же духе!")
        elif delta > 0:
            lines.append("Бывает. Держим курс.")
        return '\n'.join(lines)
    return f"⚖️ {kg} кг записан."

def _find_meal_for_product(product: str) -> dict | None:
    """Find which meal in today's confirmed plan contains the product."""
    today = datetime.now().date().isoformat()
    cpath = os.path.join(BASE_DIR, 'data', f'confirmed_menu_{today}.json')
    if not os.path.exists(cpath):
        return None
    try:
        confirmed = json.loads(open(cpath, encoding='utf-8').read())
        p_low = product.lower()
        root = p_low[:4] if len(p_low) >= 4 else p_low
        for meal in confirmed.get('plan', {}).get('meals', []):
            for item in meal.get('items', []):
                if root in item.lower() or p_low in item.lower():
                    return meal
    except Exception:
        pass
    return None

def _save_meal_substitution(product: str, substitute: str):
    today = datetime.now().date().isoformat()
    cpath = os.path.join(BASE_DIR, 'data', f'confirmed_menu_{today}.json')
    if not os.path.exists(cpath):
        return
    try:
        confirmed = json.loads(open(cpath, encoding='utf-8').read())
        confirmed.setdefault('substitutions', {})[product] = substitute
        open(cpath, 'w', encoding='utf-8').write(
            json.dumps(confirmed, ensure_ascii=False, indent=2)
        )
    except Exception:
        pass

def _handle_meal_substitute(user_text: str, claude_client) -> str:
    t = user_text.strip().lower()
    if t.startswith("нет "):
        product = t[4:].strip()
    elif t.endswith(" нет"):
        product = t[:-4].strip()
    elif t.startswith("замени "):
        product = t[7:].strip()
    elif t.startswith("заменить "):
        product = t[9:].strip()
    else:
        product = t

    meal = _find_meal_for_product(product)
    kcal    = meal["kcal"]    if meal else 0
    protein = meal["protein"] if meal else 0
    carbs   = meal["carbs"]   if meal else 0
    fat     = meal["fat"]     if meal else 0
    meal_name_map = {
        "breakfast": "Завтрак", "snack1": "Перекус 1",
        "lunch": "Обед", "snack2": "Перекус 2", "dinner": "Ужин",
    }
    meal_label = meal_name_map.get(meal["id"], "") if meal else ""

    prompt = (
        f"Замени {product} на доступное в России, "
        f"сохрани КБЖУ: ккал {kcal}, белок {protein}g, "
        f"углеводы {carbs}g, жиры {fat}g. "
        f"Ответь только блюдом и граммовкой."
    )
    try:
        msg = claude_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=80,
            messages=[{"role": "user", "content": prompt}],
        )
        substitute = msg.content[0].text.strip()
        _save_meal_substitution(product, substitute)
        _log_token_usage(msg, "claude-haiku-4-5-20251001")
        prefix = f"🔄 {meal_label} — " if meal_label else "🔄 "
        return f"{prefix}замена {product}:\n{substitute}"
    except Exception as e:
        return f"⚠️ Не удалось подобрать замену: {e}"


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


async def handle_photo_message(bot, msg) -> str:
    """Фото → Claude Vision. Caption 'переведи' → OCR+перевод, иначе → описание."""
    import tempfile, base64
    photo = msg.photo[-1]
    tg_file = await bot.get_file(photo.file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        await tg_file.download_to_drive(tmp.name)
        path = tmp.name
    try:
        with open(path, "rb") as f:
            img_b64 = base64.standard_b64encode(f.read()).decode("utf-8")
    finally:
        os.unlink(path)
    caption = (msg.caption or "").strip().lower()
    if "переведи" in caption:
        prompt = "Найди весь текст на изображении и переведи на русский язык. Без markdown, без звёздочек."
    else:
        prompt = "Опиши что изображено на фото. Коротко и по-деловому. Без markdown. Максимум 5 строк."
    response = claude_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
            {"type": "text", "text": prompt},
        ]}],
    )
    _log_token_usage(response, CLAUDE_MODEL)
    return response.content[0].text.strip()


def _translate_text(text: str) -> str:
    """Кириллица → английский, иначе → русский."""
    cyrillic = sum(1 for c in text if 'Ѐ' <= c <= 'ӿ')
    if cyrillic > len(text) * 0.3:
        prompt = f"Переведи на английский язык. Без markdown, без звёздочек.\n\n{text}"
    else:
        prompt = f"Переведи на русский язык. Без markdown, без звёздочек.\n\n{text}"
    response = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    _log_token_usage(response, CLAUDE_MODEL)
    return response.content[0].text.strip()


def _translate_document(text: str, fname: str) -> str:
    """Перевод документа на русский с сохранением структуры."""
    prompt = (
        f"Переведи на русский язык. Сохрани структуру документа. "
        f"Без markdown, без звёздочек.\n\nДокумент ({fname}):\n\n{text[:12000]}"
    )
    response = claude_client.messages.create(
        model=CLAUDE_MODEL, max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    _log_token_usage(response, CLAUDE_MODEL)
    return response.content[0].text.strip()


def _parse_token_stats() -> str:
    """Parse jarvis_live.log for [TOKEN] lines, aggregate today (MSK) by model."""
    today_str = now_moscow().strftime('%Y-%m-%d')
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarvis_live.log')
    stats: dict = {}  # model -> {calls, inp, out, cost}
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '[TOKEN]' not in line:
                    continue
                # Line format: "2026-04-15 12:34:56,789 [TOKEN] model=X input=N output=N cost=$N"
                if not line.startswith(today_str):
                    continue
                parts = {}
                for segment in line.split():
                    if '=' in segment:
                        k, v = segment.split('=', 1)
                        parts[k] = v
                model = parts.get('model', 'unknown')
                try:
                    inp = int(parts.get('input', '0'))
                    out = int(parts.get('output', '0'))
                    cost = float(parts.get('cost', '$0').lstrip('$'))
                except (ValueError, TypeError):
                    continue
                if model not in stats:
                    stats[model] = {'calls': 0, 'inp': 0, 'out': 0, 'cost': 0.0}
                stats[model]['calls'] += 1
                stats[model]['inp'] += inp
                stats[model]['out'] += out
                stats[model]['cost'] += cost
    except FileNotFoundError:
        pass
    if not stats:
        return '\U0001f4ca ' + today_str + ' \u2014 \u043d\u0435\u0442 \u0432\u044b\u0437\u043e\u0432\u043e\u0432 API \u0441\u0435\u0433\u043e\u0434\u043d\u044f'
    lines = ['\U0001f4ca \u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430 \u0442\u043e\u043a\u0435\u043d\u043e\u0432 \u2014 ' + today_str + ' \u041c\u0421\u041a\n']
    grand_total = 0.0
    for model_name in sorted(stats):
        s = stats[model_name]
        grand_total += s['cost']
        lines.append(f"{model_name}:")
        lines.append(f"  \u0412\u044b\u0437\u043e\u0432\u044b: {s['calls']}")
        lines.append(f"  \u0422\u043e\u043a\u0435\u043d\u044b: {s['inp']:,} / {s['out']:,} (in/out)")
        lines.append(f"  \u0421\u0442\u043e\u0438\u043c\u043e\u0441\u0442\u044c: ${s['cost']:.4f}\n")
    lines.append('\u2500' * 20)
    lines.append(f"\u0418\u0442\u043e\u0433\u043e \u0441\u0435\u0433\u043e\u0434\u043d\u044f: ${grand_total:.4f}")
    return '\n'.join(lines)


# в"Ђв"Ђв"Ђ Polling в"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђв"Ђ

async def poll_jarvis():
    if not JARVIS_BOT_TOKEN:
        print('JARVIS_BOT_TOKEN РЅРµ Р·Р°РґР°РЅ — polling РѕС‚РєР»СЋС‡С\'н')
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
                if msg.photo:
                    reply = await handle_photo_message(bot, msg)
                    ts = datetime.now().isoformat(timespec='seconds')
                    history = load_memory()
                    history.append({"role": "user", "content": f"[фото] {(msg.caption or '').strip()}", "ts": ts})
                    history.append({"role": "assistant", "content": reply, "ts": ts})
                    save_memory(history)
                    await _tg_send(bot, JARVIS_CHAT_ID, reply)
                    continue
                elif msg.document:
                    file_text = await extract_file_text(bot, msg)
                    if file_text and not file_text.startswith('['):
                        reply = _translate_document(file_text, msg.document.file_name or "документ")
                        ts = datetime.now().isoformat(timespec='seconds')
                        history = load_memory()
                        history.append({"role": "user", "content": f"[документ: {msg.document.file_name}]", "ts": ts})
                        history.append({"role": "assistant", "content": reply, "ts": ts})
                        save_memory(history)
                        await _tg_send(bot, JARVIS_CHAT_ID, reply)
                        continue
                    else:
                        user_text = f'[Файл: {msg.document.file_name}]\n{file_text or "не удалось прочитать"}'
                elif msg.text:
                    user_text = msg.text
                else:
                    continue
                history = load_memory()
                # Погода — отвечаем напрямую, не отдаём в Claude
                if is_auto_hunt_command(user_text):
                    reply = handle_auto_hunt_command(user_text)
                elif is_agent_command(user_text):
                    import asyncio as _aio
                    reply = _aio.get_event_loop().run_until_complete(handle_agents_command(user_text))
                elif user_text.strip().lower().startswith('/email'):
                    # /email Название компании | email@example.com
                    parts = user_text.strip()[7:].split('|')
                    if len(parts) == 2:
                        company = parts[0].strip()
                        email = parts[1].strip()
                        import subprocess
                        result = subprocess.run(
                            ['python', 'email_agent.py', company, email],
                            capture_output=True, text=True, cwd=BASE_DIR
                        )
                        reply = f"📧 КП отправлено на {email} для {company}"
                    else:
                        reply = "Формат: /email Название компании | email@example.com"
                elif user_text.strip().lower() in ('/система', 'статус сервисов', 'статус системы'):
                    reply = _cmd_system_status()
                elif _is_service_control(user_text):
                    reply = _handle_service_control(user_text)
                elif user_text.strip().lower().startswith('/stats'):
                    reply = _parse_token_stats()
                elif user_text.strip().lower().startswith('/вес'):
                    _wparts = user_text.strip().split()
                    if len(_wparts) >= 2:
                        try:
                            kg = float(_wparts[1].replace(',', '.'))
                            reply = _save_weight_and_reply(kg)
                        except ValueError:
                            reply = "⚖️ Формат: /вес 82.5"
                    else:
                        reply = "⚖️ Формат: /вес 82.5"
                elif _is_meal_confirm(user_text):
                    from meal_scheduler import handle_meal_confirm
                    result = handle_meal_confirm(user_text)
                    reply = result if result else "👍 Записал"
                elif _is_meal_substitute(user_text):
                    reply = _handle_meal_substitute(user_text, claude_client)
                elif _is_weather_question(user_text):
                    reply = get_moscow_weather()
                elif user_text.strip().lower().startswith('переведи'):
                    to_translate = user_text.strip()[8:].strip()
                    reply = _translate_text(to_translate) if to_translate else "напиши: переведи [текст]"
                elif _is_hub_archive_command(user_text):
                    reply = _handle_hub_archive(user_text)
                elif _is_hub_update_command(user_text):
                    reply = _handle_hub_update(user_text)
                elif _is_food_intake(user_text):
                    reply = _handle_food_intake(user_text)
                elif (_nlw := _parse_weight_from_text(user_text)) is not None:
                    reply = _save_weight_and_reply(_nlw)
                elif is_add_lead_intent(user_text):
                    result = smart_add_lead(user_text)
                    reply = result if result else process_with_agent(user_text, history, claude_client, CLAUDE_MODEL)
                else:
                    reply = process_with_agent(user_text, history, claude_client, CLAUDE_MODEL)
                import threading as _thr
                _thr.Thread(target=_auto_learn, args=(user_text, claude_client), daemon=True).start()
                ts = datetime.now().isoformat(timespec='seconds')
                history.append({"role": "user", "content": user_text, "ts": ts})
                history.append({"role": "assistant", "content": reply, "ts": ts})
                save_memory(history)
                await _tg_send(bot, JARVIS_CHAT_ID, reply)
        except TelegramError as exc:
            print(f'[Jarvis] Ошибка Telegram: {exc}')
        except Exception as exc:
            print(f'[Jarvis] Неожиданная ошибка: {exc}')
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

    WD = (0,1,2,3,4)  # пн-пт
    tasks = [
        ('08:00', None, make_good_morning),
        ('10:00', WD,   make_call_reminder),
        ('11:00', None, make_motivation),
        ('12:00', WD,   make_lead_digest),
        ('13:00', None, make_lunch_tip),
        ('14:30', None, make_alive_message),
        ('15:00', WD,   make_no_response_reminder),
        ('20:30', None, make_alive_message),
        ('16:00', None, make_energy_boost),
        ('17:00', None, make_day_summary),
        ('17:30', 4,    make_weekly_report),
        ('19:00', None, make_evening_summary),
    ]
    for schedule_time, day_filter, func in tasks:
        key = f"{schedule_time}:{day_filter}"
        if current == schedule_time and (day_filter is None or day_filter == weekday or (isinstance(day_filter, tuple) and weekday in day_filter)):
            last_run = LAST_JARVIS_RUN.get(key)
            if last_run == now.date():
                continue
            try:
                func()
                LAST_JARVIS_RUN[key] = now.date()
            except Exception as exc:
                send_jarvis_message(f"Jarvis failed {schedule_time}: {exc}")


if __name__ == '__main__':
    import threading as _threading
    def _scheduler_loop():
        while True:
            try:
                check_moscow_jarvis_tasks()
            except Exception as _e:
                print(f'[sched] error: {_e}')
            time.sleep(60)
    _t = _threading.Thread(target=_scheduler_loop, daemon=True)
    _t.start()
    asyncio.run(poll_jarvis())


def safe_claude_call_cascade(messages, system='', max_tokens=1000):
    """Public API unchanged. Internally uses ST8ModelRouter (Haiku→Sonnet cascade,
    LRU cache, prompt caching, cost logging)."""
    return _router.call(messages, system=system, max_tokens=max_tokens)



