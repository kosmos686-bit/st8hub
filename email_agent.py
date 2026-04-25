import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic
import os

GMAIL = "kosmos686@gmail.com"
GMAIL_PASSWORD = "repdi0-bucbEm-nytnuq"
TOKEN = "8797018278:AAGHwcZK5bvA2QuVG5Jx0FB__8hbqxpvip0"
CHAT_ALEX = 6152243830
AGENTS_DIR = r"C:\Users\user\.claude\agents"

def tg(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ALEX, "text": msg[:4000], "parse_mode": "HTML"},
        timeout=10
    )

def load_agent(name):
    path = os.path.join(AGENTS_DIR, f"{name}.md")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    return ""

def clean_text(text):
    import re
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def run_agent(system, task, model="claude-haiku-4-5-20251001"):
    client = anthropic.Anthropic()
    r = client.messages.create(
        model=model,
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": task}]
    )
    return r.content[0].text

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = f"ST8-AI <{GMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL, GMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        tg(f"❌ Ошибка email: {e}")
        return False

def process_lead(company, vertical, contact_email, context=""):
    """Полный цикл: анализ → КП → отправка"""
    
    tg(f"🤖 Обрабатываю лид: {company}")

    # Шаг 1 — анализ клиента
    discovery = load_agent("sales-discovery-coach")
    analysis = run_agent(
        discovery,
        f"Проанализируй клиента для ST8-AI:\nКомпания: {company}\nВертикаль: {vertical}\nКонтекст: {context}\n\nОпредели: боли, потребности, приоритетное предложение ST8-AI. Коротко, 3-4 пункта."
    )
    tg(f"🔍 Анализ {company}:\n{analysis}")

    # Шаг 2 — КП
    proposal = load_agent("sales-proposal-strategist")
    kp = clean_text(run_agent(
        proposal,
        f"Напиши КП для {company} ({vertical}).\nАнализ клиента: {analysis}\n\nКП должно быть: 3 абзаца, конкретные цифры, призыв к действию. Стиль: деловой, без воды.",
        model="claude-sonnet-4-6"
    )

    # Шаг 3 — проверка
    checker = load_agent("testing-reality-checker")
    check = run_agent(checker, f"Проверь КП на качество:\n{kp}\n\nВердикт одним словом: ОТПРАВЛЯТЬ или ДОРАБОТАТЬ. Причина — одно предложение.")

    tg(f"✅ Проверка: {check}")

    # Шаг 4 — тема письма
    subject = f"AI-автоматизация для {company} — ST8-AI"

    # Шаг 5 — отправка
    if contact_email:
        ok = send_email(contact_email, subject, kp)
        if ok:
            tg(f"📧 КП отправлено на {contact_email}\n\n{kp[:500]}...")
        else:
            tg(f"📋 КП готово (email не отправлен):\n\n{kp[:1000]}")
    else:
        tg(f"📋 КП готово (нет email):\n\n{kp[:1000]}")

    return kp

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        company = sys.argv[1]
        email = sys.argv[2]
        vertical = sys.argv[3] if len(sys.argv) > 3 else "B2B"
        process_lead(company=company, vertical=vertical, contact_email=email)
    else:
        process_lead(company="Тест", vertical="HoReCa", contact_email="")