import asyncio
import os
import re
from playwright.async_api import async_playwright
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv()

class AutoSystem:
    def __init__(self):
        self.data_dir = Path("data")
        self.responded_file = self.data_dir / "responded.json"
        self.responded = self._load_responded()

    def _load_responded(self):
        if self.responded_file.exists():
            try:
                return json.loads(self.responded_file.read_text(encoding='utf-8'))
            except:
                return []
        return []

    def _save_responded(self, proj):
        self.responded.append({
            'id': proj['id'],
            'title': proj['title'],
            'budget': proj['budget'],
            'time': datetime.now().isoformat()
        })
        self.responded_file.write_text(
            json.dumps(self.responded, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

    def _make_reply(self, title, budget, tz):
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                system=(
                    "Ты Юлия, руководитель команды ST8-AI на Kwork. "
                    "Пиши продающий отклик от первого лица. "
                    "Упомяни конкретику из ТЗ заказчика. "
                    "Напиши что именно мы сделаем для этого проекта — 3-4 пункта через тире. "
                    "Команда: Макс (Python/AI), Анна (аналитик), Юлия (PM). "
                    "ТОЛЬКО простой текст. Никаких звёздочек, никакого markdown. "
                    "Минимум 200 символов."
                ),
                messages=[{
                    "role": "user",
                    "content": f"Проект: {title}\nБюджет: {budget} руб.\nТЗ: {tz[:600]}\n\nНапиши отклик от Юлии. Только простой текст."
                }]
            )
            reply = msg.content[0].text
            # Убираем любой markdown
            reply = re.sub(r'\*+', '', reply)
            reply = re.sub(r'#{1,6}\s*', '', reply)
            reply = re.sub(r'_{1,2}', '', reply)
            return reply
        except Exception as e:
            print(f"   [Claude] Ошибка: {e}")
            return (
                f"Здравствуйте! Я Юлия, руководитель команды ST8-AI.\n\n"
                f"Изучили ваш проект. Вот что сделаем:\n"
                f"— Полная реализация по вашему ТЗ\n"
                f"— Чистый код с документацией\n"
                f"— Интеграция с нужными сервисами\n"
                f"— Поддержка после сдачи\n\n"
                f"Бюджет {budget} руб. нас устраивает. Готовы обсудить детали!"
            )

    async def find_projects(self):
        print("Ищу проекты...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state="data/auth_state.json")
            page = await context.new_page()
            await page.goto("https://kwork.ru/projects?page=1", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(4)

            projects_raw = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll(".want-card, .want-card--list")).map(el => {
                    const link = el.querySelector("a[href*='/projects/']");
                    const title = el.querySelector(".wants-card__header-title, .want-card__title");
                    const price = el.querySelector(".wants-card__price, .want-card__price");
                    return {
                        id: link ? link.href.split("/").filter(Boolean).pop() : null,
                        title: title ? title.innerText.trim() : null,
                        price_text: price ? price.innerText.trim() : null,
                        url: link ? link.href : null
                    };
                });
            }''')

            await context.close()
            await browser.close()

            projects = []
            already = [r['id'] for r in self.responded]

            for proj in projects_raw:
                if not proj['id'] or not proj['title'] or proj['id'] in already:
                    continue
                if not proj['price_text']:
                    continue
                numbers = re.findall(r'\d+', proj['price_text'].replace(' ', '').replace('\u00a0', ''))
                if not numbers:
                    continue
                budget = int(numbers[0])
                if 5000 <= budget <= 80000:
                    projects.append({
                        'id': proj['id'],
                        'title': proj['title'],
                        'budget': budget,
                        'url': proj['url'],
                        'price_text': proj['price_text']
                    })

            return projects

    async def get_tz(self, project_id):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(storage_state="data/auth_state.json")
                page = await context.new_page()
                await page.goto(f"https://kwork.ru/projects/{project_id}", wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(2)
                tz = await page.evaluate("""() => {
                    const sel = ['.wants-card__description', '.project-description', '[class*="description"]', '.want-card__description'];
                    for (const s of sel) {
                        const el = document.querySelector(s);
                        if (el && el.innerText.trim().length > 20) return el.innerText.trim();
                    }
                    return '';
                }""")
                await context.close()
                await browser.close()
                return tz
        except:
            return ''

    async def respond(self, project):
        print(f"\nОтклик на #{project['id']} | {project['title'][:50]}")

        # Получаем ТЗ
        tz = await self.get_tz(project['id'])
        print(f"   ТЗ: {tz[:80]}...")

        # Генерируем текст
        reply = self._make_reply(project['title'], project['budget'], tz)
        print(f"   Текст: {reply[:80]}...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(storage_state="data/auth_state.json")
            page = await context.new_page()

            try:
                await page.goto(
                    f"https://kwork.ru/new_offer?project={project['id']}",
                    wait_until="domcontentloaded",
                    timeout=30000
                )
                await asyncio.sleep(4)

                if "new_offer" not in page.url:
                    print(f"   Редирект: {page.url}")
                    return False

                # Описание через trumbowyg
                editor = await page.query_selector('.trumbowyg-editor')
                if editor:
                    await editor.click()
                    await asyncio.sleep(0.3)
                    await page.keyboard.press("Control+a")
                    await page.keyboard.press("Delete")
                    await page.keyboard.type(reply, delay=10)
                    await asyncio.sleep(0.5)
                    print("   OK: описание")
                else:
                    print("   Редактор не найден")
                    return False

                # Стоимость
                tel = await page.query_selector("input[type=tel]")
                if tel:
                    await tel.click(click_count=3)
                    await asyncio.sleep(0.1)
                    await page.keyboard.type(str(project['budget']), delay=30)
                    await asyncio.sleep(0.5)
                    print(f"   OK: цена {project['budget']}")

                # Порядок оплаты — используем locator
                await page.evaluate("window.scrollBy(0, 400)")
                await asyncio.sleep(1)
                payment_found = False
                # Пробуем разные подходы
                for attempt in range(3):
                    try:
                        loc = page.locator("text=Целиком, когда заказ выполнен").first
                        if await loc.count() > 0:
                            await loc.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            await loc.click(force=True)
                            await asyncio.sleep(0.8)
                            payment_found = True
                            print("   OK: оплата Целиком")
                            break
                    except:
                        await asyncio.sleep(0.5)
                if not payment_found:
                    # Fallback через JS dispatch event
                    await page.evaluate("""() => {
                        for (const el of document.querySelectorAll('*')) {
                            if ((el.innerText || '').trim().startsWith('Целиком')) {
                                el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                                el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                                el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                                break;
                            }
                        }
                    }""")
                    await asyncio.sleep(0.8)
                    print("   OK: оплата (JS dispatch)")

                # Срок выполнения
                vs = await page.query_selector('.vs__dropdown-toggle')
                if vs:
                    await vs.scroll_into_view_if_needed()
                    await vs.click()
                    await asyncio.sleep(1.5)
                    opt = await page.query_selector('.vs__dropdown-option')
                    if opt:
                        await opt.click()
                        await asyncio.sleep(0.5)
                        print("   OK: срок")

                # Название заказа
                order_name = project['title'][:65]
                await page.evaluate("""(txt) => {
                    const ta = document.querySelector('textarea[name="name"]');
                    if (!ta) return;
                    const box = ta.closest('.trumbowyg-box') || ta.parentElement;
                    const div = box ? box.querySelector('.trumbowyg-editor') : null;
                    if (div) {
                        div.innerHTML = '<p>' + txt + '</p>';
                        div.dispatchEvent(new InputEvent('input', {bubbles: true}));
                    }
                    if (window.$ && $(ta).trumbowyg) {
                        try { $(ta).trumbowyg('syncCode'); } catch(e) {}
                    }
                }""", order_name)
                await asyncio.sleep(0.5)
                print(f"   OK: название")

                # Скролл к кнопке
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)

                send_btn = await page.query_selector('button:has-text("Предложить")')
                if not send_btn:
                    await page.screenshot(path="data/debug_no_btn.png")
                    print("   Кнопка не найдена")
                    return False

                await page.screenshot(path="data/before_submit.png")
                await send_btn.click()
                await asyncio.sleep(5)

                # Retry если Kwork просит повторно
                body = await page.evaluate("document.body.innerText")
                if "new_offer" in page.url and "повторн" in body.lower():
                    btn2 = await page.query_selector('button:has-text("Предложить")')
                    if btn2:
                        await btn2.click()
                        await asyncio.sleep(5)

                await page.screenshot(path="data/after_submit.png")

                if "new_offer" not in page.url:
                    self._save_responded(project)
                    print(f"   ОТПРАВЛЕН! URL: {page.url}")
                    return True
                else:
                    errors = await page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('.field-error, .error-text, [class*="error"]'))
                            .map(e => e.innerText.trim())
                            .filter(t => t.length > 3 && t.length < 200);
                    }""")
                    for err in errors:
                        print(f"   Ошибка: {err}")
                    return False

            except Exception as e:
                print(f"   Исключение: {e}")
                try:
                    await page.screenshot(path="data/debug_exception.png")
                except:
                    pass
                return False
            finally:
                await context.close()
                await browser.close()


async def main():
    print("=" * 60)
    print("ST8-AI ОХОТА НА KWORK")
    print("=" * 60)

    system = AutoSystem()
    projects = await system.find_projects()

    if not projects:
        print("Нет новых проектов 5000-80000 руб.")
        return

    print(f"\nНайдено: {len(projects)} проектов")
    for i, p in enumerate(projects, 1):
        print(f"  {i}. {p['budget']:,} руб. | {p['title'][:55]}")

    print(f"\nОткликаемся на первый проект...")
    success = await system.respond(projects[0])

    if success:
        today = datetime.now().date()
        count = len([r for r in system.responded
                     if datetime.fromisoformat(r['time']).date() == today])
        print(f"\nОткликов сегодня: {count}")
        print("ГОТОВО!")
    else:
        print("Не отправлено. Смотри скриншоты data/")

if __name__ == '__main__':
    asyncio.run(main())
