"""
Max Agent - ведёт диалоги с клиентами через Claude API
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from anthropic import Anthropic

client = Anthropic()

class MaxAgent:
    def __init__(self):
        self.state_file = Path("data/max_state.json")
        self.state_file.parent.mkdir(exist_ok=True)
        self.processed = self._load_state()
    
    def _load_state(self):
        if not self.state_file.exists():
            return {}
        try:
            return json.loads(self.state_file.read_text())
        except:
            return {}
    
    def _save_state(self):
        self.state_file.write_text(json.dumps(self.processed, indent=2))
    
    async def generate_response(self, client_message, project_title, budget):
        prompt = f"""Ты Максим - опытный разработчик ботов для бизнеса.

КЛИЕНТ СПРОСИЛ:
{client_message}

ПРОЕКТ: {project_title}
БЮДЖЕТ: {budget}₽

Ответь коротко и по делу (2-3 предложения):
- Если вопрос о цене - назови цену (80% от бюджета)
- Если о сроках - 5-7 дней
- Если ТЗ не ясна - спроси уточнения
- Если согласен работать - предложи начать

Только текст ответа (без кавычек):"""
        
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()

if __name__ == "__main__":
    asyncio.run(asyncio.coroutine(lambda: print("Max Agent готов!"))())