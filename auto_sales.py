import anthropic
import requests
import json
import os
from datetime import datetime

TOKEN = "8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y"
CHAT_ALEX = 6152243830
AGENTS_DIR = r"C:\Users\user\.claude\agents"
BASE_DIR = r"C:\st8-workspace"

def tg(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ALEX, "text": msg},
        timeout=10
    )

def load_agent(name):
    path = os.path.join(AGENTS_DIR, f"{name}.md")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    return ""

def load_hub_clients():
    """Загружает список клиентов из Hub"""
    try:
        hub_path = os.path.join(BASE_DIR, "st8-memory-bank", "clientPipeline.md")
        if os.path.exists(hub_path):
            return open(hub_path, encoding="utf-8").read()[:3000]
    except:
        pass
    return ""

def run_agent(agent_prompt, task, model="claude-haiku-4-5-20251001"):
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        system=agent_prompt,
        messages=[{"role": "user", "content": task}]
    )
    return response.content[0].text

def auto_sales_cycle():
    tg("🤖 AUTO SALES запущен")
    
    # Шаг 1 — найти перспективных клиентов
    outbound = load_agent("sales-outbound-strategist")
    hub_data = load_hub_clients()
    
    prospects = run_agent(
        outbound,
        f"Проанализируй pipeline клиентов ST8-AI и выбери ТОП-3 для немедленного контакта:\n{hub_data}\n\nДля каждого: имя, причина приоритета, следующий шаг."
    )
    
    tg(f"🎯 TOP-3 клиента:\n{prospects}")
    
    # Шаг 2 — написать КП для первого клиента
    proposal = load_agent("sales-proposal-strategist")
    kp = run_agent(
        proposal,
        f"Напиши краткое КП (3-4 абзаца) для ST8-AI на основе этих клиентов:\n{prospects}\n\nФокус: AI-автоматизация, ROI, быстрое внедрение.",
        model="claude-sonnet-4-6"
    )
    
    tg(f"📄 КП готово:\n{kp[:1000]}")
    
    # Шаг 3 — проверка
    checker = load_agent("testing-reality-checker")
    check = run_agent(
        checker,
        f"Проверь это КП на production-ready:\n{kp}\n\nКраткий вердикт: готово/не готово и почему."
    )
    
    tg(f"✅ Проверка:\n{check}")

if __name__ == "__main__":
    auto_sales_cycle()