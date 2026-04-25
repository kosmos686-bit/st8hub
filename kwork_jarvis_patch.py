import asyncio
import os
import re
import sys
import json
import threading
from datetime import datetime
from pathlib import Path

# Добавляем путь к kwork боту
KWORK_BOT_PATH = r"C:\st8_kwork_bot\st8_clean"
if KWORK_BOT_PATH not in sys.path:
    sys.path.insert(0, KWORK_BOT_PATH)

# Глобальное состояние охоты
_kwork_state = {
    "running": False,
    "task": None,
    "projects_found": 0,
    "responses_sent": 0,
    "started_at": None,
}

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ─────────────────────────────────────────────────────────────
#  Переговорщик — отвечает клиентам через Claude API
# ─────────────────────────────────────────────────────────────

PEREGOVSHIK_PROMPT = """Ты ST8-AI Переговорщик на Kwork. Фрилансер-разработчик (Python, боты, парсеры).

ТВОЯ ЗАДАЧА:
- Отвечать на сообщения клиентов естественно и убедительно
- Работать с возражениями по цене
- Уточнять детали ТЗ
- Дожимать до сделки
- Предлагать апселл после выполнения

ПРАВИЛА:
- Пиши кратко (2-4 предложения максимум)
- Не используй шаблонные фразы
- Будь уверен в своей экспертизе
- Если торгуются — уступай не более 15%
- Всегда заканчивай вопросом или CTA

СТИЛЬ: профессионально, дружелюбно, без воды."""


async def _negotiate_with_claude(client_message: str, context: str = "") -> str:
    """Генерирует ответ клиенту через Claude API."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        messages = []
        if context:
            messages.append({"role": "user", "content": f"Контекст проекта: {context}"})
            messages.append({"role": "assistant", "content": "Понял контекст, готов отвечать клиенту."})
        
        messages.append({"role": "user", "content": f"Клиент написал: {client_message}\n\nНапиши ответ:"})
        
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=PEREGOVSHIK_PROMPT,
            messages=messages
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Спасибо за ваше сообщение! Уточните детали — готов приступить."


# ─────────────────────────────────────────────────────────────
#  Kwork охота через Playwright
# ─────────────────────────────────────────────────────────────

async def _kwork_hunt_loop(notify_func, duration_minutes: int = 60):
    """Основной цикл охоты за проектами."""
    global _kwork_state
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        await notify_func("Playwright не установлен. Запусти: pip install playwright && playwright install chromium")
        return
    
    _kwork_state["started_at"] = datetime.now()
    _kwork_state["projects_found"] = 0
    _kwork_state["responses_sent"] = 0
    
    await notify_func(f"Алина запущена! Ищу проекты 5000-50000 руб. Охота {duration_minutes} мин.")
    
    keywords = ["telegram бот", "парсер", "чат бот", "интеграция api", "автоматизация", "скрипт python"]
    seen = set()
    
    end_time = asyncio.get_event_loop().time() + (duration_minutes * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Авторизация
        try:
            kwork_login = os.getenv("KWORK_LOGIN", "jul1apopova23@yandex.ru")
            kwork_pass = os.getenv("KWORK_PASSWORD", "Milana2016!")
            
            await page.goto("https://kwork.ru/login", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            await page.fill('input[name="login"]', kwork_login)
            await page.fill('input[name="password"]', kwork_pass)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=20000)
            await asyncio.sleep(3)
            await notify_func("Алина авторизована на Kwork.")
        except Exception as e:
            await notify_func(f"Ошибка входа в Kwork: {e}")
            await browser.close()
            return
        
        # Основной цикл поиска
        while asyncio.get_event_loop().time() < end_time and _kwork_state["running"]:
            try:
                await page.goto(
                    "https://kwork.ru/projects?c=41&attr=212",
                    wait_until="networkidle",
                    timeout=30000
                )
                await asyncio.sleep(2)
                
                # Парсим проекты
                projects = await page.query_selector_all(".projects-list .project-item, .project-card, .want-card")
                
                found_this_round = 0
                for proj in projects[:15]:
                    try:
                        title_el = await proj.query_selector(".project-title a, a.want-card__title, h2 a")
                        if not title_el:
                            continue
                        
                        title = (await title_el.inner_text()).strip()
                        url = await title_el.get_attribute("href")
                        if not url:
                            continue
                        
                        full_url = f"https://kwork.ru{url}" if url.startswith("/") else url
                        proj_id = url.split("/")[-1].split("?")[0]
                        
                        if proj_id in seen:
                            continue
                        seen.add(proj_id)
                        
                        # Проверяем бюджет
                        budget_el = await proj.query_selector(".project-price, .want-card__price, .price")
                        budget_text = (await budget_el.inner_text()).strip() if budget_el else "0"
                        numbers = re.findall(r'\d+', budget_text.replace(" ", "").replace("\u00a0", ""))
                        if not numbers:
                            continue
                        
                        budget = int(numbers[0])
                        if not (5000 <= budget <= 80000):
                            continue
                        
                        # Проверяем ключевые слова
                        title_lower = title.lower()
                        if not any(kw in title_lower for kw in keywords):
                            continue
                        
                        # НАЙДЕН!
                        _kwork_state["projects_found"] += 1
                        found_this_round += 1
                        
                        await notify_func(
                            f"НАЙДЕН ПРОЕКТ #{_kwork_state['projects_found']}\n"
                            f"{title}\n"
                            f"Бюджет: {budget_text}\n"
                            f"{full_url}\n\n"
                            f"Алина откликается..."
                        )
                        
                        # Генерируем отклик через Claude
                        response_text = await _generate_response_claude(title, budget)
                        
                        # Откликаемся
                        success = await _send_response(page, full_url, response_text)
                        if success:
                            _kwork_state["responses_sent"] += 1
                            await notify_func(f"Отклик отправлен: {title[:50]}...")
                        
                        await asyncio.sleep(5)
                        
                    except Exception as e:
                        continue
                
                if found_this_round == 0:
                    pass  # Тихо ждём следующего раунда
                
                # Ждём 3 минуты
                await asyncio.sleep(180)
                
            except Exception as e:
                await notify_func(f"Ошибка раунда: {e}")
                await asyncio.sleep(60)
        
        await browser.close()
    
    elapsed = (datetime.now() - _kwork_state["started_at"]).seconds // 60
    await notify_func(
        f"Охота завершена!\n"
        f"Время: {elapsed} мин\n"
        f"Найдено проектов: {_kwork_state['projects_found']}\n"
        f"Откликов отправлено: {_kwork_state['responses_sent']}"
    )
    _kwork_state["running"] = False


async def _generate_response_claude(title: str, budget: int) -> str:
    """Генерирует персональный отклик через Claude."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        prompt = f"""Напиши короткий отклик (3-4 предложения) на проект фрилансера-разработчика Python.

Проект: {title}
Бюджет: {budget} руб.

Требования:
- Начни с "Привет!" 
- Кратко покажи экспертизу
- Назови технологию
- Заверши предложением обсудить детали
- БЕЗ шаблонных фраз"""
        
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except:
        title_lower = title.lower()
        if "telegram" in title_lower or "бот" in title_lower:
            tech = "aiogram 3.x + FSM"
        elif "парсер" in title_lower:
            tech = "Playwright + Stealth"
        else:
            tech = "Python async"
        return f"Привет! Посмотрел проект — понятная задача. Делаю на {tech}, чистый код с документацией. Цена {budget} руб., срок 3-5 дней. Готовы обсудить детали?"


async def _send_response(page, url: str, response_text: str) -> bool:
    """Отправляет отклик на проект."""
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)
        
        selectors = [
            'textarea[placeholder*="опишите"]',
            'textarea[placeholder*="Опишите"]', 
            'textarea[name="response"]',
            '.want-response textarea',
            'textarea'
        ]
        
        for selector in selectors:
            try:
                await page.fill(selector, response_text, timeout=5000)
                
                btn_selectors = [
                    'button:has-text("Предложить")',
                    'button:has-text("Откликнуться")',
                    'button:has-text("Отправить")',
                    'button[type="submit"]'
                ]
                
                for btn in btn_selectors:
                    try:
                        await page.click(btn, timeout=5000)
                        await asyncio.sleep(3)
                        return True
                    except:
                        continue
                break
            except:
                continue
        return False
    except:
        return False


# ─────────────────────────────────────────────────────────────
#  Команды для Jarvis
# ─────────────────────────────────────────────────────────────

async def handle_kwork_command(user_text: str, notify_func) -> str:
    """Обработчик команд /кворк для Jarvis."""
    global _kwork_state
    
    text_lower = user_text.strip().lower()
    
    # /кворк старт [минуты]
    if "старт" in text_lower or "start" in text_lower:
        if _kwork_state["running"]:
            found = _kwork_state["projects_found"]
            sent = _kwork_state["responses_sent"]
            return f"Алина уже работает! Найдено: {found} проектов, откликов: {sent}.\nЧтобы остановить: /кворк стоп"
        
        # Извлекаем длительность
        nums = re.findall(r'\d+', user_text)
        duration = int(nums[0]) if nums else 60
        duration = min(max(duration, 10), 480)  # от 10 мин до 8 часов
        
        _kwork_state["running"] = True
        _kwork_state["task"] = asyncio.ensure_future(
            _kwork_hunt_loop(notify_func, duration_minutes=duration)
        )
        
        return f"Запускаю Алину на {duration} минут!\nБуду присылать уведомления о каждом проекте."
    
    # /кворк стоп
    elif "стоп" in text_lower or "stop" in text_lower:
        if not _kwork_state["running"]:
            return "Алина и так не работает."
        
        _kwork_state["running"] = False
        if _kwork_state["task"]:
            _kwork_state["task"].cancel()
        
        found = _kwork_state["projects_found"]
        sent = _kwork_state["responses_sent"]
        return f"Алина остановлена.\nВсего найдено: {found} проектов\nОткликов: {sent}"
    
    # /кворк статус
    elif "статус" in text_lower or "status" in text_lower:
        if _kwork_state["running"]:
            elapsed = ""
            if _kwork_state["started_at"]:
                mins = (datetime.now() - _kwork_state["started_at"]).seconds // 60
                elapsed = f"\nРаботает: {mins} мин"
            return (
                f"Алина работает! {elapsed}\n"
                f"Найдено проектов: {_kwork_state['projects_found']}\n"
                f"Откликов: {_kwork_state['responses_sent']}\n\n"
                f"Остановить: /кворк стоп"
            )
        else:
            return (
                f"Алина не запущена.\n"
                f"Последняя сессия: {_kwork_state['projects_found']} проектов, {_kwork_state['responses_sent']} откликов\n\n"
                f"Запустить: /кворк старт [минуты]"
            )
    
    # /кворк переговоры [текст клиента]
    elif "перегов" in text_lower:
        parts = user_text.split(maxsplit=2)
        if len(parts) < 3:
            return "Укажи текст клиента: /кворк переговоры [что написал клиент]"
        client_msg = parts[2]
        reply = await _negotiate_with_claude(client_msg)
        return f"Переговорщик отвечает:\n\n{reply}"
    
    # Помощь
    else:
        return (
            "Команды Kwork:\n\n"
            "/кворк старт — запустить охоту (60 мин)\n"
            "/кворк старт 30 — охота 30 минут\n"
            "/кворк стоп — остановить\n"
            "/кворк статус — текущий статус\n"
            "/кворк переговоры [текст] — ответить клиенту через AI"
        )


def is_kwork_command(text: str) -> bool:
    """Проверяет что это команда /кворк."""
    t = text.strip().lower()
    return t.startswith("/кворк") or t.startswith("кворк ")
