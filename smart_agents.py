import asyncio
import os
import re
import requests
import json
from pathlib import Path
from datetime import datetime
import anthropic

MEMORY_FILE = Path("agent_memory/kwork_results.json")

ANNA_SYSTEM = """Ты Анна — аналитик команды ST8-AI на Kwork.

Специализация ST8-AI: Telegram-боты, AI-агенты, Python-автоматизация, интеграции.
Бюджетный диапазон нашей команды: 5 000 – 150 000 ₽.
Команда: Макс (Python-разработчик), Анна (аналитик), Юлия (PM).

Отвечай строго по задаче: кратко, структурированно, без лирики."""

MAX_SYSTEM = """Ты Макс — ведущий Python-разработчик команды ST8-AI.

Стек: python-telegram-bot / aiogram, Claude API / OpenAI, SQLite / PostgreSQL,
FastAPI, Redis, интеграции с iiko / 1С / amoCRM.

Пишешь отклики на Kwork: профессионально, конкретно, с конкретными примерами.
Отклик — не шаблон, а персонализированное предложение под ТЗ заказчика.
Без воды, без «Рады сотрудничеству»."""


def _claude(system: str, user: str, max_tokens: int = 600) -> str:
    """Вспомогательная функция вызова Claude API"""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    return msg.content[0].text.strip()


def _load_memory() -> list:
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    return []


class AnalyzerAgent:
    """Агент Анна — OODA-аналитик проектов Kwork"""

    def __init__(self):
        self.name = "Анна"
        self.role = "📊 Аналитик"
        self.chat_id = 6152243830
        self.token = "8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y"

    def send_telegram(self, message):
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'}
            )
        except:
            pass

    # ── OODA: Observe ─────────────────────────────────────────────────────────
    def ooda_observe(self, project: dict) -> dict:
        """Собирает все доступные данные по проекту"""
        description = project.get("description", "")
        links = re.findall(r'https?://\S+', description)
        budget = project.get("budget", 0)
        print(f"   [Анна/Observe] бюджет={budget}₽, ссылок={len(links)}, описание={len(description)} симв.")
        return {
            "title": project.get("title", ""),
            "budget": budget,
            "buyer": project.get("buyer", ""),
            "description": description,
            "links": links,
            "has_description": len(description) > 50,
        }

    # ── OODA: Orient ──────────────────────────────────────────────────────────
    def ooda_orient(self, obs: dict) -> dict:
        """Анализирует проект через Claude: подходит ли нам, риски, категория"""
        memory = _load_memory()
        similar = [m for m in memory
                   if any(w in m.get("title","").lower()
                          for w in obs["title"].lower().split() if len(w) > 4)][:2]
        memory_ctx = ""
        if similar:
            memory_ctx = "\n\nПохожие проекты из нашей истории:\n" + "\n".join(
                f"- {s['title']} | {s['budget']}₽ | статус: {s['status']}" for s in similar
            )

        prompt = (
            f"Проект: {obs['title']}\n"
            f"Бюджет: {obs['budget']} ₽\n"
            f"Заказчик: {obs['buyer']}\n"
            f"Описание: {obs['description'][:600]}\n"
            f"Ссылок в ТЗ: {len(obs['links'])}"
            f"{memory_ctx}\n\n"
            f"Оцени:\n"
            f"1. Категория проекта (бот/AI-агент/автоматизация/парсер/другое)\n"
            f"2. Подходит ли нашей команде? (да/нет/частично)\n"
            f"3. Топ-3 требования из ТЗ\n"
            f"4. Риски (1-2 пункта)\n"
            f"Ответь кратко, по пунктам."
        )
        print(f"   [Анна/Orient] Запрашиваю Claude...")
        raw = _claude(ANNA_SYSTEM, prompt, max_tokens=400)
        print(f"   [Анна/Orient] {raw[:80]}...")
        return {"raw": raw, "similar_count": len(similar)}

    # ── OODA: Decide ──────────────────────────────────────────────────────────
    def ooda_decide(self, orientation: dict, obs: dict) -> dict:
        """Принимает решение: откликаться или нет, стратегия отклика"""
        prompt = (
            f"На основе анализа проекта:\n{orientation['raw']}\n\n"
            f"Бюджет: {obs['budget']} ₽\n\n"
            f"Реши:\n"
            f"1. ОТКЛИКАТЬСЯ: да / нет / с оговорками\n"
            f"2. Стратегия отклика: что подчеркнуть (1-2 предложения)\n"
            f"3. Ключевое УТП для этого заказчика\n"
            f"Кратко и конкретно."
        )
        print(f"   [Анна/Decide] Принимаю решение...")
        raw = _claude(ANNA_SYSTEM, prompt, max_tokens=250)
        should_respond = "нет" not in raw.lower().split("\n")[0].lower()
        print(f"   [Анна/Decide] Откликаться: {should_respond}")
        return {"raw": raw, "should_respond": should_respond}

    # ── OODA: Act ─────────────────────────────────────────────────────────────
    def ooda_act(self, decision: dict, orientation: dict, obs: dict) -> dict:
        """Формирует структурированный результат для передачи Максу"""
        result = {
            "type": obs["title"][:40],
            "requirements": [],
            "links": obs["links"],
            "orientation": orientation["raw"],
            "decision": decision["raw"],
            "should_respond": decision["should_respond"],
            "budget": obs["budget"],
            "buyer": obs["buyer"],
        }
        # Извлекаем requirements из ориентирования
        for line in orientation["raw"].split("\n"):
            if line.strip().startswith(("•", "-", "✅", "3.")):
                result["requirements"].append(line.strip()[:80])
        print(f"   [Анна/Act] Передаю Максу. Требований: {len(result['requirements'])}")
        return result

    async def analyze(self, project: dict) -> dict:
        """OODA-цикл анализа проекта"""
        print(f"\n📊 АННА / OODA-ЦИКЛ:")

        obs = self.ooda_observe(project)
        orientation = self.ooda_orient(obs)
        decision = self.ooda_decide(orientation, obs)
        result = self.ooda_act(decision, orientation, obs)

        req_lines = "\n".join(f"  • {r}" for r in result["requirements"][:4]) or "  • Уточнить у заказчика"
        decide_first_line = decision["raw"].split("\n")[0][:100]

        self.send_telegram(
            f"📊 <b>АННА — OODA АНАЛИЗ</b>\n\n"
            f"📋 <b>Проект:</b> {project['title'][:60]}\n"
            f"💰 <b>Бюджет:</b> {project['budget']:,} ₽\n\n"
            f"🔍 <b>Ориентирование:</b>\n{orientation['raw'][:300]}\n\n"
            f"✅ <b>Решение:</b> {decide_first_line}\n\n"
            f"📋 <b>Требования:</b>\n{req_lines}\n\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')} → передаю Максу"
        )
        return result


class WriterAgent:
    """Агент Макс — OODA-разработчик откликов на Kwork"""

    def __init__(self):
        self.name = "Макс"
        self.role = "✍️ Разработчик"
        self.chat_id = 6152243830
        self.token = "8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y"

    def send_telegram(self, message):
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'}
            )
        except:
            pass

    # ── OODA: Observe ─────────────────────────────────────────────────────────
    def ooda_observe(self, project: dict, analysis: dict) -> dict:
        """Читает ТЗ и память похожих проектов"""
        memory = _load_memory()
        keywords = project.get("title","").lower().split()
        similar = [m for m in memory
                   if any(k in m.get("title","").lower() for k in keywords if len(k) > 4)][:3]
        print(f"   [Макс/Observe] памяти: {len(memory)}, похожих: {len(similar)}")
        return {
            "title": project.get("title",""),
            "budget": project.get("budget", 0),
            "description": project.get("description",""),
            "analysis": analysis,
            "similar_projects": similar,
        }

    # ── OODA: Orient ──────────────────────────────────────────────────────────
    def ooda_orient(self, obs: dict) -> dict:
        """Планирует архитектуру решения через Claude"""
        memory_ctx = ""
        if obs["similar_projects"]:
            memory_ctx = "\nПохожие выполненные проекты:\n" + "\n".join(
                f"- {s['title']} → {s['response_text'][:100]}" for s in obs["similar_projects"]
            )

        prompt = (
            f"Проект заказчика: {obs['title']}\n"
            f"Бюджет: {obs['budget']} ₽\n"
            f"Описание: {obs['description'][:500]}\n"
            f"Анализ Анны:\n{obs['analysis'].get('orientation','')[:300]}"
            f"{memory_ctx}\n\n"
            f"Спланируй архитектуру решения:\n"
            f"1. Основные компоненты (2-3 пункта)\n"
            f"2. Ключевые технические задачи\n"
            f"3. Что выгодно подчеркнуть заказчику"
        )
        print(f"   [Макс/Orient] Планирую архитектуру...")
        raw = _claude(MAX_SYSTEM, prompt, max_tokens=400)
        print(f"   [Макс/Orient] {raw[:80]}...")
        return {"raw": raw}

    # ── OODA: Decide ──────────────────────────────────────────────────────────
    def ooda_decide(self, orientation: dict, obs: dict) -> dict:
        """Выбирает стек и подход к написанию отклика"""
        prompt = (
            f"Архитектура проекта:\n{orientation['raw']}\n\n"
            f"Бюджет: {obs['budget']} ₽\n\n"
            f"Выбери:\n"
            f"1. Технический стек (конкретные библиотеки/фреймворки)\n"
            f"2. Срок выполнения (реалистичный)\n"
            f"3. Главный аргумент почему выбрать нашу команду\n"
            f"Кратко, 3 пункта."
        )
        print(f"   [Макс/Decide] Выбираю стек...")
        raw = _claude(MAX_SYSTEM, prompt, max_tokens=200)
        print(f"   [Макс/Decide] {raw[:80]}...")
        return {"raw": raw}

    # ── OODA: Act ─────────────────────────────────────────────────────────────
    def ooda_act(self, decision: dict, orientation: dict, obs: dict) -> str:
        """Пишет финальный отклик через Claude"""
        prompt = (
            f"Напиши ТЕХНИЧЕСКУЮ ЧАСТЬ отклика на Kwork для проекта:\n"
            f"Название: {obs['title']}\n"
            f"Бюджет: {obs['budget']} ₽\n"
            f"Описание: {obs['description'][:400]}\n\n"
            f"Архитектура решения:\n{orientation['raw'][:300]}\n\n"
            f"Стек и сроки:\n{decision['raw']}\n\n"
            f"Требования (от Анны):\n{obs['analysis'].get('decision','')[:200]}\n\n"
            f"Правила:\n"
            f"- Начни с конкретного понимания задачи заказчика\n"
            f"- Укажи что именно сделаем (2-3 пункта)\n"
            f"- Назови стек и срок\n"
            f"- Заверши призывом обсудить детали\n"
            f"- Объём: 5-8 предложений\n"
            f"- БЕЗ «Рады сотрудничеству» и шаблонных фраз\n"
            f"- НЕ добавляй приветствие и подпись — только техническая часть"
        )
        print(f"   [Макс/Act] Пишу отклик...")
        tech_part = _claude(MAX_SYSTEM, prompt, max_tokens=500)
        tech_part = tech_part.replace("instagram", "запрещёнограмм").replace("Instagram", "Запрещёнограмм")
        response_text = (
            "Привет! Я Юлия, руководитель команды разработчиков.\n\n"
            "Анна изучила вашу задачу и передала Максу — вот наше решение:\n\n"
            f"{tech_part}\n\n"
            "Команда:\n"
            "🔍 Анна — проанализировала задачу\n"
            "💻 Макс — разработает решение\n"
            "📋 Юлия — управляю проектом\n\n"
            "С уважением, Юлия"
        )
        print(f"   [Макс/Act] Отклик: {len(response_text)} симв.")
        return response_text

    def write_response(self, project: dict, analysis: dict) -> str:
        """OODA-цикл написания отклика"""
        print(f"\n✍️ МАКС / OODA-ЦИКЛ:")

        obs = self.ooda_observe(project, analysis)
        orientation = self.ooda_orient(obs)
        decision = self.ooda_decide(orientation, obs)
        response_text = self.ooda_act(decision, orientation, obs)

        self.send_telegram(
            f"✍️ <b>МАКС — OODA ОТКЛИК</b>\n\n"
            f"📋 <b>Проект:</b> {project['title'][:60]}\n"
            f"💰 <b>Бюджет:</b> {project['budget']:,} ₽\n\n"
            f"🏗 <b>Архитектура:</b>\n{orientation['raw'][:200]}\n\n"
            f"⚙️ <b>Стек/Сроки:</b>\n{decision['raw'][:150]}\n\n"
            f"📝 <b>Отклик:</b>\n{response_text[:400]}\n\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')} → готов к отправке"
        )
        return response_text


class SmartOrchestrator:
    """Оркестратор: управляет OODA-агентами Анна → Макс"""

    def __init__(self):
        self.analyzer = AnalyzerAgent()
        self.writer = WriterAgent()
        self.chat_id = 6152243830
        self.token = "8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y"

    def send_telegram(self, message):
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'}
            )
        except:
            pass

    def load_memory(self) -> list:
        if MEMORY_FILE.exists():
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        return []

    def save_result(self, project_id: str, title: str, budget: int, response_text: str, status: str):
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
        print(f"   [Память] Сохранён проект {project_id} ({status})")

    async def process(self, project: dict) -> str:
        """Запускает полный OODA-конвейер: Анна → Макс"""
        print(f"\n{'='*70}")
        print(f"🤖 OODA-КОНВЕЙЕР: {project['title'][:50]}")
        print(f"{'='*70}")

        self.send_telegram(
            f"🚀 <b>OODA-КОНВЕЙЕР ЗАПУЩЕН</b>\n\n"
            f"📋 {project['title'][:60]}\n"
            f"💰 {project['budget']:,} ₽\n\n"
            f"🔄 Анна: Observe → Orient → Decide → Act..."
        )

        # Анна: OODA-анализ
        analysis = await self.analyzer.analyze(project)

        if not analysis.get("should_respond", True):
            msg = (
                f"🚫 <b>АННА: НЕ ОТКЛИКАЕМСЯ</b>\n\n"
                f"📋 {project['title'][:60]}\n"
                f"💡 {analysis.get('decision','')[:200]}"
            )
            self.send_telegram(msg)
            print(f"   [Оркестратор] Анна решила не откликаться.")
            return ""

        await asyncio.sleep(1)

        # Макс: OODA-написание
        response = self.writer.write_response(project, analysis)

        # Итог
        self.send_telegram(
            f"✅ <b>OODA-КОНВЕЙЕР ЗАВЕРШЁН</b>\n\n"
            f"📋 <b>Проект:</b> {project['title'][:60]}\n"
            f"💰 <b>Бюджет:</b> {project['budget']:,} ₽\n"
            f"👤 <b>Заказчик:</b> {project.get('buyer','?')}\n\n"
            f"✅ Отклик готов к отправке на Kwork\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )

        self.save_result(
            project_id=str(project.get("id", "unknown")),
            title=project["title"],
            budget=project["budget"],
            response_text=response[:300],
            status="responded"
        )

        return response


async def main():
    test_project = {
        'id': '903039',
        'title': 'Создать Telegram-бота для записи клиентов с интеграцией amoCRM',
        'budget': 25000,
        'buyer': 'test_buyer',
        'description': (
            'Нужен бот в Telegram для записи клиентов. '
            'Бот должен показывать расписание, принимать запись и передавать данные в amoCRM. '
            'Уведомления для администратора. Работа 24/7.'
        )
    }

    orchestrator = SmartOrchestrator()
    result = await orchestrator.process(test_project)
    print(f"\nФинальный отклик:\n{result}")


if __name__ == '__main__':
    asyncio.run(main())
