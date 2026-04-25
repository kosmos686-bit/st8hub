import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import re
from dotenv import load_dotenv
import anthropic

load_dotenv()

AUTH_STATE = "data/auth_state.json"

class KworkAutoSystem:
    def __init__(self):
        self.responded_file = Path("data/responded.json")
        self.responded_file.parent.mkdir(exist_ok=True)
        self.responded = self._load_responded()
        self.daily_limit = 5

    def _load_responded(self):
        if self.responded_file.exists():
            try:
                return json.loads(self.responded_file.read_text(encoding='utf-8'))
            except Exception:
                return []
        return []

    def _save_responded(self, proj_id):
        self.responded.append({'id': str(proj_id), 'time': datetime.now().isoformat()})
        self.responded_file.write_text(
            json.dumps(self.responded, indent=2, ensure_ascii=False), encoding='utf-8'
        )

    def _already_responded(self, proj_id):
        return str(proj_id) in [str(r['id']) for r in self.responded]

    def _today_count(self):
        today = datetime.now().date()
        return len([r for r in self.responded
                    if datetime.fromisoformat(r['time']).date() == today])

    def generate_reply(self, title: str, description: str, budget: int) -> str:
        """Генерирует персонализированный отклик через Claude"""
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            budget_fmt = f"{budget:,}".replace(",", "\u00a0") if budget else "?"
            msg = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                system=(
                    "Ты Юлия, руководитель команды ST8-AI на Kwork. "
                    "Пишешь отклик на проект. Команда: Макс (Python/AI разработчик), "
                    "Анна (аналитик), Юлия (PM). "
                    "Стиль: профессионально, конкретно, 3-5 предложений. "
                    "Покажи что прочитал задание. Без шаблонных фраз."
                ),
                messages=[{
                    "role": "user",
                    "content": (
                        f"Проект: {title}\n"
                        f"Описание: {description[:500]}\n"
                        f"Бюджет: {budget_fmt} ₽\n\n"
                        f"Напиши отклик от Юлии."
                    )
                }]
            )
            return msg.content[0].text
        except Exception as e:
            print(f"   [Claude] Ошибка: {e}")
            return (
                "Привет! Изучила ваш проект — готовы взяться.\n\n"
                "Наша команда (Python разработчик + аналитик) делала похожие задачи. "
                "Работаем через безопасную сделку Kwork. Когда удобно обсудить детали?"
            )

    async def find_projects(self, page_num: int = 1):
        """Ищет проекты с авторизацией"""
        print(f"🔍 Ищу проекты (стр. {page_num})...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # С авторизацией — видим проекты как залогиненный пользователь
            context = await browser.new_context(storage_state=AUTH_STATE)
            page = await context.new_page()

            try:
                await page.goto(
                    f"https://kwork.ru/projects?page={page_num}",
                    wait_until="domcontentloaded",
                    timeout=30000
                )
                await page.wait_for_timeout(3000)

                # Извлекаем проекты через DOM
                projects_raw = await page.evaluate("""() => {
                    const result = [];
                    const cards = document.querySelectorAll(
                        '[class*="project-card"], [class*="want-card"], .wants-card, [data-id]'
                    );
                    cards.forEach(card => {
                        const link = card.querySelector('a[href*="/projects/"]');
                        if (!link) return;
                        const match = link.href.match(/\\/projects\\/(\\d+)/);
                        if (!match) return;
                        const id = match[1];
                        const title = (
                            card.querySelector('[class*="title"], h2, h3')?.innerText || ''
                        ).trim().slice(0, 200);
                        const desc = (
                            card.querySelector('[class*="desc"], [class*="text"], p')?.innerText || ''
                        ).trim().slice(0, 500);
                        const priceEl = card.querySelector('[class*="price"], [class*="budget"]');
                        const priceMatch = priceEl ? priceEl.innerText.match(/\\d[\\d\\s]*/) : null;
                        const budget = priceMatch ? parseInt(priceMatch[0].replace(/\\s/g, '')) : 0;
                        if (id && title) {
                            result.push({ id, title, description: desc, budget, url: link.href });
                        }
                    });
                    return result;
                }""")

                # Если DOM не дал результатов — fallback через regex
                if not projects_raw:
                    print("   [DOM] Карточки не найдены, пробую regex...")
                    content = await page.content()
                    ids = list(dict.fromkeys(re.findall(r'/projects/(\d+)', content)))
                    amounts = re.findall(r'(\d[\d\s]{1,8})\s*₽', content)
                    for i, proj_id in enumerate(ids[:15]):
                        budget = int(amounts[i].replace(' ', '')) if i < len(amounts) else 0
                        projects_raw.append({
                            'id': proj_id,
                            'title': f'Проект #{proj_id}',
                            'description': '',
                            'budget': budget,
                            'url': f'https://kwork.ru/projects/{proj_id}'
                        })

                await context.close()
                await browser.close()

                # Фильтруем уже отвеченные
                fresh = [p for p in projects_raw if not self._already_responded(p['id'])]
                print(f"   Найдено: {len(projects_raw)}, новых: {len(fresh)}")
                return fresh

            except Exception as e:
                print(f"   [find_projects] Ошибка: {e}")
                await context.close()
                await browser.close()
                return []

    async def respond_to_project(self, project: dict) -> bool:
        """Отправляет отклик на проект с авторизацией"""
        print(f"\n📤 Отклик на проект #{project['id']} | {project['budget']} ₽")
        print(f"   {project['url']}")

        # Генерируем умный ответ
        reply_text = self.generate_reply(
            project['title'],
            project.get('description', ''),
            project['budget']
        )
        print(f"   [Claude] Ответ: {reply_text[:80]}...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            # ВАЖНО: с авторизацией!
            context = await browser.new_context(storage_state=AUTH_STATE)
            page = await context.new_page()

            try:
                await page.goto(
                    project['url'],
                    wait_until="domcontentloaded",
                    timeout=30000
                )
                await page.wait_for_timeout(3000)

                # Шаг 1: найти и кликнуть кнопку "Предложить услугу" / "Откликнуться"
                offer_btn = None
                btn_selectors = [
                    'button:has-text("Предложить")',
                    'button:has-text("Откликнуться")',
                    'a:has-text("Предложить")',
                    '[class*="want-btn"]',
                    '[class*="offer-btn"]',
                    '[class*="respond"]',
                ]
                for sel in btn_selectors:
                    try:
                        el = page.locator(sel).first
                        if await el.count() > 0:
                            offer_btn = el
                            print(f"   ✅ Кнопка найдена: {sel}")
                            break
                    except Exception:
                        continue

                if not offer_btn:
                    print("   ❌ Кнопка 'Предложить' не найдена")
                    # Скриншот для диагностики
                    await page.screenshot(path="data/debug_offer.png")
                    print("   📸 Скриншот: data/debug_offer.png")
                    await context.close()
                    await browser.close()
                    return False

                await offer_btn.click()
                await page.wait_for_timeout(2000)

                # Шаг 2: заполнить textarea
                textarea = None
                for sel in ['textarea', '[contenteditable="true"]']:
                    try:
                        el = page.locator(sel).first
                        if await el.count() > 0:
                            textarea = el
                            break
                    except Exception:
                        continue

                if not textarea:
                    print("   ❌ Поле ввода не найдено")
                    await page.screenshot(path="data/debug_textarea.png")
                    await context.close()
                    await browser.close()
                    return False

                await textarea.click()
                await textarea.fill(reply_text)
                await page.wait_for_timeout(500)
                print("   ✅ Текст введён")

                # Шаг 3: найти и нажать кнопку отправки
                send_btn = None
                send_selectors = [
                    'button:has-text("Отправить")',
                    'button:has-text("Предложить")',
                    'button[type="submit"]',
                    '[class*="send-btn"]',
                    '[class*="submit"]',
                ]
                for sel in send_selectors:
                    try:
                        el = page.locator(sel).first
                        if await el.count() > 0:
                            send_btn = el
                            print(f"   ✅ Кнопка отправки: {sel}")
                            break
                    except Exception:
                        continue

                if send_btn:
                    await send_btn.click()
                    await page.wait_for_timeout(3000)
                    self._save_responded(project['id'])
                    print(f"   ✅ ОТКЛИК ОТПРАВЛЕН! #{project['id']}")
                    await context.close()
                    await browser.close()
                    return True
                else:
                    print("   ❌ Кнопка отправки не найдена")
                    await page.screenshot(path="data/debug_send.png")
                    await context.close()
                    await browser.close()
                    return False

            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
                try:
                    await page.screenshot(path="data/debug_error.png")
                except Exception:
                    pass
                await context.close()
                await browser.close()
                return False


async def main():
    print("=" * 60)
    print("ST8 ОХОТА НА ПРОЕКТЫ v2")
    print("=" * 60)

    system = KworkAutoSystem()

    today_count = system._today_count()
    remaining = system.daily_limit - today_count
    print(f"Откликов сегодня: {today_count}/{system.daily_limit} (осталось: {remaining})")

    if remaining <= 0:
        print("⛔ Дневной лимит исчерпан")
        return

    projects = await system.find_projects(page_num=1)

    if not projects:
        print("\n❌ Нет новых проектов")
        return

    print(f"\n✅ Найдено новых проектов: {len(projects)}\n")
    for i, proj in enumerate(projects[:5], 1):
        print(f"  {i}. {proj['budget']:,} ₽ | {proj['title'][:60]} | {proj['url']}")

    # Откликаемся на первые N в рамках лимита
    success_count = 0
    for proj in projects[:remaining]:
        ok = await system.respond_to_project(proj)
        if ok:
            success_count += 1
            await asyncio.sleep(10)  # пауза между откликами

    print(f"\n{'='*60}")
    print(f"✅ Отправлено откликов: {success_count}")
    print(f"Всего сегодня: {system._today_count()}/{system.daily_limit}")


if __name__ == '__main__':
    asyncio.run(main())
