"""
Dima Agent - генерирует шаблоны кода для ботов
"""
import asyncio
from pathlib import Path
from anthropic import Anthropic

client = Anthropic()

class DimaAgent:
    def __init__(self):
        self.output_dir = Path("data/generated_bots")
        self.output_dir.mkdir(exist_ok=True)
    
    async def generate_bot(self, project_id, title, requirements, budget):
        print(f"💻 Dima генерирует код для {title}...")
        
        prompt = f"""Ты Дима - разработчик Telegram ботов на Python.

ЗАДАЧА:
{requirements}

БЮДЖЕТ: {budget}₽

Напиши ГОТОВЫЙ шаблон bot.py для aiogram 3.4:
- Основные handlers
- FSM состояния
- База данных SQLite
- Готово к расширению

Код ТОЛЬКО (без объяснений):"""
        
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        code = message.content[0].text
        if code.startswith("```python"):
            code = code[9:]
        if code.endswith("```"):
            code = code[:-3]
        
        project_dir = self.output_dir / project_id
        project_dir.mkdir(exist_ok=True)
        (project_dir / "bot.py").write_text(code, encoding='utf-8')
        (project_dir / "requirements.txt").write_text(
            "aiogram==3.4.1\npython-dotenv==1.0.0\naiosqlite==0.19.0\n"
        )
        print(f"✅ Код сохранён в {project_dir}")
        return str(project_dir)

if __name__ == "__main__":
    asyncio.run(asyncio.coroutine(lambda: print("Dima Agent готов!"))())