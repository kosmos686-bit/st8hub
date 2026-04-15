# -*- coding: utf-8 -*-
import ctypes as _ctypes
import sys as _sys

# ── Защита от дублей: только один scheduler одновременно ─────────────────────
_SCHED_MUTEX = _ctypes.windll.kernel32.CreateMutexW(None, True, "Global\\ST8AI_Scheduler")  # held for process lifetime
if _ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    print("[Scheduler] Уже запущен другой экземпляр. Выход.")
    _sys.exit(0)
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
import os
import random
import urllib.request
import urllib.parse
import ssl
from dotenv import load_dotenv
import schedule
import time
import re
import json
import smtplib
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import anthropic
from tavily import TavilyClient
from telegram import Bot
import threading
from jarvis import check_moscow_jarvis_tasks, run_polling

# Загрузка переменных окружения из .env (перезапись существующих значений)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

# Импорт функции из telegram_leads.py
from telegram_leads import send_lead_card

# Tavily API ключ
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
if not TAVILY_API_KEY:
    raise RuntimeError('TAVILY_API_KEY must be set in environment variables')
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Anthropic Claude API ключ
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise RuntimeError('ANTHROPIC_API_KEY must be set in environment variables')
claude_client = anthropic.Client(api_key=ANTHROPIC_API_KEY)
CLAUDE_MODEL = 'claude-sonnet-4-20250514'

# Gmail SMTP credentials (optional)
GMAIL_USERNAME = os.getenv('GMAIL_USERNAME')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')
GMAIL_RECIPIENT = os.getenv('GMAIL_RECIPIENT', 'Juliapopova2023@gmail.com')
GMAIL_SMTP_SERVER = 'smtp.gmail.com'
GMAIL_SMTP_PORT = 587

# GitHub push configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_HUB_REMOTE = os.getenv('GITHUB_HUB_REMOTE', 'https://github.com/kosmos686-bit/st8hub.git')

# 2GIS API
DGIS_API_KEY = os.getenv('DGIS_API_KEY')

BEST_PROMPTS_PATH = os.path.join(os.path.dirname(__file__), 'best_prompts.md')
HUB_LEADS_PATH = os.path.join(os.path.dirname(__file__), 'st8hub', 'leads.json')
STRICT_NETWORK_WORDS = [
    'сеть', 'холдинг', 'группа', 'chain', 'group', 'network', 'branch', 'branches', 'региональная сеть',
    'транспортная', 'логистическая', 'перевозки', 'доставка', 'складской', 'групп компаний',
    'группа компаний', 'торговая сеть', 'розничная сеть', 'производственный', 'промышленный'
]
STRICT_EXCLUDE_TERMS = [
    'aggregator', 'directory', 'list', 'rating', 'article', 'forum', 'blog', 'review', 'best', 'top', 'рейтинг', 'обзор', 'форум', 'список', 'каталог',
    'companies in', 'members', 'services in', 'shipping',
    'dubai', 'nyc', 'new york', 'london', 'usa', '.uk', 'australia',
    'rusprofile', 'audit-it', 'rbc.ru', 'executive.ru', 'restoclub', 'kommersant', 'dkvartal',
    'instagram.com', 'facebook.com', 'x.com', 'twitter.com', 'vk.com', 'youtube.com',
    'banket365', 'restoran.ru', 'tomesto.ru', 'cataloxy',
    'checko', 'checko.ru', 'list-org', 'list-org.com', 'spark-interfax', 'реабиз', 'компаниум', 'зачестныйбизнес', 'vspravke', 'synapsenet',
    'главные', 'открытия', 'интервью', 'богатые', 'рейтинг ресторан', 'о ресторане', 'гастрооткрыт',
    'склад временного хранения', 'гостиница', 'кто самые', 'история', 'легендарных', 'авторских',
    'лучшие места', 'подборка', 'читайте', 'смотрите'
]
STRICT_DIRECTOR_WORDS = [
    'директор', 'владелец', 'owner', 'ceo', 'founder', 'генеральный', 'управляющий', 'executive', 'chief'
]
STRICT_SEGMENTS = {
    'horeca': ['рестора', 'кафе', 'бар', 'ресторан', 'food', 'restaurant', 'cafe', 'bar'],
    'retail': ['магазин', 'супермаркет', 'ритеил', 'retail', 'shop', 'store'],
    'production': ['завод', 'фабрика', 'производство', 'manufacturing', 'factory'],
    'logistics': ['склад', 'доставка', 'logistics', 'warehouse', 'logistic']
}

ГОРОДА = [
    "Москва", "Санкт-Петербург", "Екатеринбург", "Новосибирск", "Казань",
    "Краснодар", "Нижний Новгород", "Челябинск", "Уфа", "Самара",
    "Ростов-на-Дону", "Пермь", "Воронеж", "Волгоград", "Красноярск"
]

ЗАПРОСЫ_HORECA = [
    "ресторанный холдинг сеть ресторанов {город} официальный сайт директор",
    "сеть кафе {город} владелец контакты официальный сайт",
    "ресторанная группа {город} руководство официальный сайт",
    "кофейня сеть {город} директор контакты телефон",
    "сеть баров ресторанов {город} владелец сайт контакты",
]

ЗАПРОСЫ_RETAIL = [
    "торговая сеть {город} генеральный директор официальный сайт",
    "розничная сеть магазинов {город} владелец контакты",
    "сеть супермаркетов {город} директор официальный сайт",
    "торговый холдинг {город} руководство сайт контакты",
    "сеть магазинов продукты {город} директор телефон",
]

ЗАПРОСЫ_PRODUCTION = [
    "производственный холдинг {город} директор официальный сайт",
    "завод фабрика {город} генеральный директор контакты",
    "производственная компания {город} руководство сайт",
    "пищевое производство {город} директор контакты телефон",
    "промышленный холдинг {город} владелец официальный сайт",
]

ЗАПРОСЫ_LOGISTICS = [
    "транспортный холдинг {город} генеральный директор сайт",
    "логистическая группа компаний {город} директор контакты",
    "транспортно-логистическая компания {город} владелец сайт",
    "грузоперевозки холдинг {город} директор официальный сайт",
    "складской комплекс группа {город} руководство контакты",
]

ШАБЛОНЫ_ПО_СЕГМЕНТУ = {
    "horeca": ЗАПРОСЫ_HORECA,
    "retail": ЗАПРОСЫ_RETAIL,
    "production": ЗАПРОСЫ_PRODUCTION,
    "logistics": ЗАПРОСЫ_LOGISTICS,
    "all": ЗАПРОСЫ_HORECA + ЗАПРОСЫ_RETAIL + ЗАПРОСЫ_PRODUCTION + ЗАПРОСЫ_LOGISTICS,
}

def send_lead_email(lead):
    if not GMAIL_USERNAME or not GMAIL_PASSWORD:
        print(f"Email credentials not set, skipping email for {lead['company_name']}")
        return
    body = build_lead_card_text(lead)
    msg = EmailMessage()
    msg['Subject'] = f"🔥 Новый лид ST8-AI — {lead['company_name']}"
    msg['From'] = GMAIL_USERNAME
    msg['To'] = GMAIL_RECIPIENT
    msg.set_content(body)

    with smtplib.SMTP(GMAIL_SMTP_SERVER, GMAIL_SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(GMAIL_USERNAME, GMAIL_PASSWORD)
        smtp.send_message(msg)

# Bot token and chat IDs
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise RuntimeError('BOT_TOKEN must be set in environment variables')
CHAT_IDS = ['6152243830', '5438530925']

def generate_pain_and_touch(company_name, category):
    """
    Генерирует боль и два варианта первого касания на основе категории.
    Стиль: уверенно, без воды, опытный B2B продавец.
    """
    if category == "horeca":
        pain = "В сетях ресторанов рост масштаба убивает маржинальность: фрагментированная аналитика не показывает реальные LTV, слабая персонализация теряет гостей, а ручная CRM съедает бюджеты на маркетинг."
        touch_a = f"В {company_name} рост сети уже начал давить на маржу? Фрагментированная аналитика скрывает реальные LTV, а слабая персонализация теряет гостей. Мы внедряем AI-платформу, которая объединяет данные и автоматизирует retention — окупаемость от 3 месяцев. Готовы обсудить пилот?"
        touch_b = f"Когда {company_name} масштабируется, операционная аналитика становится хаосом, персонализация — мифом, а LTV падает. Наша система ST8-AI решает это: единая платформа для данных, AI-скоринга гостей и автоматических кампаний. Есть 10 минут на быстрый разбор вашей ситуации?"
    elif category == "retail":
        pain = "В ритейл-сетях персонализация — пустой звук: длинные циклы кампаний, слабая связь CRM с оффлайн-продажами, а рост ассортимента только увеличивает потери на неликвидах."
        touch_a = f"{company_name}, ваши кампании тянутся месяцами без эффекта? Персонализация не работает из-за разрыва онлайн-оффлайн, а CRM не видит реальных покупателей. ST8-AI интегрирует данные, предсказывает спрос и автоматизирует офферы — рост конверсии на 20-30%. Хотите пример из похожей сети?"
        touch_b = f"В {company_name} рост сети убивает эффективность: персонализация не персонализирована, кампании — бесконечны, а CRM не связана с реальными продажами. Наша AI-платформа объединяет все каналы, прогнозирует спрос и запускает умные акции. Давайте посмотрим, сколько вы теряете сейчас?"
    elif category == "production":
        pain = "В производстве непредсказуемый спрос ломает планирование: простои линий, потери на сырье, а контроль качества — ручной ад без прозрачности цепочки."
        touch_a = f"{company_name}, спрос непредсказуем, линии простаивают, а качество — лотерея? Мы внедряем AI для прогноза, оптимизации производства и автоматического контроля — снижение потерь на 15-20%. Готовы к пилоту на одной линии?"
        touch_b = f"Когда {company_name} растет, планирование становится хаосом: непредсказуемый спрос, простои, потери на сырье. ST8-AI дает точный прогноз, оптимизацию цепочки и AI-контроль качества. Сколько вы теряете на простоях ежемесячно?"
    elif category == "logistics":
        pain = "В логистике неэффективные маршруты и слабый прогноз нагрузки убивают маржу: last-mile — bottleneck, склады — переполнены, а KPI — ручной подсчет."
        touch_a = f"{company_name}, маршруты неоптимальны, last-mile тормозит, а прогноз нагрузки — угадывание? AI-оптимизация маршрутов и складов снижает costs на 20%, автоматизирует KPI. Есть кейс из ритейла — обсудим?"
        touch_b = f"В {company_name} логистика — слабое звено: неэффективные маршруты, слабый прогноз, last-mile съедает бюджет. Наша платформа оптимизирует все: AI-маршруты, прогноз спроса, автоматизация. Сколько стоит ваш текущий хаос?"
    else:
        pain = "Общие операционные сложности: фрагментированные данные, ручные процессы, потеря эффективности при росте."
        touch_a = f"{company_name}, рост бизнеса принес хаос в данные и процессы? Мы автоматизируем операции AI, объединяем системы и повышаем эффективность. Окупаемость от 3 месяцев. Готовы к быстрому аудиту?"
        touch_b = f"В {company_name} данные разрознены, процессы ручные, эффективность падает. ST8-AI — единая платформа для AI-автоматизации и оптимизации. Давайте разберем вашу ситуацию за 15 минут?"
    return pain, [touch_a, touch_b]


def generate_claude_outreach(company_name, contact, category, site, email, linkedin, telegram_profile, phone):
    """Генерирует персональные тексты касания через Claude API."""
    segment_map = {
        "horeca": "HoReCa",
        "retail": "Ритейл",
        "production": "Производство",
        "logistics": "Логистика",
        "all": "Разные"
    }
    segment = segment_map.get(category, "Разные")
    meta = {
        "company": company_name,
        "contact": contact,
        "segment": segment,
        "site": site,
        "email": email or "не найден",
        "linkedin": linkedin or "не найден",
        "telegram_profile": telegram_profile or "не найден",
        "phone": phone or "не найден"
    }
    prompt = f"""
Ты — опытный B2B продавец ST8-AI. Изучи профиль компании и сформулируй главное pain в её сегменте. Напиши два текста касания: один для Telegram, другой для Мессенджера Макс. Каждый текст должен быть 3-4 предложения, начинаться с конкретной боли клиента и заканчиваться одним вопросом. Стиль — уверенный, без воды, как опытный продавец, который знает боль клиента изнутри.

Профиль компании:
Компания: {meta['company']}
ЛПР: {meta['contact']}
Сегмент: {meta['segment']}
Сайт: {meta['site']}
Email: {meta['email']}
LinkedIn: {meta['linkedin']}
Telegram/соцсети: {meta['telegram_profile']}
Телефон: {meta['phone']}

Выходной формат: JSON с полями telegram_text и max_text.
"""
    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        try:
            parsed = json.loads(text)
            return parsed.get('telegram_text'), parsed.get('max_text')
        except json.JSONDecodeError:
            telegram_text = None
            max_text = None
            match = re.search(r'"telegram_text"\s*:\s*"([^"]+)"', text)
            if match:
                telegram_text = match.group(1)
            match = re.search(r'"max_text"\s*:\s*"([^"]+)"', text)
            if match:
                max_text = match.group(1)
            return telegram_text, max_text
    except Exception as exc:
        print(f"Claude generation failed: {exc}")
        return None, None


def search_2gis_contacts(company_name):
    """
    Ищет контакты компании через 2GIS Catalog API.
    Возвращает dict с ключами: phone, site, address, org_name.
    """
    if not DGIS_API_KEY:
        return {}
    try:
        params = urllib.parse.urlencode({
            'q': company_name,
            'type': 'branch',
            'fields': 'items.point,items.address,items.contact_groups,items.org',
            'key': DGIS_API_KEY,
        })
        url = f"https://catalog.api.2gis.com/3.0/items?{params}"
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        items = data.get('result', {}).get('items', [])
        if not items:
            return {}
        item = items[0]
        result = {}
        # Название организации
        result['org_name'] = item.get('org', {}).get('name')
        # Адрес
        result['address'] = item.get('address', {}).get('name')
        # Телефон и сайт из contact_groups
        for group in item.get('contact_groups', []):
            for c in group.get('contacts', []):
                ctype = c.get('type', '')
                value = c.get('value', '')
                if ctype == 'phone' and not result.get('phone'):
                    result['phone'] = value
                elif ctype == 'website' and not result.get('site'):
                    result['site'] = value
        print(f"[2GIS] {company_name!r} → {result}")
        return result
    except Exception as exc:
        print(f"[2GIS] Ошибка для {company_name!r}: {exc}")
        return {}


def search_leads(category, num_leads=20):
    """
    Ищет лиды с помощью Tavily.
    """
    # Ротация: 1 случайный город × 1 случайный шаблон (экономия Tavily-кредитов)
    templates = ШАБЛОНЫ_ПО_СЕГМЕНТУ.get(category, ШАБЛОНЫ_ПО_СЕГМЕНТУ["all"])
    города_выборка = random.sample(ГОРОДА, 1)
    category_queries = [
        random.choice(templates).format(город=город)
        for город in города_выборка
    ]
    print(f"[search_leads:{category}] Запросы: {category_queries}")
    raw_results = []
    for query in category_queries:
        try:
            response = tavily_client.search(query=query, max_results=num_leads)
        except Exception as exc:
            print(f"[search_leads:{category}] Tavily ошибка '{query}': {exc}")
            continue
        batch = response.get('results', [])
        print(f"[search_leads:{category}] '{query}' — Tavily вернул {len(batch)} результатов")
        raw_results.extend(batch)
    print(f"[search_leads:{category}] Итого сырых результатов: {len(raw_results)}")
    leads = []
    seen_company_keywords = set()
    for result in raw_results:
        if not is_strict_icp(result):
            continue
        title = result.get('title', '')
        url = result.get('url', '')
        content = result.get('content', '')

        # Пропускаем служебные страницы
        _skip_titles = {'контакты', 'руководство', 'о компании', 'contacts', 'about'}
        if title.strip().lower() in _skip_titles:
            print(f"[search_leads:{category}] ПРОПУСК служебного title: {title!r}")
            continue

        # Извлечение названия компании из title
        def _extract_company_name(title, content):
            t = title.strip()
            # Если начинается с ООО/ПАО/АО/ЗАО/ИП — оставить как есть
            if re.match(r'^(ООО|ПАО|АО|ЗАО|ИП)\s', t):
                name = t
            # Если есть «название» в кавычках — брать его
            elif re.search(r'[«"][^»"]{3,50}[»"]', t):
                m = re.search(r'[«"]([^»"]{3,50})[»"]', t)
                name = m.group(1).strip() if m else t
            # Если содержит двоеточие — брать текст после двоеточия
            elif ':' in t:
                name = t.split(':', 1)[1].strip()
            # Если title = два слова с заглавной (имя человека) — искать org в content
            elif re.match(r'^[А-ЯЁA-Z][а-яёa-z]+ [А-ЯЁA-Z][а-яёa-z]+$', t):
                org_match = re.search(
                    r'(ООО|ПАО|АО|ЗАО|ИП)\s+[«"]?([А-ЯЁA-Zа-яёa-z0-9\s\-]+)[»"]?',
                    content
                )
                name = org_match.group(0).strip() if org_match else t
            # Тире с пробелами " — " — брать часть ДО тире
            elif ' — ' in t:
                name = t.split(' — ', 1)[0].strip()
            # Символ | — брать часть ДО него
            elif '|' in t:
                name = t.split('|', 1)[0].strip()
            # Стандартно — до первого ' - '
            elif ' - ' in t:
                name = t.split(' - ')[0].strip()
            else:
                name = t
            # Убираем ИНН, КПП, ОГРН и всё после
            name = re.sub(r',?\s*(ИНН|КПП|ОГРН)\b.*', '', name).strip()
            name = re.split(r'\s+(?:ИНН|КПП|ОГРН)\s*\d', name)[0].strip()
            # Убираем города в конце: ", Москва", ", Казань" и т.д.
            name = re.sub(r',\s*(Москва|Санкт-Петербург|Екатеринбург|Новосибирск|Казань|Краснодар|Нижний Новгород|Челябинск|Уфа|Самара|Ростов-на-Дону|Пермь|Воронеж|Волгоград|Красноярск)$', '', name).strip()
            # Обрезаем до первой точки или тире если длиннее 60 символов
            if len(name) > 60:
                m = re.search(r'[.\-–—]', name[20:])
                if m:
                    name = name[:20 + m.start()].strip()
                else:
                    name = name[:60].strip()
            return name

        company_name = _extract_company_name(title, content)
        # Дедупликация: берём первые два значимых слова как ключ
        name_key = ' '.join(company_name.lower().split()[:2])
        if name_key in seen_company_keywords:
            print(f"[search_leads:{category}] ДУБЛЬ пропущен: {company_name!r}")
            continue
        seen_company_keywords.add(name_key)
        # Извлечение ЛПР из content Tavily
        contact = None
        lpr_match = re.search(
            r'([А-ЯЁ][а-яё]+(?:\s[А-ЯЁ][а-яё]+){1,2})'
            r'[,\s]+(?:генеральный директор|директор|владелец|основатель|президент|ceo|founder|owner)',
            content, re.IGNORECASE
        )
        if lpr_match:
            contact = lpr_match.group(0).strip()
        if not contact:
            contact = "Директор / Владелец"

        email = None
        linkedin = None
        telegram_profile = None
        phone = None
        site = url

        # Поиск контактов через 2GIS API
        _dgis_irrelevant = [
            'ателье', 'телеателье', 'салон', 'парикмахер', 'стоматолог', 'аптека',
            'магазин', 'кафе', 'ресторан', 'пиццерия', 'суши', 'шаурма', 'цветы',
            'школа', 'детский', 'клиника', 'медцентр', 'фитнес', 'спортзал',
        ]
        dgis = search_2gis_contacts(company_name)
        dgis_org = (dgis.get('org_name') or '').lower()
        # Проверка 1: нет нерелевантных слов
        _dgis_ok = not any(w in dgis_org for w in _dgis_irrelevant)
        # Проверка 2: хотя бы одно слово из названия компании есть в org_name
        if _dgis_ok and dgis_org:
            company_words = [w.lower() for w in company_name.split() if len(w) > 3]
            _dgis_ok = any(w in dgis_org for w in company_words) if company_words else True
        if _dgis_ok:
            if dgis.get('phone'):
                phone = dgis['phone']
            if dgis.get('site'):
                site = dgis['site']
            if dgis.get('org_name') and dgis['org_name'] != company_name:
                company_name = dgis['org_name']
        else:
            print(f"[2GIS] Нерелевантный результат ({dgis.get('org_name')!r}), используем Tavily")

        contact_queries = [
            f"2gis {company_name} телефон адрес директор",
            f"яндекс карты {company_name} контакты",
            f"{company_name} официальный сайт email генеральный директор",
        ]
        for cq in contact_queries:
            try:
                cr = tavily_client.search(query=cq, max_results=3)
            except Exception as exc:
                print(f"[search_leads] Ошибка контактного поиска: {exc}")
                continue
            for res in cr.get('results', []):
                res_url = res.get('url', '')
                cont_raw = res.get('content', '')

                # Сайт: первый .ru домен не из агрегаторов
                if not site or site == url:
                    domain = res_url.split('/')[2] if '//' in res_url else ''
                    if domain.endswith('.ru') and not any(
                        x in domain for x in ('rusprofile', 'audit-it', '2gis', 'yandex')
                    ):
                        site = f"https://{domain}"

                # Телефон
                if not phone:
                    phones = re.findall(
                        r'\+7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',
                        cont_raw
                    )
                    phone = phones[0] if phones else None

                # Email
                if not email:
                    emails = re.findall(
                        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                        cont_raw
                    )
                    ru_emails = [e for e in emails if e.endswith('.ru')]
                    email = ru_emails[0] if ru_emails else (emails[0] if emails else None)

                # ЛПР — только ФИО (2 или 3 русских слова с заглавной) рядом с должностью
                if contact == "Директор / Владелец":
                    _fio2 = r'([А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+)'
                    _fio3 = r'([А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+)'
                    _pos = r'(?:генеральн\w*\s+директор\w*|директор\w*|владелец|основател\w*|управляющ\w*|президент)'
                    for pat in [_fio3 + r'[\s,\-–]+' + _pos, _pos + r'[\s,\-–]+' + _fio3,
                                _fio2 + r'[\s,\-–]+' + _pos, _pos + r'[\s,\-–]+' + _fio2]:
                        lpr = re.search(pat, cont_raw, re.IGNORECASE)
                        if lpr:
                            candidate = lpr.group(1).strip()
                            words = candidate.split()
                            if 2 <= len(words) <= 3 and all(2 <= len(w) <= 15 and w[0].isupper() for w in words):
                                contact = candidate
                                print(f"[search_leads] ЛПР найден: {contact!r} для {company_name!r}")
                                break

                # Telegram / LinkedIn
                if not telegram_profile and 't.me/' in res_url:
                    telegram_profile = res_url
                elif not linkedin and 'linkedin.com' in res_url:
                    linkedin = res_url

        # Подставляем "требует уточнения" если не найдено
        phone = phone or "требует уточнения"
        email = email or "требует уточнения"

        # Исправление мусорных значений ЛПР
        _lpr_junk_words = ('работа', 'компании', 'вакансии', 'вакансия', 'сотрудник')
        _lpr_lower = contact.lower()
        _lpr_is_junk = (
            any(w in _lpr_lower for w in _lpr_junk_words)
            or (_lpr_lower.startswith('генеральный') and len(contact.split()) <= 2)
        )
        if _lpr_is_junk:
            contact = "Директор / Владелец"

        pain, _ = generate_pain_and_touch(company_name, category)
        telegram_touch, max_touch = generate_claude_outreach(
            company_name=company_name,
            contact=contact,
            category=category,
            site=site,
            email=email,
            linkedin=linkedin,
            telegram_profile=telegram_profile,
            phone=phone
        )
        if not telegram_touch or not max_touch:
            default_pain, touches = generate_pain_and_touch(company_name, category)
            telegram_touch, max_touch = touches[0], touches[1]
            pain = default_pain

        segment_map = {
            "horeca": "HoReCa",
            "retail": "Ритейл",
            "production": "Производство",
            "logistics": "Логистика",
            "all": "Разные"
        }
        segment = segment_map.get(category, "Разные")

        # Финальный фильтр названия компании
        _name_reject = False
        _name_lower = company_name.lower()
        _name_junk_words = (
            'вакансии', 'вакансия', 'партнеры инвестируют', 'инвестируют',
            'сервисный центр', 'ресторатор', 'предприниматель', 'основатель',
        )
        _name_junk_starts = ('о компании', 'свежие', 'работа', 'ресторатор')
        if any(w in _name_lower for w in _name_junk_words):
            _name_reject = True
        elif any(_name_lower.startswith(s) for s in _name_junk_starts):
            _name_reject = True
        elif company_name.endswith('...'):
            _name_reject = True
        elif len(company_name) > 60:
            _name_reject = True
        elif re.match(r'^[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z][а-яёa-z]+$', company_name.strip()):
            _name_reject = True  # ФИО (три слова с заглавной)
        if _name_reject:
            print(f"[search_leads:{category}] ОТКЛОНЁН по имени компании: {company_name!r}")
            continue

        score = score_lead(company_name, segment, phone, contact)
        leads.append({
            "company_name": company_name,
            "lpr": contact,
            "phone": phone,
            "email": email,
            "telegram_social": telegram_profile or linkedin,
            "site": site,
            "segment": segment,
            "telegram_touch": telegram_touch,
            "max_touch": max_touch,
            "pain": pain,
            "score": score,
            "response": "новый",
            "created_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        })
    print(f"[search_leads:{category}] Прошло фильтр: {len(leads)} из {len(raw_results)}")
    return leads[:num_leads]


_JUNK_EXACT_TITLES = {
    'о ресторане', 'контакты', 'о компании', 'руководство',
    'главная', 'о нас', 'новости', 'блог', 'главная страница', 'меню',
}
_JUNK_TITLE_START_WORDS = (
    'как', 'что', 'где', 'кто', 'почему', 'когда', 'зачем',
    'главные', 'лучшие', 'топ', 'создай', 'найди', 'открой', 'узнай',
)


def is_strict_icp(result):
    title = result.get('title', '') or ''
    content = result.get('content', '') or ''
    url = result.get('url', '') or ''
    text = ' '.join([title, content, url]).lower()
    title_lower = title.strip().lower()

    if not url:
        print(f"[is_strict_icp] ОТКЛОНЁН (нет url): {title!r}")
        return False

    matched_exclude = [term for term in STRICT_EXCLUDE_TERMS if term in text]
    if matched_exclude:
        print(f"[is_strict_icp] ОТКЛОНЁН (стоп-слова {matched_exclude}): {title!r}")
        return False

    if not any(word in text for word in STRICT_NETWORK_WORDS):
        print(f"[is_strict_icp] ОТКЛОНЁН (нет сетевых слов): {title!r}")
        return False

    # Мусорные точные названия
    if title_lower in _JUNK_EXACT_TITLES:
        print(f"[is_strict_icp] ОТКЛОНЁН (служебный title): {title!r}")
        return False

    # Слишком короткое или слишком длинное название (статья)
    if len(title.strip()) < 4:
        print(f"[is_strict_icp] ОТКЛОНЁН (title слишком короткий): {title!r}")
        return False
    if len(title.strip()) > 80:
        print(f"[is_strict_icp] ОТКЛОНЁН (title слишком длинный — статья): {title!r}")
        return False

    # Title начинается с года
    if re.match(r'^(202[3-9]|2030)', title.strip()):
        print(f"[is_strict_icp] ОТКЛОНЁН (начинается с года): {title!r}")
        return False

    # Title начинается с вопросительного/мусорного слова
    first_word = title_lower.split()[0] if title_lower.split() else ''
    if first_word in _JUNK_TITLE_START_WORDS:
        print(f"[is_strict_icp] ОТКЛОНЁН (мусорное начало заголовка): {title!r}")
        return False

    list_markers = ['десятка', 'топ', 'самых', 'влиятельных']
    if any(marker in title_lower for marker in list_markers):
        print(f"[is_strict_icp] ОТКЛОНЁН (рейтинговый заголовок): {title!r}")
        return False

    if re.match(r'^[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+(\s[А-ЯЁ][а-яё]+)?$', title.strip()):
        print(f"[is_strict_icp] ОТКЛОНЁН (имя человека в заголовке): {title!r}")
        return False

    person_markers = [' - федерация', 'ресторановед', 'folk team — о том']
    if any(marker in title_lower for marker in person_markers):
        print(f"[is_strict_icp] ОТКЛОНЁН (маркер персоны/блога): {title!r}")
        return False

    junk_title_markers = ['@', ' • ', '| instagram', '| vk', '| facebook', '| twitter', '| x.com',
                          'владелец «', 'собственник «', 'запустит сеть', 'откроет сеть']
    if any(marker in title_lower for marker in junk_title_markers):
        print(f"[is_strict_icp] ОТКЛОНЁН (мусорный заголовок): {title!r}")
        return False

    print(f"[is_strict_icp] ПРИНЯТ: {title!r}")
    return True


def load_hub_leads():
    if not os.path.exists(os.path.dirname(HUB_LEADS_PATH)):
        os.makedirs(os.path.dirname(HUB_LEADS_PATH), exist_ok=True)
    if not os.path.exists(HUB_LEADS_PATH):
        return []
    with open(HUB_LEADS_PATH, 'r', encoding='utf-8') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []


def save_hub_leads(leads):
    if not os.path.exists(os.path.dirname(HUB_LEADS_PATH)):
        os.makedirs(os.path.dirname(HUB_LEADS_PATH), exist_ok=True)
    with open(HUB_LEADS_PATH, 'w', encoding='utf-8') as file:
        json.dump(leads, file, ensure_ascii=False, indent=2)


def add_lead_to_hub(lead):
    leads = load_hub_leads()
    for existing in leads:
        if existing.get('company_name') == lead['company_name'] and existing.get('lpr') == lead['lpr']:
            return False
    lead_copy = dict(lead)
    lead_copy['response'] = 'новый'
    lead_copy['created_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    leads.insert(0, lead_copy)
    save_hub_leads(leads)
    return True


def update_hub_lead_response(company_name, response):
    leads = load_hub_leads()
    changed = False
    for lead in leads:
        if lead.get('company_name') == company_name:
            lead['response'] = response
            changed = True
    if changed:
        save_hub_leads(leads)
        git_push_hub(f"Update lead response: {company_name} -> {response}")
    return changed


def git_push_hub(message):
    hub_path = os.path.join(os.path.dirname(__file__), 'st8hub')
    if not os.path.exists(hub_path):
        return
    try:
        status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=hub_path, text=True).strip()
        if not status:
            return
        remote_url = GITHUB_HUB_REMOTE
        if GITHUB_TOKEN and '@' not in remote_url:
            remote_url = remote_url.replace('https://', f'https://{GITHUB_TOKEN}@')
        subprocess.run(['git', 'add', 'leads.json'], cwd=hub_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['git', 'commit', '-m', message], cwd=hub_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['git', 'push', remote_url, 'main'], cwd=hub_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as exc:
        print(f"Git push failed: {exc}")


def weekly_claude_training():
    leads = load_hub_leads()
    successful = [lead for lead in leads if lead.get('response') == 'ответил']
    prompt_header = '# Best prompts for ST8-AI\n\n'
    if not successful:
        content = prompt_header + 'Пока нет достаточно успешных лидов для обучения. Будем собирать данные и анализировать в следующем отчёте.'
        with open(BEST_PROMPTS_PATH, 'w', encoding='utf-8') as file:
            file.write(content)
        return
    summary = '\n'.join([f"- {lead.get('company_name')} — {lead.get('telegram_touch','').replace(chr(10),' ')}" for lead in successful[:5]])
    analysis_prompt = f"Анализируй успешные лиды ST8-AI. Вот 5 лидов, которые ответили:\n{summary}\n\nЧто общего у этих успешных текстов касаний? Сформируй 3 улучшенных шаблона prompt для генерации новых текстов касаний в формате JSON с ключами prompt1, prompt2, prompt3."
    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=350,
            messages=[{"role": "user", "content": analysis_prompt}]
        )
        result_text = response.content[0].text.strip()
    except Exception as exc:
        result_text = f"Ошибка анализа Claude: {exc}"
    with open(BEST_PROMPTS_PATH, 'w', encoding='utf-8') as file:
        file.write(prompt_header + result_text)


def score_lead(company_name, segment, phone, lpr):
    """Вызывает Claude для оценки лида по шкале 1-10. Возвращает int."""
    prompt = (
        f"Оцени лида для B2B продаж ST8-AI по шкале 1-10. "
        f"Критерии: наличие телефона (+2), наличие email (+1), размер компании (сеть 5+ точек +3), "
        f"сегмент (HoReCa +2, ритейл +1), наличие ЛПР (+2). "
        f"Компания: {company_name}, сегмент: {segment}, телефон: {phone}, ЛПР: {lpr}. "
        f"Ответь только цифрой от 1 до 10."
    )
    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=5,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        m = re.search(r'\d+', text)
        score = int(m.group()) if m else 5
        return max(1, min(10, score))
    except Exception as exc:
        print(f"[score_lead] Ошибка: {exc}")
        return 5


def analyze_responses():
    """Анализирует тексты касаний которые получили ответ. Запускать каждую пятницу в 16:00."""
    leads = load_hub_leads()
    successful = [lead for lead in leads if lead.get('response') == 'ответил']
    if not successful:
        send_text_notification("📊 Анализ касаний: пока нет лидов со статусом 'ответил'.")
        return
    touches = '\n'.join([
        f"- {lead.get('company_name')} [{lead.get('segment','')}]: {(lead.get('telegram_touch') or '').replace(chr(10),' ')}"
        for lead in successful[:10]
    ])
    prompt = (
        f"Проанализируй тексты касаний которые получили ответ. Что общего? Какие фразы работают? "
        f"Дай 3 конкретных рекомендации для улучшения. Вот тексты:\n{touches}"
    )
    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.content[0].text.strip()
    except Exception as exc:
        analysis = f"Ошибка анализа: {exc}"
    report_date = datetime.utcnow().strftime('%Y-%m-%d')
    with open(BEST_PROMPTS_PATH, 'w', encoding='utf-8') as f:
        f.write(f"# Best Prompts Analysis {report_date}\n\n{analysis}\n")
    send_text_notification(f"📊 Анализ касаний (пятница):\n\n{analysis[:800]}")


def predict_pipeline():
    """Предиктивный анализ пайплайна. Запускать каждый понедельник в 9:00."""
    leads = load_hub_leads()
    if not leads:
        send_text_notification("📈 Прогноз пайплайна: лидов нет.")
        return
    summary_lines = []
    for lead in leads[:20]:
        score = lead.get('score', '?')
        summary_lines.append(
            f"- {lead.get('company_name')} [{lead.get('segment','')}] ЛПР: {lead.get('lpr','')} "
            f"Статус: {lead.get('response','')} Скор: {score}"
        )
    leads_summary = '\n'.join(summary_lines)
    prompt = (
        f"Проанализируй пайплайн ST8-AI. Вот все лиды со статусами:\n{leads_summary}\n\n"
        f"Определи: 1) Кто скорее всего закроется в сделку на этой неделе и почему "
        f"2) Кто требует срочного follow-up 3) Какой сегмент самый конверсионный. "
        f"Дай конкретные рекомендации."
    )
    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        forecast = response.content[0].text.strip()
    except Exception as exc:
        forecast = f"Ошибка прогноза: {exc}"
    send_text_notification(f"📈 Прогноз пайплайна на неделю:\n\n{forecast[:900]}")


def weekly_report():
    leads = load_hub_leads()
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    weekly = [lead for lead in leads if 'created_at' in lead and datetime.strptime(lead['created_at'], '%Y-%m-%dT%H:%M:%SZ') >= one_week_ago]
    if not weekly:
        weekly = leads
    total = len(weekly)
    if total == 0:
        send_text_notification('Еженедельный отчёт: лиды отсутствуют.')
        return
    answered = len([lead for lead in weekly if lead.get('response') == 'ответил'])
    percent = round(answered / total * 100)
    segment_scores = {}
    for lead in weekly:
        seg = lead.get('segment', 'Неизвестен')
        segment_scores.setdefault(seg, {'count':0,'answered':0})
        segment_scores[seg]['count'] += 1
        if lead.get('response') == 'ответил':
            segment_scores[seg]['answered'] += 1
    best_segment = 'Не определён'
    best_rate = 0
    for seg, stats in segment_scores.items():
        rate = stats['answered'] / stats['count'] if stats['count'] else 0
        if rate > best_rate:
            best_rate = rate
            best_segment = seg
    success_texts = [lead.get('telegram_touch','') for lead in weekly if lead.get('response') == 'ответил'][:3]
    if not success_texts:
        success_texts = ['Нет успешных текстов за неделю.']
    report = f"🔥 Еженедельный отчёт ST8-AI\n\nВсего лидов: {total}\nОтветили: {percent}%\nЛучший сегмент: {best_segment}\n\nТоп-3 текста касаний:\n"
    for i, text in enumerate(success_texts, 1):
        report += f"{i}. {text}\n\n"
    report += "Рекомендация: сфокусируйтесь на лиды сегмента {best_segment} и тестируйте тексты с прямой болевой гипотезой.\n"
    send_text_notification(report)


def get_lead_response_counts():
    leads = load_hub_leads()
    counts = {status: 0 for status in ['новый','написали','ответил','не ответил','отказ']}
    for lead in leads:
        response = lead.get('response', 'новый')
        if response not in counts:
            counts[response] = 0
        counts[response] += 1
    return counts


def ensure_ai_department_dirs():
    os.makedirs(os.path.join(os.path.dirname(__file__), 'kp'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'backups'), exist_ok=True)


def normalize_filename(value):
    sanitized = re.sub(r'[^A-Za-z0-9_-]+', '_', value)
    return sanitized[:80].strip('_') or 'lead'


def save_kp_for_lead(lead):
    ensure_ai_department_dirs()
    filename = f"KP_{normalize_filename(lead['company_name'])}.md"
    path = os.path.join(os.path.dirname(__file__), 'kp', filename)
    content = f"""# КП ST8-AI для {lead['company_name']}

## Контакты
- ЛПР: {lead['lpr']}
- Телефон: {lead['phone'] or 'требует уточнения'}
- Email: {lead['email'] or 'требует уточнения'}
- Telegram/соцсети: {lead['telegram_social'] or 'требует уточнения'}
- Сайт: {lead['site'] or 'требует уточнения'}
- Сегмент: {lead['segment']}

## Боль
{lead['pain']}

## Решение ST8-AI
- Аналитика и централизованная CRM
- AI-персонализация гостей
- Автоматизация retention и промо

## Пакеты
| Пакет | Точки | Цена | Что включает |
|-------|-------|------|-------------|
| Базовый | 1–3 | от 65 000 ₽ | Базовая автоматизация |
| Бизнес | 4–10 | от 165 000 ₽ | Полная AI-платформа + интеграции |
| Сеть | 10+ | от 385 000 ₽ | Кастомное решение + поддержка |

## Условия оплаты
- 50% предоплата
- 30% после milestone
- 20% после приёмки
"""
    with open(path, 'w', encoding='utf-8') as file:
        file.write(content)
    return path


def read_markdown_table(path):
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file if line.strip()]
    if len(lines) < 2:
        return []
    for line in lines[2:]:
        parts = [part.strip() for part in line.split('|')[1:-1]]
        if len(parts) >= 5:
            entries.append({
                'date': parts[0],
                'company': parts[1],
                'lpr': parts[2],
                'status': parts[3],
                'comment': parts[4]
            })
    return entries


def write_markdown_table(path, header, entries):
    with open(path, 'w', encoding='utf-8') as file:
        file.write(header + '\n')
        for entry in entries:
            file.write(f"| {entry['date']} | {entry['company']} | {entry['lpr']} | {entry['status']} | {entry['comment']} |\n")


def update_lead_status(lead, status='новый', comment=''):
    path = os.path.join(os.path.dirname(__file__), 'leads_status.md')
    header = '# Leads Status\n\n| Дата | Компания | ЛПР | Статус | Комментарий |\n|------|---------|-----|--------|-------------|\n'
    entries = read_markdown_table(path)
    found = False
    for entry in entries:
        if entry['company'] == lead['company_name'] and entry['lpr'] == lead['lpr']:
            entry['status'] = status
            entry['comment'] = comment or entry['comment']
            entry['date'] = datetime.utcnow().strftime('%Y-%m-%d')
            found = True
            break
    if not found:
        entries.append({
            'date': datetime.utcnow().strftime('%Y-%m-%d'),
            'company': lead['company_name'],
            'lpr': lead['lpr'],
            'status': status,
            'comment': comment
        })
    write_markdown_table(path, header, entries)


def append_ab_result(lead, winner=None, comment=''): 
    path = os.path.join(os.path.dirname(__file__), 'ab_results.md')
    with open(path, 'a', encoding='utf-8') as file:
        file.write(f"| {datetime.utcnow().strftime('%Y-%m-%d')} | {lead['company_name']} | {lead['lpr']} | A | B | {winner or 'требует уточнения'} | {comment} |\n")


def make_note_file(path, content):
    with open(path, 'w', encoding='utf-8') as file:
        file.write(content)


def generate_cheat_sheet():
    client_path = os.path.join(os.path.dirname(__file__), 'st8-memory-bank', 'clientPipeline.md')
    if not os.path.exists(client_path):
        return
    with open(client_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    now = datetime.utcnow().strftime('%Y-%m-%d')
    note = [f"# Шпаргалка на звонки {now}\n\n"]
    for line in lines:
        if line.startswith('###') or line.startswith('|') or line.startswith('## '):
            note.append(line)
    path = os.path.join(os.path.dirname(__file__), 'kp', f'cheat_sheet_{now}.md')
    make_note_file(path, ''.join(note))
    send_text_notification(f"Чек-лист звонков готов: {path}")


def daily_news_digest():
    now = datetime.utcnow().strftime('%Y-%m-%d')
    prompt = (
        f"Ты аналитик рынка HoReCa и ритейл России. Составь оперативный дайджест: "
        f"3 актуальных тренда или новости рынка (автоматизация, AI, новые игроки, M&A, регуляторика). "
        f"Каждый пункт — 1-2 предложения, конкретно и по делу. Без предисловий. "
        f"Дата отчёта: {now}."
    )
    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        digest = response.content[0].text.strip()
    except Exception as exc:
        digest = f"Ошибка генерации дайджеста: {exc}"
    path = os.path.join(os.path.dirname(__file__), f'daily_digest_{now}.md')
    make_note_file(path, f"# Дайджест новостей {now}\n\n{digest}\n")
    send_text_notification(f"Дайджест готов: {path}\n\n{digest}")


def weekly_analytics_report():
    path = os.path.join(os.path.dirname(__file__), 'leads_status.md')
    entries = read_markdown_table(path)
    counts = {'новый': 0, 'написали': 0, 'ответили': 0, 'в работе': 0, 'отказ': 0}
    for entry in entries:
        if entry['status'] in counts:
            counts[entry['status']] += 1
    report = f"# Еженедельный отчёт {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"
    report += '\n'.join([f"- {status}: {count}" for status, count in counts.items()])
    report += "\n\nРекомендации:\n- Уточнить лиды в статусе 'написали'.\n- Выполнить follow-up через 3 дня.\n"
    report_path = os.path.join(os.path.dirname(__file__), f"weekly_report_{datetime.utcnow().strftime('%Y-%m-%d')}.md")
    make_note_file(report_path, report)
    send_text_notification(f"Еженедельный отчёт готов: {report_path}\n\n{report}")


def weekly_ab_analysis():
    path = os.path.join(os.path.dirname(__file__), 'ab_results.md')
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    summary = 'A/B результаты:\n' + ''.join(lines[-10:])
    report_path = os.path.join(os.path.dirname(__file__), f"ab_analysis_{datetime.utcnow().strftime('%Y-%m-%d')}.md")
    make_note_file(report_path, f"# Анализ A/B результатов\n\n{summary}\n")
    send_text_notification(f"A/B анализ готов: {report_path}")


def generate_outreach_ready():
    path = os.path.join(os.path.dirname(__file__), 'outreach_ready.md')
    content = f"# Outreach Ready {datetime.utcnow().strftime('%Y-%m-%d')}\n\n" + "- Персональные рассылки готовы к запуску.\n"
    make_note_file(path, content)
    send_text_notification(f"Outreach ready подготовлен: {path}")


def backup_memory_bank():
    src = os.path.join(os.path.dirname(__file__), 'st8-memory-bank')
    if not os.path.exists(src):
        return
    dest = os.path.join(os.path.dirname(__file__), 'backups', f"memory-bank_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    shutil.copytree(src, dest)
    send_text_notification(f"Backup memory-bank создан: {dest}")


def auto_update_context():
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    for filename in ['activeContext.md', 'progress.md']:
        path = os.path.join(os.path.dirname(__file__), 'st8-memory-bank', filename)
        if os.path.exists(path):
            with open(path, 'a', encoding='utf-8') as file:
                file.write(f"\n> AUTO UPDATE: {timestamp} by scheduler\n")


def send_text_notification(text):
    async def _send():
        bot = Bot(token=BOT_TOKEN)
        for chat_id in CHAT_IDS:
            for attempt in range(3):
                try:
                    await bot.send_message(chat_id=chat_id, text=text)
                    break
                except Exception as exc:
                    print(f"Ошибка отправки {chat_id} (попытка {attempt+1}/3): {exc}")
                    if attempt < 2:
                        await asyncio.sleep(5)
    asyncio.run(_send())


def send_leads(leads):
    """
    Сохраняет лиды в Hub с приоритизацией по наличию контактов.
    """
    new_leads = 0
    with_contacts = 0
    needs_contact = 0

    for lead in leads:
        has_phone = lead.get('phone') and lead['phone'] != 'требует уточнения'
        has_email = lead.get('email') and lead['email'] != 'требует уточнения'
        status = 'новый' if (has_phone or has_email) else 'требует контакт'

        if add_lead_to_hub(lead):
            new_leads += 1
            if status == 'новый':
                with_contacts += 1
            else:
                needs_contact += 1
            save_kp_for_lead(lead)
            update_lead_status(lead, status=status)
            append_ab_result(lead)
            auto_update_context()
        else:
            print(f"Lead already exists in Hub: {lead['company_name']}")
        try:
            send_lead_email(lead)
        except Exception as exc:
            print(f"Error sending lead email: {exc}")
        time.sleep(1)

    if new_leads > 0:
        git_push_hub(f"Add {new_leads} new leads to Hub")
        send_text_notification(
            f"🔥 +{new_leads} лидов в Hub ({with_contacts} с контактами, {needs_contact} требуют уточнения)"
        )


def send_no_response_reminders():
    path = os.path.join(os.path.dirname(__file__), 'leads_status.md')
    entries = read_markdown_table(path)
    cutoff = datetime.utcnow() - timedelta(days=3)
    for entry in entries:
        if entry['status'] == 'написали':
            try:
                entry_date = datetime.strptime(entry['date'], '%Y-%m-%d')
            except ValueError:
                continue
            if entry_date <= cutoff:
                send_text_notification(f"Напоминание: лид {entry['company']} в статусе 'написали' {entry['date']} не ответил. Нужно follow-up.")


def job_horeca():
    print("Запуск поиска HoReCa лидов...")
    try:
        leads = search_leads("horeca", 20)
        send_leads(leads)
    except Exception as e:
        print(f"[job_horeca] Ошибка (Tavily лимит или сеть): {e}")

def job_retail():
    print("Запуск поиска ритейл лидов...")
    try:
        leads = search_leads("retail", 20)
        send_leads(leads)
    except Exception as e:
        print(f"[job_retail] Ошибка (Tavily лимит или сеть): {e}")

def job_production_logistics():
    print("Запуск поиска производство и логистика лидов...")
    try:
        leads_prod = search_leads("production", 20)
        leads_log = search_leads("logistics", 20)
        send_leads(leads_prod + leads_log)
    except Exception as e:
        print(f"[job_production_logistics] Ошибка (Tavily лимит или сеть): {e}")

def job_all():
    print("Запуск поиска всех направлений (дожим)...")
    try:
        leads = search_leads("all", 20)
        send_leads(leads)
    except Exception as e:
        print(f"[job_all] Ошибка (Tavily лимит или сеть): {e}")


# ── 2GIS map parser job ──────────────────────────────────────────────────────

MAP_PARSER_CITIES = ["москва", "санкт-петербург", "казань", "екатеринбург", "новосибирск"]
MAP_PARSER_CATEGORIES = ["ресторан", "кафе", "отель", "производство", "логистика"]
MAP_PARSER_LEADS_DIR = os.path.join(os.path.dirname(__file__), "leads")
MAP_PARSER_PHONES_SEEN_PATH = os.path.join(os.path.dirname(__file__), "leads", "seen_phones.json")
MAP_PARSER_CHAT_ID = "6152243830"
# City rotation index persisted in memory across calls
_map_parser_city_idx = [0]


def _load_seen_phones():
    os.makedirs(MAP_PARSER_LEADS_DIR, exist_ok=True)
    if not os.path.exists(MAP_PARSER_PHONES_SEEN_PATH):
        return set()
    try:
        with open(MAP_PARSER_PHONES_SEEN_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save_seen_phones(phones: set):
    os.makedirs(MAP_PARSER_LEADS_DIR, exist_ok=True)
    with open(MAP_PARSER_PHONES_SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(phones), f, ensure_ascii=False)


def _send_map_leads_to_telegram(new_leads: list, city: str, category: str):
    if not new_leads:
        return
    lines = [f"📍 2GIS: {city} / {category} — {len(new_leads)} новых лидов\n"]
    for i, lead in enumerate(new_leads[:30], 1):
        name = lead.get("name", "—")
        phone = lead.get("phone") or "—"
        site = lead.get("website") or lead.get("web") or "—"
        lines.append(f"{i}. {name}\n   📞 {phone}\n   🌐 {site}")
    text = "\n".join(lines)

    async def _send():
        bot = Bot(token=BOT_TOKEN)
        # Split if too long (Telegram limit 4096 chars)
        chunk_size = 3800
        for start in range(0, len(text), chunk_size):
            chunk = text[start:start + chunk_size]
            for attempt in range(3):
                try:
                    await bot.send_message(chat_id=MAP_PARSER_CHAT_ID, text=chunk)
                    break
                except Exception as exc:
                    print(f"  Telegram send error (attempt {attempt+1}/3): {exc}")
                    if attempt < 2:
                        await asyncio.sleep(3)

    asyncio.run(_send())


def job_map_parser():
    """Parse 2GIS for 5 cities in rotation, all categories, save JSON, send new leads to Telegram."""
    try:
        from map_parser import search_2gis
    except ImportError as e:
        print(f"map_parser import error: {e}")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(MAP_PARSER_LEADS_DIR, exist_ok=True)
    seen_phones = _load_seen_phones()
    new_phones = set()
    total_new = 0

    # Pick 5 cities starting from current rotation index
    start = _map_parser_city_idx[0] % len(MAP_PARSER_CITIES)
    cities_today = [MAP_PARSER_CITIES[(start + i) % len(MAP_PARSER_CITIES)] for i in range(5)]
    _map_parser_city_idx[0] = (start + 5) % len(MAP_PARSER_CITIES)

    print(f"[map_parser] {today} — cities: {cities_today}")

    for city in cities_today:
        city_leads_all = []

        for category in MAP_PARSER_CATEGORIES:
            try:
                leads = search_2gis(query=category, city=city, limit=20)
            except Exception as e:
                print(f"  [map_parser] error {city}/{category}: {e}")
                leads = []

            # Filter duplicates by phone
            new_leads = []
            for lead in leads:
                phone = lead.phone.strip() if lead.phone else ""
                if not phone:
                    # include leads without phone (deduplicate by name+city)
                    key = f"notel:{lead.name.lower()[:30]}:{city}"
                    if key not in seen_phones and key not in new_phones:
                        new_phones.add(key)
                        new_leads.append(lead.to_dict())
                elif phone not in seen_phones and phone not in new_phones:
                    new_phones.add(phone)
                    new_leads.append(lead.to_dict())

            city_leads_all.extend(new_leads)
            total_new += len(new_leads)

            if new_leads:
                _send_map_leads_to_telegram(new_leads, city, category)

        # Save all leads for this city to JSON
        if city_leads_all:
            city_slug = city.replace(" ", "_").replace("-", "_")
            out_path = os.path.join(MAP_PARSER_LEADS_DIR, f"{today}_{city_slug}.json")
            # Merge with existing file if present
            existing = []
            if os.path.exists(out_path):
                try:
                    with open(out_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                except Exception:
                    existing = []
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(existing + city_leads_all, f, ensure_ascii=False, indent=2)
            print(f"  [map_parser] saved {len(city_leads_all)} leads -> {out_path}")

    # Persist seen phones
    seen_phones.update(new_phones)
    _save_seen_phones(seen_phones)

    # Push all new leads to GitHub Pages ST8 Hub (leads.json)
    if total_new > 0:
        try:
            hub_leads = load_hub_leads()
            existing_phones = {l.get("phone", "") for l in hub_leads}
            added = 0
            for city in cities_today:
                city_slug = city.replace(" ", "_").replace("-", "_")
                out_path = os.path.join(MAP_PARSER_LEADS_DIR, f"{today}_{city_slug}.json")
                if not os.path.exists(out_path):
                    continue
                with open(out_path, "r", encoding="utf-8") as f:
                    file_leads = json.load(f)
                for lead in file_leads:
                    phone = lead.get("phone", "")
                    if phone and phone in existing_phones:
                        continue
                    hub_entry = {
                        "company_name": lead.get("name", ""),
                        "phone": phone,
                        "site": lead.get("website", "") or lead.get("web", ""),
                        "city": lead.get("city", ""),
                        "category": lead.get("category", ""),
                        "date": today,
                        "status": "новый",
                        "source": "2gis",
                        "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                    hub_leads.insert(0, hub_entry)
                    if phone:
                        existing_phones.add(phone)
                    added += 1
            if added > 0:
                save_hub_leads(hub_leads)
                git_push_hub(f"2GIS: +{added} new leads ({today})")
                print(f"  [map_parser] pushed {added} leads to GitHub Hub")
        except Exception as exc:
            print(f"  [map_parser] GitHub push error: {exc}")

    print(f"[map_parser] done. Total new leads today: {total_new}")


def monday_jarvis_brief():
    """Еженедельный брифинг по понедельникам в 08:00 — пайплайн, зависшие сделки, приоритеты недели."""
    leads = load_hub_leads()

    # Зависшие лиды (нет активности > 7 дней)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stalled = []
    for lead in leads:
        created = lead.get('created_at', '')
        last_touch = lead.get('last_touch', created)
        if last_touch:
            try:
                dt = datetime.strptime(last_touch[:19], '%Y-%m-%dT%H:%M:%S')
                if (now - dt).days >= 7 and lead.get('response', '') not in ('закрыт', 'отказ'):
                    stalled.append(lead)
            except Exception:
                pass

    # Топ лиды по скору
    top_leads = sorted(leads, key=lambda x: float(x.get('score', 0) or 0), reverse=True)[:10]
    top_lines = '\n'.join(
        f"- {l.get('company_name','?')} [{l.get('segment','')}] ЛПР: {l.get('lpr','')} "
        f"Статус: {l.get('response','')} Скор: {l.get('score','?')}"
        for l in top_leads
    )

    stalled_lines = '\n'.join(
        f"- {l.get('company_name','?')} [{l.get('segment','')}] ЛПР: {l.get('lpr','')}"
        for l in stalled[:7]
    ) or 'нет зависших'

    # Контекст из памяти (AIRI + клиенты)
    memory_ctx = ''
    base = os.path.dirname(__file__)
    mem_files = [
        os.path.join(base, 'agent_memory', 'airi.md'),
        os.path.join(base, 'agent_memory', 'airi_approaches.md'),
        os.path.join(base, 'st8-memory-bank', 'clientPipeline.md'),
    ]
    parts = []
    for path in mem_files:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                txt = f.read().strip()
            if txt:
                parts.append(txt[:600])
    if parts:
        memory_ctx = '\n\n'.join(parts)

    prompt = (
        f"Сегодня понедельник. Сделай краткий стратегический брифинг для CEO ST8-AI на эту неделю.\n\n"
        f"ТОП ЛИДЫ:\n{top_lines}\n\n"
        f"ЗАВИСШИЕ (>7 дней без активности):\n{stalled_lines}\n\n"
        f"КОНТЕКСТ (AIRI, клиенты):\n{memory_ctx}\n\n"
        f"Дай:\n"
        f"1) Топ-3 приоритета на эту неделю (конкретно: кому написать, что сделать)\n"
        f"2) Зависшие сделки — кого реанимировать первым\n"
        f"3) Стратегический фокус недели (1-2 предложения)\n\n"
        f"Коротко, по делу, без воды. Максимум 300 слов."
    )

    try:
        response = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        brief = response.content[0].text.strip()
    except Exception as exc:
        brief = f"Ошибка генерации брифинга: {exc}"

    stalled_count = len(stalled)
    msg = (
        f"📋 *Понедельник. Брифинг недели*\n\n"
        f"Всего лидов: {len(leads)} | Зависших: {stalled_count}\n\n"
        f"{brief}"
    )
    send_text_notification(msg[:1500])


# Настройка расписания
schedule.every().day.at("08:00").do(daily_news_digest)
schedule.every().day.at("08:30").do(generate_cheat_sheet)
schedule.every().day.at("10:00").do(job_map_parser)
# ЛИДЫ ПРИОСТАНОВЛЕНЫ до 21.04.2026 — раскомментировать для возобновления
# schedule.every().day.at("09:00").do(job_horeca)
# schedule.every().day.at("12:00").do(job_retail)
# schedule.every().day.at("15:00").do(job_production_logistics)
schedule.every().day.at("17:00").do(weekly_analytics_report)
# schedule.every().day.at("18:00").do(job_all)
schedule.every().day.at("09:30").do(send_no_response_reminders)
schedule.every().friday.at("16:00").do(analyze_responses)
schedule.every().friday.at("17:00").do(weekly_analytics_report)
schedule.every().monday.at("08:00").do(monday_jarvis_brief)
schedule.every().monday.at("09:00").do(predict_pipeline)
schedule.every().sunday.at("18:00").do(weekly_ab_analysis)
schedule.every().sunday.at("11:00").do(backup_memory_bank)
schedule.every(1).minutes.do(check_moscow_jarvis_tasks)

if __name__ == "__main__":
    print("Polling управляется через jarvis_watchdog.py")
    print("Scheduler запущен. Ожидание задач...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверка каждую минуту