import asyncio
import sys
import json
import time
import requests
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from playwright.async_api import async_playwright

TOKEN = '8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y'
CHAT_ID = 6152243830
PENDING_FILE = Path("data/pending_replies.json")
AUTH_STATE = "data/auth_state.json"


def load_pending() -> dict:
    try:
        return json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_pending(data: dict):
    PENDING_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def send_tg(text: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text},
            timeout=10
        )
    except Exception:
        pass


def answer_cb(cq_id: str, text: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery",
            json={"callback_query_id": cq_id, "text": text},
            timeout=10
        )
    except Exception:
        pass


async def send_kwork_reply(username: str, reply_text: str) -> bool:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=AUTH_STATE)
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
            print(f"   [Bot] Отправлено @{username}")
            return True
        except Exception as e:
            print(f"   [Bot] Ошибка Playwright: {e}")
            return False
        finally:
            await context.close()
            await browser.close()


def poll():
    offset = 0
    edit_queue = []  # usernames ожидающих ручного ввода
    print(f"[Bot] Polling запущен. TOKEN={TOKEN[:20]}...")

    while True:
        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{TOKEN}/getUpdates",
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

                # Текстовое сообщение — ручной ответ после "Изменить"
                msg = update.get("message")
                if msg and msg.get("text") and edit_queue:
                    custom_text = msg["text"].strip()
                    username = edit_queue.pop(0)
                    print(f"[Bot] Ручной ответ для @{username}: {custom_text[:60]}")
                    ok = asyncio.run(send_kwork_reply(username, custom_text))
                    if ok:
                        pending = load_pending()
                        pending.pop(username, None)
                        save_pending(pending)
                        send_tg(f"\u2705 Ваш ответ отправлен @{username} на Kwork")
                    else:
                        send_tg(f"\u274c Не удалось отправить @{username}")
                    continue

                cq = update.get("callback_query")
                if not cq:
                    continue
                cb_data = cq.get("data", "")
                cq_id = cq["id"]

                print(f"[Bot] Callback: {cb_data}")

                if cb_data.startswith("send_inbox_"):
                    username = cb_data[len("send_inbox_"):]
                    pending = load_pending()
                    reply_text = pending.get(username)
                    if not reply_text:
                        answer_cb(cq_id, "\u26a0\ufe0f Ответ не найден (устарел?)")
                        print(f"[Bot] pending_replies.json: {list(pending.keys())}")
                        continue
                    answer_cb(cq_id, "\u23f3 Отправляю...")
                    ok = asyncio.run(send_kwork_reply(username, reply_text))
                    if ok:
                        pending.pop(username, None)
                        save_pending(pending)
                        send_tg(f"\u2705 Ответ Юлии отправлен @{username} на Kwork")
                    else:
                        send_tg(f"\u274c Не удалось отправить @{username} — kwork.ru/inbox/{username}")

                elif cb_data.startswith("edit_inbox_"):
                    username = cb_data[len("edit_inbox_"):]
                    answer_cb(cq_id, "\u270f\ufe0f Жду ваш вариант...")
                    edit_queue.append(username)
                    send_tg(
                        f"\u270f\ufe0f Напишите свой вариант ответа для @{username}:\n"
                        f"(следующее сообщение будет отправлено заказчику)"
                    )

        except Exception as e:
            print(f"[Bot] Ошибка polling: {e}")
            time.sleep(5)


if __name__ == "__main__":
    poll()
