import asyncio
import sys
import schedule
import time
import os
import threading

sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime
from playwright.async_api import async_playwright
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from order_executor import OrderExecutor

load_dotenv()

class HourlyMonitor:
    """Мониторит новые сообщения в сделках Kwork"""

    def __init__(self):
        self.chat_id = 6152243830
        self.token = '8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y'
        self.monitored_file = Path("data/monitored_deals.json")
        self.executor = OrderExecutor()
        self.pending_replies = {}  # username -> reply_text
        self.edit_queue = []       # [username, ...] ожидают ручного ответа
        self.load_monitored()
        t = threading.Thread(target=self._poll_callbacks, daemon=True)
        t.start()
    
    def load_monitored(self):
        if self.monitored_file.exists():
            self.monitored = json.loads(self.monitored_file.read_text(encoding='utf-8'))
        else:
            self.monitored = {}
        self.inbox_seen_file = Path("data/inbox_seen.json")
        self.inbox_seen = set()
        if self.inbox_seen_file.exists():
            try:
                self.inbox_seen = set(json.loads(self.inbox_seen_file.read_text(encoding='utf-8')))
            except Exception:
                pass
    
    def send_telegram(self, message):
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
            )
        except:
            pass
    
    async def check_messages(self):
        """Проверяет новые сообщения в Kwork"""
        
        print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - ПРОВЕРКА СООБЩЕНИЙ")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state="data/auth_state.json")
            page = await context.new_page()
            
            try:
                await page.goto("https://kwork.ru/seller", wait_until="networkidle")
                await asyncio.sleep(2)
                
                new_messages = await page.evaluate('''() => {
                    const deals = [];
                    document.querySelectorAll('[class*="deal"]').forEach(el => {
                        const link = el.querySelector('a[href*="/projects/"], a[href*="/deal/"]');
                        const id = el.getAttribute('data-id') || (link && link.href.split('/').pop());
                        const title = (el.querySelector('[class*="title"]')?.innerText || el.innerText.split('\\n')[0] || '').trim();
                        const hasNew = el.querySelector('[class*="badge"], [class*="unread"], [class*="new"]') !== null;
                        const priceEl = el.querySelector('[class*="price"], [class*="budget"], [class*="cost"]');
                        const nums = priceEl ? priceEl.innerText.replace(/[^\\d]/g, '').match(/\\d+/) : null;
                        const msgEl = el.querySelector('[class*="message"], [class*="last-msg"], [class*="preview"]');
                        const statusEl = el.querySelector('[class*="status"], [class*="state"], [class*="stage"]');
                        const statusText = statusEl ? statusEl.innerText.trim().toLowerCase() : '';
                        const cssClasses = el.className || '';
                        if (id && title) {
                            deals.push({
                                id: id,
                                title: title,
                                hasNew: hasNew,
                                url: link ? link.href : null,
                                budget: nums ? parseInt(nums[0]) : 0,
                                last_message: msgEl ? msgEl.innerText.trim().slice(0, 300) : '',
                                status: statusText,
                                css_classes: cssClasses
                            });
                        }
                    });
                    return deals;
                }''')
                
                await context.close()
                await browser.close()
                
                return new_messages
            
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                await context.close()
                await browser.close()
                return []
    
    def generate_yulia_reply(self, title: str, budget: int, client_message: str) -> str | None:
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            budget_fmt = f"{budget:,}".replace(",", "\u00a0") if budget else "не указан"
            msg = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                system="Ты Юлия, руководитель команды ST8-AI. Отвечаешь заказчику на Kwork. Команда: Макс (Python разработчик), Анна (аналитик), Юлия (PM). Стиль: профессионально, конкретно, без воды.",
                messages=[{
                    "role": "user",
                    "content": f"Проект: {title}\nБюджет: {budget_fmt} ₽\nСообщение заказчика: {client_message}"
                }]
            )
            return msg.content[0].text
        except Exception as e:
            print(f"   [Claude] Ошибка: {e}")
            return None

    def _active_responses_count(self):
        try:
            data = json.loads(Path("data/responded.json").read_text(encoding="utf-8"))
            return len(data)
        except Exception:
            return 0

    async def check_inbox(self):
        """Проверяет непрочитанные сообщения в kwork.ru/inbox"""
        print(f"   [Inbox] Проверяю kwork.ru/inbox...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(storage_state="data/auth_state.json")
            page = await context.new_page()
            try:
                await page.goto("https://kwork.ru/inbox", wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(5000)
                messages = await page.evaluate("""() => {
                    const results = [];
                    const seen = new Set();
                    document.querySelectorAll('li.chat__list-item').forEach(li => {
                        const userEl = li.querySelector('.chat__list-user');
                        const username = userEl ? userEl.innerText.trim() : '';
                        if (!username || seen.has(username)) return;
                        seen.add(username);

                        const msgEl = li.querySelector('.chat__list-message');
                        const preview = msgEl ? msgEl.innerText.trim().slice(0, 300) : '';
                        if (!preview) return;
                        if (preview.startsWith('\u0412\u044b:')) return;

                        const counterEl = li.querySelector('.chat__list-counter');
                        const unread_count = counterEl ? counterEl.innerText.trim() : '0';

                        results.push({
                            username: username,
                            name: username,
                            preview: preview,
                            unread_count: unread_count,
                            has_unread: unread_count !== '0' && unread_count !== '',
                            url: 'https://kwork.ru/inbox/' + username
                        });
                    });
                    return results;
                }""")
                print(f"   [Inbox] Диалогов с превью: {len(messages)}, непрочитанных: {sum(1 for m in messages if m['has_unread'])}")
                return messages
            except Exception as e:
                print(f"   [Inbox] Ошибка: {e}")
                return []
            finally:
                await context.close()
                await browser.close()

    def generate_inbox_reply(self, username: str, preview: str) -> str | None:
        """Генерирует ответ Юлии на сообщение из inbox"""
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            msg = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                system=(
                    "Ты Юлия, руководитель команды ST8-AI. Отвечаешь клиенту в личных сообщениях на Kwork. "
                    "Команда: Макс (Python разработчик), Анна (аналитик), Юлия (PM). "
                    "Стиль: профессионально, дружелюбно, конкретно, без воды. Максимум 3-4 предложения."
                ),
                messages=[{
                    "role": "user",
                    "content": f"Сообщение от пользователя @{username}:\n{preview}\n\nНапиши ответ от Юлии."
                }]
            )
            return msg.content[0].text
        except Exception as e:
            print(f"   [Claude/Inbox] Ошибка: {e}")
            return None

    async def send_kwork_inbox_reply(self, username: str, reply_text: str) -> bool:
        """Открывает kwork.ru/inbox/username и отправляет текст в чат"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(storage_state="data/auth_state.json")
            page = await context.new_page()
            try:
                await page.goto(f"https://kwork.ru/inbox/{username}", wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(4000)
                textarea = await page.wait_for_selector("textarea", timeout=10000)
                await textarea.click()
                await textarea.fill(reply_text)
                await page.wait_for_timeout(500)
                send_btn = page.locator("button.chat__send-button, button[type='submit']").first
                if await send_btn.count() > 0:
                    await send_btn.click()
                else:
                    await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)
                print(f"   [Playwright/Send] Ответ отправлен @{username}")
                return True
            except Exception as e:
                print(f"   [Playwright/Send] Ошибка: {e}")
                return False
            finally:
                await context.close()
                await browser.close()

    def _answer_cb(self, cq_id: str, text: str):
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.token}/answerCallbackQuery",
                json={"callback_query_id": cq_id, "text": text},
                timeout=10
            )
        except Exception:
            pass

    def _poll_callbacks(self):
        """Long-polling Telegram: callback_query + message в отдельном потоке"""
        offset = 0
        print("   [TG/Poll] Обработчик callback запущен")
        while True:
            try:
                resp = requests.get(
                    f"https://api.telegram.org/bot{self.token}/getUpdates",
                    params={
                        "offset": offset,
                        "timeout": 30,
                        "allowed_updates": ["callback_query", "message"]
                    },
                    timeout=35
                )
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1

                    # ── Обычное текстовое сообщение (ручной ответ после "Изменить") ──
                    msg = update.get("message")
                    if msg and msg.get("text") and self.edit_queue:
                        custom_text = msg["text"].strip()
                        username = self.edit_queue.pop(0)
                        print(f"   [TG/Poll] Ручной ответ для @{username}: {custom_text[:50]}")
                        ok = asyncio.run(self.send_kwork_inbox_reply(username, custom_text))
                        if ok:
                            self.send_telegram(f"\u2705 Ваш ответ отправлен @{username} на Kwork")
                        else:
                            self.send_telegram(f"\u274c Не удалось отправить @{username} — kwork.ru/inbox/{username}")
                        continue

                    # ── Callback от кнопок ──
                    cq = update.get("callback_query")
                    if not cq:
                        continue
                    cb_data = cq.get("data", "")
                    cq_id = cq["id"]

                    if cb_data.startswith("send_inbox_"):
                        username = cb_data[len("send_inbox_"):]
                        reply_text = self.pending_replies.get(username)
                        if not reply_text:
                            self._answer_cb(cq_id, "\u26a0\ufe0f Ответ не найден (устарел?)")
                            continue
                        self._answer_cb(cq_id, "\u23f3 Отправляю...")
                        print(f"   [TG/Poll] send_inbox_{username} — запускаю Playwright")
                        ok = asyncio.run(self.send_kwork_inbox_reply(username, reply_text))
                        if ok:
                            self.pending_replies.pop(username, None)
                            self.send_telegram(f"\u2705 Ответ Юлии отправлен @{username} на Kwork")
                        else:
                            self.send_telegram(f"\u274c Не удалось отправить @{username} — kwork.ru/inbox/{username}")

                    elif cb_data.startswith("edit_inbox_"):
                        username = cb_data[len("edit_inbox_"):]
                        self._answer_cb(cq_id, "\u270f\ufe0f Жду ваш вариант...")
                        self.edit_queue.append(username)
                        self.send_telegram(
                            f"\u270f\ufe0f Напишите свой вариант ответа для @{username}:\n"
                            f"(следующее сообщение будет отправлено заказчику)"
                        )
                        print(f"   [TG/Poll] edit_inbox_{username} — ждём ручной ввод")

            except Exception as e:
                print(f"   [TG/Poll] Ошибка: {e}")
                time.sleep(5)

    async def process_inbox_messages(self):
        """Для каждого непрочитанного диалога генерирует ответ Юлии и отправляет в Telegram с кнопками"""
        messages = await self.check_inbox()
        new_count = 0
        for msg in messages:
            key = f"{msg['username']}:{msg['preview'][:80]}"
            if key in self.inbox_seen:
                continue
            self.inbox_seen.add(key)

            print(f"   [Inbox] Новое: {msg['name']} ({msg['username']}) | {msg['preview'][:50]}")
            print(f"   [Claude] Генерирую ответ Юлии...")
            reply = self.generate_inbox_reply(msg['username'], msg['preview'])

            if reply:
                self.pending_replies[msg['username']] = reply
                Path("data/pending_replies.json").write_text(
                    json.dumps(self.pending_replies, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                text = (
                    f"💬 НОВОЕ СООБЩЕНИЕ В INBOX!\n"
                    f"👤 От: {msg['name']} (@{msg['username']})\n"
                    f"✉️ {msg['preview'][:200]}\n\n"
                    f"🤖 Юлия подготовила ответ:\n{reply}"
                )
                requests.post(
                    f"https://api.telegram.org/bot{self.token}/sendMessage",
                    json={
                        'chat_id': self.chat_id,
                        'text': text,
                        'reply_markup': {
                            'inline_keyboard': [[
                                {'text': '✅ Отправить', 'callback_data': f'send_inbox_{msg["username"]}'},
                                {'text': '✏️ Изменить', 'callback_data': f'edit_inbox_{msg["username"]}'}
                            ]]
                        }
                    },
                    timeout=15
                )
            else:
                text = (
                    f"💬 НОВОЕ СООБЩЕНИЕ В INBOX!\n"
                    f"👤 От: {msg['name']} (@{msg['username']})\n"
                    f"✉️ {msg['preview'][:200]}\n"
                    f"🔗 kwork.ru/inbox/{msg['username']}"
                )
                self.send_telegram(text)

            print(f"   [Inbox] → TG: {msg['name']} | reply={'да' if reply else 'нет'}")
            new_count += 1

        if new_count:
            self.inbox_seen_file.write_text(
                json.dumps(list(self.inbox_seen), ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        else:
            print(f"   [Inbox] Новых сообщений нет")

    async def process_new_messages(self):
        """Обрабатывает найденные новые сообщения"""
        now = datetime.now().strftime("%H:%M")
        print(f"Ищу новые сообщения...")
        await self.process_inbox_messages()

        deals = await self.check_messages()
        new_deals = [d for d in deals if d.get("hasNew") and str(d["id"]) not in self.monitored]

        print(f"   Сделок: {len(deals)}, новых: {len(new_deals)}")

        if new_deals:
            for deal in new_deals:
                budget = deal.get("budget", 0)
                budget_fmt = f"{budget:,}".replace(",", "\u00a0") if budget else "?"
                msg_text = (deal.get("last_message") or "").strip()

                if msg_text:
                    print(f"   [Claude] Генерирую ответ Юлии для {deal['id']}...")
                    reply = self.generate_yulia_reply(deal['title'], budget, msg_text)
                else:
                    reply = None

                if reply:
                    text = (
                        f"💬 ЗАКАЗЧИК ОТВЕТИЛ!\n"
                        f"📌 Проект: {deal['title'][:70]}\n"
                        f"✉️ Сообщение: {msg_text[:200]}\n\n"
                        f"🤖 Юлия подготовила ответ:\n{reply}"
                    )
                    requests.post(
                        f"https://api.telegram.org/bot{self.token}/sendMessage",
                        json={
                            'chat_id': self.chat_id,
                            'text': text,
                            'reply_markup': {
                                'inline_keyboard': [[
                                    {'text': '✅ Отправить', 'callback_data': f'send_reply_{deal["id"]}'},
                                    {'text': '✏️ Изменить', 'callback_data': f'edit_reply_{deal["id"]}'}
                                ]]
                            }
                        },
                        timeout=15
                    )
                else:
                    text = (
                        f"💬 НОВЫЙ ОТВЕТ НА KWORK!\n"
                        f"⏰ {now}\n\n"
                        f"📌 Проект: {deal['title'][:70]}\n"
                        f"💰 Бюджет: {budget_fmt} \u20bd\n"
                        f"🔗 https://kwork.ru/projects/{deal['id']}\n"
                    )
                    self.send_telegram(text)

                print(f"   [TG] Отправлено уведомление: {deal['id']}")

                self.monitored[str(deal["id"])] = {
                    "title": deal["title"],
                    "url": deal.get("url"),
                    "first_message_at": datetime.now().isoformat(),
                    "status": "received",
                }
                self.monitored_file.write_text(
                    json.dumps(self.monitored, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
        else:
            print(f"   Ответов нет")

        # Второй проход: проверяем смену статуса для всех отслеживаемых сделок.
        # Если статус изменился на "принята/в работе" — заказчик выбрал нас → executor.
        for deal in deals:
            deal_id = str(deal["id"])
            stored = self.monitored.get(deal_id)
            if not stored or stored.get("status") == "order_started":
                continue
            status_text = deal.get("status", "").lower()
            css = deal.get("css_classes", "").lower()
            is_accepted = any(kw in status_text for kw in ["работ", "принят", "выполн", "active", "progress"])
            is_accepted = is_accepted or any(kw in css for kw in ["in-work", "in_work", "accepted", "active"])
            if is_accepted:
                print(f"   [Executor] Сделка {deal_id} принята заказчиком! Запускаю executor...")
                self.monitored[deal_id]["status"] = "order_started"
                self.monitored[deal_id]["order_started_at"] = datetime.now().isoformat()
                self.monitored_file.write_text(
                    json.dumps(self.monitored, indent=2, ensure_ascii=False), encoding="utf-8"
                )
                await self.executor.execute_order(deal_id, stored.get("title", ""), deal.get("budget", 0))

class SchedulerManager:
    """Управляет расписанием проверок"""
    
    def __init__(self):
        self.monitor = HourlyMonitor()
    
    def run_check(self):
        """Запускает проверку"""
        asyncio.run(self.monitor.process_new_messages())
    
    def start(self):
        """Запускает планировщик"""
        
        # Проверяем сообщения каждый час
        schedule.every(1).hour.do(self.run_check)
        
        # Первая проверка сразу
        self.run_check()
        
        print("=" * 70)
        print("🔔 ПОЛНАЯ СИСТЕМА АВТОМАТИЗАЦИИ ЗАПУЩЕНА!")
        print("=" * 70)
        print()
        print("ПРОЦЕСС:")
        print("  1️⃣ Проверка новых сообщений: каждый час")
        print("  2️⃣ Если пришёл ответ → ВКЛЮЧАЕТСЯ АГЕНТ")
        print("  3️⃣ Агент разрабатывает работу (30 сек)")
        print("  4️⃣ ДОСТАВЛЯЕТ НА ТВОЮ ПРОВЕРКУ")
        print("  5️⃣ Ты одобряешь или переделываешь")
        print("  6️⃣ Работа отправляется заказчику")
        print()
        print("=" * 70)
        print()
        
        # Основной цикл
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == '__main__':
    try:
        import schedule
    except ImportError:
        print("pip install schedule")
        exit(1)
    
    manager = SchedulerManager()
    manager.start()
