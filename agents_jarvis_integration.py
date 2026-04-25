"""
agents_jarvis_integration.py — Интеграция Макса и Димы с Jarvis
Команды: /макс, /дима, /агенты
"""
import os, re, json, time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

try:
    from max_agent import MaxAgent
    _max = MaxAgent()
except Exception as e:
    _max = None
    print(f'[agents] MaxAgent не загружен: {e}')

try:
    from dima_agent import DimaAgent
    _dima = DimaAgent()
except Exception as e:
    _dima = None
    print(f'[agents] DimaAgent не загружен: {e}')

_DIALOGS_PATH = Path(__file__).parent / 'data' / 'agent_dialogs.json'

def _save_dialog(agent, user_input, result):
    _DIALOGS_PATH.parent.mkdir(exist_ok=True)
    try:
        data = json.loads(_DIALOGS_PATH.read_text(encoding='utf-8')) if _DIALOGS_PATH.exists() else []
    except Exception:
        data = []
    data.append({'ts': datetime.now().isoformat(timespec='seconds'),
                 'agent': agent, 'input': user_input[:200], 'result': result[:500]})
    _DIALOGS_PATH.write_text(json.dumps(data[-200:], ensure_ascii=False, indent=2), encoding='utf-8')

async def handle_max_command(text):
    if _max is None:
        return '❌ Макс не загружен. Проверь max_agent.py'
    client_msg = re.sub(r'^/макс\s*', '', text.strip(), flags=re.I).strip()
    budget_m = re.search(r'бюджет[:\s]+(\d+)', client_msg, re.I)
    budget = int(budget_m.group(1)) if budget_m else 5000
    if budget_m:
        client_msg = client_msg[:budget_m.start()] + client_msg[budget_m.end():]
    if not client_msg.strip():
        return '🤖 *Макс готов!*\nПример: `/макс Сколько стоит бот для записи?`'
    try:
        reply = await _max.generate_response(client_msg.strip(), 'Разработка Telegram бота', budget)
        _save_dialog('max', client_msg, reply)
        return f'💬 *Макс отвечает:*\n\n{reply}'
    except Exception as exc:
        return f'❌ Ошибка Макса: {exc}'

async def handle_dima_command(text):
    if _dima is None:
        return '❌ Дима не загружен. Проверь dima_agent.py'
    task = re.sub(r'^/дима\s*', '', text.strip(), flags=re.I).strip()
    if not task:
        return '💻 *Дима готов!*\nПример: `/дима бот для записи к врачу с оплатой`'
    budget_m = re.search(r'бюджет[:\s]+(\d+)', task, re.I)
    budget = int(budget_m.group(1)) if budget_m else 5000
    project_id = f'proj_{re.sub(r"[^a-zA-Z0-9]", "_", task[:20])}_{int(time.time())}'
    try:
        output_dir = await _dima.generate_bot(project_id, task[:50], task, budget)
        _save_dialog('dima', task, f'Код в {output_dir}')
        return f'✅ *Дима написал код!*\n📁 `{output_dir}`\nФайлы: `bot.py`, `requirements.txt`'
    except Exception as exc:
        return f'❌ Ошибка Димы: {exc}'

def agents_status():
    max_s  = '✅ Готов' if _max  else '❌ Не загружен'
    dima_s = '✅ Готов' if _dima else '❌ Не загружен'
    return (f'🤖 *Агенты:*\n💬 Макс: {max_s}\n💻 Дима: {dima_s}\n\n'
            f'Команды:\n`/макс <сообщение клиента>`\n`/дима <задача>`\n`/агенты`')

def is_agent_command(text):
    low = text.strip().lower()
    return (low.startswith('/макс') or low.startswith('/дима') or low.startswith('/агенты'))

async def handle_agents_command(text, notify_func=None):
    low = text.strip().lower()
    if low.startswith('/агенты'):
        return agents_status()
    if low.startswith('/макс'):
        return await handle_max_command(text)
    if low.startswith('/дима'):
        return await handle_dima_command(text)
    return '❓ Неизвестная команда.'