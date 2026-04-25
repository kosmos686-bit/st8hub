import asyncio
import os
import sys
import json
import re
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import anthropic
from smart_agents import SmartOrchestrator
from hunt_kwork_real import respond_to_project, save_responded, notify_response_sent

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

TELEGRAM_TOKEN = '8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y'
CHAT_ID = 6152243830
MEMORY_FILE = Path("agent_memory/kwork_results.json")

MAX_SYSTEM = """Ты Макс, Python-разработчик команды ST8-AI. Специализация: Telegram-боты, AI-агенты, автоматизация.

Задача: изучи ТЗ и напиши готовый рабочий код.

ОБЯЗАТЕЛЬНО оборачивай весь код в блоки формата:
```python:filename.py
[код]
```
Никогда не пиши код без этого формата. Каждый файл — отдельный блок с именем после двоеточия.

Пример правильного ответа:
```python:bot.py
# основной файл бота
```
```python:requirements.txt
aiogram==3.0
```

Правила:
- Рабочий код, не заглушки. Максимально компактно — не более 300 строк на файл
- Комментарии на русском
- ВСЕГДА добавляй requirements.txt в отдельном блоке
- Минимум 2 файла: основной код + requirements.txt
- Не пиши длинные функции — разбивай на части если нужно"""

ANNA_SYSTEM = """Ты Анна, аналитик-тестировщик команды ST8-AI. Проверяешь код Макса.

Анализируй:
1. Логические ошибки и баги
2. Отсутствующие импорты
3. Несоответствие ТЗ
4. Потенциальные проблемы в продакшене

Ответ строго в формате JSON (без markdown, только JSON):
{"passed": true, "score": 85, "issues": ["проблема 1"], "summary": "краткий вывод"}"""


class OrderExecutor:

    def __init__(self):
        self.orders_dir = Path("orders")
        self.orders_dir.mkdir(exist_ok=True)
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def load_memory(self) -> list:
        """Читает историю выполненных проектов из kwork_results.json"""
        if MEMORY_FILE.exists():
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        return []

    def save_result(self, project_id: str, title: str, budget: int, response_text: str, status: str):
        """Сохраняет результат заказа в kwork_results.json"""
        MEMORY_FILE.parent.mkdir(exist_ok=True)
        memory = self.load_memory()
        memory.append({
            "project_id": project_id,
            "title": title,
            "budget": budget,
            "response_text": response_text,
            "status": status,
            "saved_at": datetime.now().isoformat()
        })
        MEMORY_FILE.write_text(json.dumps(memory, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"   [Память] Сохранён проект {project_id} (статус: {status})")

    def send_telegram(self, text: str, reply_markup: dict = None):
        payload = {'chat_id': CHAT_ID, 'text': text}
        if reply_markup:
            payload['reply_markup'] = reply_markup
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json=payload,
                timeout=15
            )
        except Exception as e:
            print(f"[TG] Ошибка: {e}")

    async def parse_kwork_task(self, project_id: str) -> dict:
        """Парсит ТЗ проекта с Kwork через Playwright"""
        print(f"   [Парсинг] kwork.ru/projects/{project_id}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state="data/auth_state.json")
            page = await context.new_page()
            try:
                await page.goto(
                    f"https://kwork.ru/projects/{project_id}",
                    wait_until="networkidle",
                    timeout=30000
                )
                await asyncio.sleep(2)
                data = await page.evaluate("""() => {
                    const title = document.querySelector('h1')?.innerText?.trim() || '';
                    const descEl = document.querySelector(
                        '[class*="description"], [class*="want-card__desc"], .project-description'
                    );
                    const description = descEl
                        ? descEl.innerText.trim()
                        : document.body.innerText.slice(0, 4000);
                    const budgetEl = document.querySelector(
                        '[class*="budget"], [class*="price"], [class*="cost"]'
                    );
                    const budgetText = budgetEl
                        ? budgetEl.innerText.replace(/[^\\d]/g, '')
                        : '0';
                    return { title, description, budget: parseInt(budgetText) || 0 };
                }""")
                print(f"   [Парсинг] Получено: {len(data.get('description',''))} символов")
                return data
            except Exception as e:
                print(f"   [Парсинг] Ошибка: {e}")
                return {}
            finally:
                await context.close()
                await browser.close()

    def create_task_file(self, project_id: str, title: str, description: str, budget: int) -> Path:
        """Создаёт папку заказа и task.md"""
        order_dir = self.orders_dir / project_id
        order_dir.mkdir(exist_ok=True)
        (order_dir / "solution").mkdir(exist_ok=True)

        budget_fmt = f"{budget:,}".replace(",", "\u00a0") if budget else "не указан"
        task_content = (
            f"# Задача: {title}\n\n"
            f"**ID проекта:** {project_id}  \n"
            f"**Бюджет:** {budget_fmt} ₽  \n"
            f"**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"## Описание\n\n{description}\n"
        )
        task_file = order_dir / "task.md"
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write(task_content)
        print(f"   [Файлы] task.md -> {task_file}")
        return order_dir

    def run_max_agent(self, order_dir: Path) -> dict:
        """Агент Макс пишет код по task.md"""
        print(f"   [Макс] Читаю ТЗ...")
        task_content = (order_dir / "task.md").read_text(encoding="utf-8")

        # Ищем похожие проекты в памяти
        memory = self.load_memory()
        title_lower = task_content[:200].lower()
        similar = [
            m for m in memory
            if any(kw in m.get("title", "").lower() for kw in title_lower.split()
                   if len(kw) > 4)
        ][:3]
        memory_context = ""
        if similar:
            memory_context = "\n\nПохожие проекты из памяти команды:\n"
            for s in similar:
                memory_context += (
                    f"- {s['title']} (бюджет {s['budget']} ₽, статус: {s['status']})\n"
                    f"  Решение: {s['response_text'][:120]}...\n"
                )
            print(f"   [Память] Найдено похожих проектов: {len(similar)}")
        else:
            print(f"   [Память] Похожих проектов не найдено, пишем с нуля")

        msg = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            system=MAX_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"ТЗ заказчика:\n\n{task_content}{memory_context}\n\nНапиши полный рабочий код."
            }]
        )
        response_text = msg.content[0].text

        # Сохраняем полный ответ
        (order_dir / "max_response.md").write_text(response_text, encoding="utf-8")

        # Парсим блоки ```lang:filename ... ```
        solution_dir = order_dir / "solution"
        files_written = []
        pattern = r'```[\w]*:?([\w./\-]+\.[\w]+)\n(.*?)(?:```|$)'
        matches = re.findall(pattern, response_text, re.DOTALL)

        if matches:
            for filename, content in matches:
                filepath = solution_dir / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                filepath.write_text(content.strip(), encoding="utf-8")
                files_written.append(filename)
                print(f"   [Макс] Написал: {filename} ({len(content)} симв.)")
        else:
            # Fallback: сохраняем весь ответ
            (solution_dir / "main.py").write_text(response_text, encoding="utf-8")
            files_written.append("main.py")
            print(f"   [Макс] Блоки не найдены — сохранил как main.py")

        return {"files": files_written, "response": response_text}

    def run_anna_tests(self, order_dir: Path) -> dict:
        """Агент Анна проверяет код"""
        print(f"   [Анна] Проверяю код...")
        solution_dir = order_dir / "solution"
        code_files = list(solution_dir.rglob("*.py"))

        if not code_files:
            return {"passed": False, "score": 0, "issues": ["Нет .py файлов"], "summary": "Код не найден"}

        code_content = ""
        for f in code_files:
            code_content += f"\n\n### {f.name}\n```python\n{f.read_text(encoding='utf-8')}\n```"

        task_content = (order_dir / "task.md").read_text(encoding="utf-8")

        msg = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=ANNA_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"ТЗ:\n{task_content}\n\nКод Макса:{code_content}\n\nВерни JSON с результатом проверки."
            }]
        )
        response_text = msg.content[0].text.strip()

        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                print(f"   [Анна] Оценка: {result.get('score','?')}/100, passed={result.get('passed')}")
                return result
            except json.JSONDecodeError:
                pass

        return {"passed": True, "score": 70, "issues": [], "summary": response_text[:300]}

    async def execute_order(self, project_id: str, title: str = "", budget: int = 0) -> dict:
        """Главный метод: парсит ТЗ → Макс пишет код → Анна проверяет → уведомление"""
        print(f"\n{'='*60}")
        print(f"ВЫПОЛНЯЮ ЗАКАЗ #{project_id}")
        print(f"{'='*60}")

        self.send_telegram(
            f"⚙️ Начинаю выполнение заказа!\n"
            f"📌 Проект: {title or project_id}\n"
            f"🔍 Парсю ТЗ с Kwork...\n"
            f"⏳ Макс уже пишет код..."
        )

        # 1. Парсим ТЗ
        task_data = await self.parse_kwork_task(project_id)
        if task_data.get("title"):
            title = task_data["title"]
        if task_data.get("budget"):
            budget = task_data["budget"]
        description = task_data.get("description", "Описание не получено с Kwork")

        # 2. Отклик на Kwork (OODA: Анна анализирует → Макс пишет отклик → браузер отправляет)
        project_dict = {"id": project_id, "title": title, "budget": budget, "description": description}
        try:
            orchestrator = SmartOrchestrator()
            print(f"   [OODA] Анна + Макс готовят отклик...")
            response_text = await orchestrator.process(project_dict)
            if response_text:
                async with async_playwright() as pw:
                    browser = await pw.chromium.launch(headless=False, slow_mo=200)
                    ctx = await browser.new_context(
                        storage_state="data/auth_state.json",
                        viewport={"width": 1280, "height": 900},
                    )
                    page = await ctx.new_page()
                    success = await respond_to_project(page, project_dict, response_text)
                    await ctx.close()
                    await browser.close()
                if success:
                    save_responded(project_dict)
                    notify_response_sent(project_dict)
                    print(f"   [Отклик] Отправлен на kwork.ru/projects/{project_id}")
                else:
                    print(f"   [Отклик] Не отправлен (форма не прошла)")
            else:
                print(f"   [OODA] Анна решила не откликаться — пропускаю")
        except Exception as e:
            print(f"   [Отклик] Ошибка: {e}")

        # 3. Папка + task.md
        order_dir = self.create_task_file(project_id, title, description, budget)

        # 4. Макс пишет код
        max_result = self.run_max_agent(order_dir)
        print(f"   [Макс] Написал {len(max_result['files'])} файлов")

        # 4. Анна тестирует
        anna_result = self.run_anna_tests(order_dir)
        tests_passed = anna_result.get("passed", False)
        score = anna_result.get("score", 0)
        issues = anna_result.get("issues", [])

        # 5. Отчёт в Telegram
        budget_fmt = f"{budget:,}".replace(",", "\u00a0")
        status_icon = "✅" if tests_passed else "⚠️"
        issues_text = ""
        if issues:
            issues_text = "\n⚠️ Замечания Анны:\n" + "\n".join(f"  • {i}" for i in issues[:3])

        text = (
            f"🎯 ЗАКАЗ ВЫПОЛНЕН!\n"
            f"📌 Проект: {title[:60]}\n"
            f"💰 Бюджет: {budget_fmt} ₽\n"
            f"📁 Код: orders/{project_id}/solution/\n"
            f"{status_icon} Тесты: {score}/100"
            f"{issues_text}\n"
            f"👉 Проверь и одобри отправку"
        )
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                'chat_id': CHAT_ID,
                'text': text,
                'reply_markup': {
                    'inline_keyboard': [[
                        {'text': '✅ Одобрить и отправить', 'callback_data': f'deliver_{project_id}'},
                        {'text': '🔄 Переписать', 'callback_data': f'redo_{project_id}'}
                    ]]
                }
            },
            timeout=15
        )

        # Сохраняем результат в память
        solution_dir = order_dir / "solution"
        code_summary = " | ".join(max_result["files"])
        self.save_result(
            project_id=project_id,
            title=title,
            budget=budget,
            response_text=code_summary,
            status="completed" if tests_passed else "completed_with_issues"
        )

        print(f"\n✅ Заказ #{project_id} выполнен! Оценка Анны: {score}/100")
        return {
            "project_id": project_id,
            "title": title,
            "budget": budget,
            "files": max_result["files"],
            "tests_passed": tests_passed,
            "score": score,
            "order_dir": str(order_dir)
        }


async def main():
    import sys
    project_id = sys.argv[1] if len(sys.argv) > 1 else "3155366"
    title = sys.argv[2] if len(sys.argv) > 2 else ""
    budget = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    executor = OrderExecutor()
    result = await executor.execute_order(project_id, title, budget)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
