import asyncio
import json
import os
import re
import sys
import requests
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from smart_agents import SmartOrchestrator

load_dotenv()
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

TELEGRAM_TOKEN = '8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y'
CHAT_ID = 6152243830

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"  [TG] Ошибка отправки: {e}")

def notify_response_sent(project):
    now = datetime.now().strftime("%H:%M")
    budget_fmt = f"{project['budget']:,}".replace(",", "\u00a0")
    text = (
        f"\u2705 \u041e\u0422\u041a\u041b\u0418\u041a \u041e\u0422\u041f\u0420\u0410\u0412\u041b\u0415\u041d!\n"
        f"\u23f0 {now}\n\n"
        f"\U0001f4cc {project['title'][:70]}\n"
        f"\U0001f4b0 \u0411\u044e\u0434\u0436\u0435\u0442: {budget_fmt} \u20bd\n"
        f"\U0001f517 https://kwork.ru/projects/{project['id']}\n\n"
        f"\U0001f465 \u041a\u043e\u043c\u0430\u043d\u0434\u0430 \u0441\u0440\u0430\u0431\u043e\u0442\u0430\u043b\u0430:\n"
        f"\U0001f50d \u0410\u043b\u0438\u043d\u0430 \u2014 \u043d\u0430\u0448\u043b\u0430 \u043f\u0440\u043e\u0435\u043a\u0442\n"
        f"\U0001f4ca \u0410\u043d\u043d\u0430 \u2014 \u043f\u0440\u043e\u0430\u043d\u0430\u043b\u0438\u0437\u0438\u0440\u043e\u0432\u0430\u043b\u0430\n"
        f"\u270d\ufe0f \u041c\u0430\u043a\u0441 \u2014 \u043d\u0430\u043f\u0438\u0441\u0430\u043b \u043e\u0442\u043a\u043b\u0438\u043a\n"
        f"\U0001f4e4 \u042e\u043b\u0438\u044f \u2014 \u043e\u0442\u043f\u0440\u0430\u0432\u0438\u043b\u0430 \u043d\u0430 Kwork\n\n"
        f"\u23f3 \u0416\u0434\u0451\u043c \u043e\u0442\u0432\u0435\u0442\u0430 \u0437\u0430\u043a\u0430\u0437\u0447\u0438\u043a\u0430...\n"
        f"\U0001f514 \u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433: \u043a\u0430\u0436\u0434\u044b\u0439 \u0447\u0430\u0441"
    )
    send_telegram(text)

# -- Темы для охоты ------------------------------------------
SEARCH_QUERIES = [
    "telegram бот",
    "ai агент",
    "автоматизация python",
    "чат бот",
    "python разработка",
]

KEYWORDS_SCORE = [
    "telegram", "бот", "bot", "aiogram", "ai", "ии", "агент", "agent",
    "автоматизация", "автомат", "python", "питон", "чат", "chat",
    "gpt", "llm", "openai", "langchain", "парсер", "parser",
    "webhook", "api", "интеграция",
]

TARGET_MIN = 5000
TARGET_MAX = 80000
TARGET_COUNT = 5



def load_responded_ids():
    ids = set()
    for fname in ["data/responded.json", "data/responses_log.json"]:
        try:
            data = json.loads(open(fname, encoding="utf-8").read())
            for r in data:
                ids.add(str(r.get("id") or r.get("project_id") or ""))
        except Exception:
            pass
    ids.discard("")
    return ids


def save_responded(project):
    fpath = Path("data/responded.json")
    data = []
    try:
        data = json.loads(fpath.read_text(encoding="utf-8"))
    except Exception:
        pass
    data.append({
        "id": str(project["id"]),
        "title": project["title"],
        "budget": project["budget"],
        "time": datetime.now().isoformat(),
    })
    fpath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def score_project(p):
    title_lower = (p.get("title") or "").lower()
    score = 0
    for kw in KEYWORDS_SCORE:
        if kw in title_lower:
            score += 1
    # бонус за бюджет (нормализуем в диапазоне)
    budget = p.get("budget", 0)
    score += min(budget / 10000, 5)
    return score


async def search_projects(page, query, responded_ids):
    url = f"https://kwork.ru/projects?c=41&keyword={query.replace(' ', '+')}"
    print(f"  Ищу: '{query}' -> {url}")
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)
    except Exception as e:
        print(f"  Ошибка загрузки: {e}")
        return []

    projects = await page.evaluate("""() => {
        return Array.from(document.querySelectorAll(".want-card")).slice(0, 50).map(card => {
            const link = card.querySelector("a[href*='/projects/']");
            const title = card.querySelector(".wants-card__header-title");
            const price = card.querySelector(".wants-card__price");
            const nums = (price ? price.innerText : "").replace(/[^\\d]/g, "").match(/\\d+/g);
            return {
                id: link ? link.href.split("/projects/")[1].split("/")[0].split("?")[0] : null,
                title: title ? title.innerText.trim() : null,
                budget: nums ? parseInt(nums[0]) : 0,
                url: link ? link.href : null
            };
        }).filter(p => p.id && p.title && p.budget >= 5000 && p.budget <= 80000);
    }""")

    fresh = [p for p in projects if str(p["id"]) not in responded_ids]
    print(f"  Найдено: {len(projects)} в диапазоне, {len(fresh)} новых")
    return fresh


async def respond_to_project(page, project, response_text):
    form_url = f"https://kwork.ru/new_offer?project={project['id']}"
    print(f"\n  Открываю форму: {form_url}")
    await page.goto(form_url, wait_until="networkidle", timeout=60000)
    await asyncio.sleep(3)

    if "new_offer" not in page.url:
        print(f"  Редирект -> {page.url} (проект закрыт)")
        return False

    # 1. ОПИСАНИЕ
    desc_editor = await page.query_selector('.trumbowyg-editor[placeholder*="как вы будете"]')
    if not desc_editor:
        desc_editor = await page.query_selector('.trumbowyg-editor')
    if not desc_editor:
        print("  Редактор описания не найден")
        return False

    await desc_editor.click()
    await asyncio.sleep(0.3)
    await page.keyboard.press("Control+a")
    await asyncio.sleep(0.1)
    await page.keyboard.press("Delete")
    await asyncio.sleep(0.1)
    await page.keyboard.type(response_text, delay=8)
    await asyncio.sleep(0.5)

    hidden_ta = await page.query_selector('textarea[name="description"]')
    actual_len = 0
    if hidden_ta:
        val = await hidden_ta.input_value()
        actual_len = len(val)
    print(f"  Описание: {actual_len} символов в textarea")
    if actual_len < 150:
        print(f"  Слишком мало символов, пропускаю")
        return False

    # 2. ЦЕНА
    price_input = await page.query_selector('input[type="tel"]')
    if price_input:
        await price_input.click(click_count=3)
        await asyncio.sleep(0.1)
        await page.keyboard.type(str(project["budget"]), delay=30)
        await asyncio.sleep(0.5)
        print(f"  Цена: {project['budget']} руб.")

    # 3. ПОРЯДОК ОПЛАТЫ — кликаем первый offer-payment-type__item напрямую
    payment_result = await page.evaluate("""() => {
        const item = document.querySelector('.offer-payment-type__item');
        if (!item) return null;
        item.scrollIntoView({block: 'center'});
        const r = item.getBoundingClientRect();
        return { x: r.left + r.width / 2, y: r.top + r.height / 2, cls: item.className };
    }""")
    await asyncio.sleep(0.5)
    if payment_result:
        await page.mouse.click(payment_result["x"], payment_result["y"])
        await asyncio.sleep(0.8)
        print(f"  Оплата: кликнуто ({payment_result['x']:.0f},{payment_result['y']:.0f}) cls={payment_result['cls'][:50]}")
    else:
        print(f"  Оплата: .offer-payment-type__item не найден")

    # 4. НАЗВАНИЕ ЗАКАЗА
    order_name = f"Предложение: {project['title'][:50]}"
    await page.evaluate("""(txt) => {
        const ta = document.querySelector('textarea[name="name"]');
        if (!ta) return;
        const box = ta.closest('.trumbowyg-box') || ta.parentElement;
        const editorDiv = box ? box.querySelector('.trumbowyg-editor') : null;
        if (window.$ && typeof $(ta).trumbowyg === 'function') {
            try { $(ta).trumbowyg('html', '<p>' + txt + '</p>'); } catch(e) {}
        }
        if (editorDiv) {
            editorDiv.innerHTML = '<p>' + txt + '</p>';
            editorDiv.dispatchEvent(new InputEvent('input', {bubbles: true}));
        }
        if (window.$ && typeof $(ta).trumbowyg === 'function') {
            try { $(ta).trumbowyg('syncCode'); } catch(e) {}
        }
    }""", order_name)
    await asyncio.sleep(0.5)
    print(f"  Название: {order_name[:50]}")

    # 5. СРОК ВЫПОЛНЕНИЯ — click(force=True) обходит vs__actions overlay
    vs_toggle = page.locator('.vs__dropdown-toggle').first
    await vs_toggle.scroll_into_view_if_needed()
    await asyncio.sleep(0.3)
    await vs_toggle.click(force=True)
    await asyncio.sleep(1.5)
    opt_txt = await page.evaluate("""() => {
        const options = document.querySelectorAll('.vs__dropdown-menu li');
        if (options.length > 0) { const t = options[0].innerText.trim(); options[0].click(); return t; }
        return null;
    }""")
    await page.wait_for_timeout(500)
    if opt_txt:
        print(f"  Срок: выбран '{opt_txt}'")
    else:
        print(f"  Срок: опции не найдены, keyboard fallback...")
        await page.keyboard.press("ArrowDown")
        await asyncio.sleep(0.5)
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)

    # 6. ОТПРАВКА
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(2)

    send_btn = await page.query_selector('button:has-text("Предложить")')
    if not send_btn:
        print(f"  Кнопка не найдена")
        return False

    await page.screenshot(path=f"data/hunt_before_submit_{project['id']}.png")

    for attempt in range(1, 3):
        try:
            await send_btn.click()
            await page.wait_for_timeout(3000)
            break
        except Exception as e:
            if "Timeout" in type(e).__name__ and attempt == 1:
                print(f"  Timeout при отправке, retry #{attempt + 1}...")
                await asyncio.sleep(3)
                send_btn = await page.query_selector('button:has-text("Предложить")')
                if not send_btn:
                    print(f"  Кнопка исчезла после timeout")
                    return False
            else:
                raise

    # Модалка "Шаблонный текст" — кликаем "Отправить как есть"
    template_btn = await page.query_selector('button:has-text("Отправить как есть")')
    if template_btn:
        print(f"  Модалка 'Шаблонный текст' — кликаю 'Отправить как есть'")
        await template_btn.click()
        await asyncio.sleep(5)

    # Retry если просит нажать повторно
    print(f"  URL post-submit: {page.url}")
    body_txt = await page.evaluate("document.body.innerText")
    if "new_offer" in page.url and "повторн" in body_txt.lower():
        print(f"  Retry -- кликаю повторно...")
        send_btn2 = await page.query_selector('button:has-text("Предложить")')
        if send_btn2:
            await send_btn2.click()
            await asyncio.sleep(3)
            # Снова проверяем модалку после retry
            template_btn2 = await page.query_selector('button:has-text("Отправить как есть")')
            if template_btn2:
                print(f"  Модалка повторно — кликаю 'Отправить как есть'")
                await template_btn2.click()
                await asyncio.sleep(5)
            print(f"  URL после retry: {page.url}")

    if "new_offer" not in page.url:
        print(f"  USPEKH -- URL: {page.url}")
        return True

    # Полный дамп ошибок из формы
    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(0.5)
    await page.screenshot(path=f"data/hunt_fail_{project['id']}.png", full_page=True)

    err_text = await page.evaluate("""() => {
        // Собираем всё красное / ошибочное
        const msgs = new Set();
        document.querySelectorAll(
            '[class*="error"], [class*="Error"], [class*="invalid"], [class*="red"], [style*="color: red"]'
        ).forEach(e => {
            const t = (e.innerText || '').trim();
            if (t.length > 3 && t.length < 300) msgs.add(t);
        });
        // Из всего body — строки похожие на ошибки
        document.body.innerText.split('\\n').forEach(line => {
            line = line.trim();
            if (line.length < 5 || line.length > 250) return;
            if (line.includes('Укажите') || line.includes('Выберите') ||
                line.includes('Заполните') || line.includes('обязательно') ||
                line.includes('повторно') || line.includes('Нажмите') ||
                line.includes('соглашение') || line.includes('Правил') ||
                line.includes('запрещен') || line.includes('пустые')) {
                msgs.add(line);
            }
        });
        return [...msgs].slice(0, 8);
    }""")
    for msg in err_text:
        print(f"  [ERR] {msg[:120]}")
    if not err_text:
        print(f"  Форма не отправлена, ошибок не найдено. Скриншот: data/hunt_fail_{project['id']}.png")
    return False


async def main():
    print("=" * 60)
    print("KWORK ОХОТА -- 5 ОТКЛИКОВ")
    print(f"Темы: {', '.join(SEARCH_QUERIES)}")
    print(f"Диапазон: {TARGET_MIN:,}-{TARGET_MAX:,} руб.")
    print("=" * 60)

    responded_ids = load_responded_ids()
    print(f"\nУже откликнулись: {len(responded_ids)} проектов\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context(
            storage_state="data/auth_state.json",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        # -- ПОИСК -----------------------------------------------
        print("[ПОИСК] Собираю проекты по всем темам...")
        all_projects = {}
        for query in SEARCH_QUERIES:
            projects = await search_projects(page, query, responded_ids)
            for proj in projects:
                pid = str(proj["id"])
                if pid not in all_projects:
                    all_projects[pid] = proj
            await asyncio.sleep(1)

        print(f"\nВсего уникальных новых проектов: {len(all_projects)}")

        if not all_projects:
            print("Нет подходящих проектов -- выход")
            await context.close()
            await browser.close()
            return

        # -- ОТБОР ТОП-5 -----------------------------------------
        ranked = sorted(all_projects.values(), key=score_project, reverse=True)

        print(f"\n[ТОП-{TARGET_COUNT}] Лучшие проекты:")
        for i, p in enumerate(ranked[:TARGET_COUNT], 1):
            print(f"  {i}. [{p['budget']:,} руб.] {p['title'][:60]}")
            print(f"     https://kwork.ru/projects/{p['id']}")

        # -- ОТКЛИКИ ---------------------------------------------
        sent = 0
        failed = 0
        orchestrator = SmartOrchestrator()
        print(f"\n[ОТКЛИКИ] Отправляю на {TARGET_COUNT} проектов...")
        for proj in ranked[:TARGET_COUNT]:
            print(f"\n{'-'*50}")
            print(f"Проект #{proj['id']}: {proj['title'][:55]}")
            print(f"Бюджет: {proj['budget']:,} руб.")
            try:
                print(f"  [OODA] Анна + Макс анализируют проект...")
                response_text = await orchestrator.process(proj)
                if not response_text:
                    print(f"  [OODA] Анна решила не откликаться — пропускаю")
                    failed += 1
                    continue
                success = await respond_to_project(page, proj, response_text)
                if success:
                    save_responded(proj)
                    responded_ids.add(str(proj["id"]))
                    sent += 1
                    print(f"  +++ ОТКЛИК #{sent} ОТПРАВЛЕН +++")
                    notify_response_sent(proj)
                else:
                    failed += 1
                    print(f"  --- Не отправлен ---")
            except Exception as e:
                failed += 1
                print(f"  ОШИБКА: {e}")
            await asyncio.sleep(3)

        # -- ИТОГ ------------------------------------------------
        print(f"\n{'='*60}")
        print(f"ИТОГ: Отправлено {sent} / {TARGET_COUNT} откликов")
        print(f"      Ошибок: {failed}")
        print(f"{'='*60}")

        await asyncio.sleep(3)
        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
