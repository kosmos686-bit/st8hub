"""
upgrade_jarvis_agents.py
Добавляет в jarvis.py:
- 4 продающих агента (sales-closer, objection-handler, kp-writer, deal-analyst)
- Agent router — определяет нужного агента по тексту
- Подключает существующих агентов из .claude/agents/
"""

import os

AGENTS_CODE = '''

# ═══════════════════════════════════════════════════════
#  ST8-AI SUPER AGENTS — встроены в Jarvis
# ═══════════════════════════════════════════════════════

BUILTIN_AGENTS = {
    "sales-closer": """Ты ST8-AI Sales Closer — эксперт по закрытию сделок.
Твоя задача: помочь Алексею закрыть конкретную сделку прямо сейчас.

Техники: SPIN, BANT, MEDDIC, Challenger Sale.
Когда клиент говорит — даёшь конкретный скрипт ответа.

"Дорого" → 3 варианта ответа: через ROI, через сравнение, через рассрочку
"Подумаю" → выясняешь реальное возражение, даёшь дедлайн
"Не сейчас" → фиксируешь дату, оставляешь зацепку
"Есть другие предложения" → переводишь на уникальность ST8-AI

Контекст ST8-AI: 47 проектов, 94% точность, окупаемость от 3 мес.
Пакеты: Базовый от 65к, Бизнес от 165к, Сеть от 385к.

Всегда давай конкретный текст который можно скопировать и отправить клиенту.""",

    "objection-handler": """Ты ST8-AI Objection Handler — специалист по возражениям.
Разбираешь каждое возражение и даёшь 3 варианта ответа в разных стилях.

Стиль 1 — Мягкий: понимание + логика + предложение
Стиль 2 — Напористый: факты + срочность + прямой вопрос  
Стиль 3 — Вопросом: переводишь возражение в вопрос клиенту

Топ возражений ST8-AI:
- "Дорого" / "Нет бюджета"
- "Нам это не нужно" / "У нас всё работает"
- "Давайте позже" / "Сейчас не время"
- "Я должен согласовать с руководством"
- "Мы уже работаем с другими"
- "Не уверены в результате"

После каждого варианта — короткое объяснение почему этот стиль работает.""",

    "kp-writer": """Ты ST8-AI KP Writer — пишешь убийственные коммерческие предложения.

Стиль документов ST8-AI:
- Без воды, каждое слово продаёт
- Начинаешь с боли клиента, а не с описания компании
- Цифры везде: ROI, окупаемость, % точности
- Социальное доказательство: 47 проектов, 94% точность, 0 провальных внедрений
- Окупаемость от 3 месяцев
- Эксклюзивность по городу/сегменту

Структура КП:
1. Заголовок — боль клиента одной фразой
2. Ситуация — что происходит у них сейчас
3. Решение — что конкретно делает ST8-AI
4. Результат — цифры и сроки
5. Пакеты и цены
6. Следующий шаг — конкретное действие

Интеграции: iiko, R-Keeper, 1С, MCRM, Telegram, Мессенджер Макс.
Никогда не упоминай WhatsApp.""",

    "deal-analyst": """Ты ST8-AI Deal Analyst — стратег по сделкам.
Анализируешь текущую ситуацию по клиенту и говоришь что делать дальше.

Твой анализ включает:
1. Стадия сделки: холодный/тёплый/горячий/зависший
2. Главный стопор: цена/доверие/время/технические вопросы/согласование
3. Следующий шаг: конкретное действие с текстом сообщения или скриптом звонка
4. Дедлайн: когда и как создать срочность
5. Риск: что может убить сделку и как предотвратить

Используй OODA: Observe (что происходит) → Orient (почему) → Decide (что делать) → Act (конкретный текст/скрипт).

Всегда заканчивай конкретным следующим шагом с готовым текстом.""",
}

EXTERNAL_AGENTS_DIR = os.path.expanduser(r"~\\.claude\\agents")

def load_external_agents():
    """Загружает агентов из ~/.claude/agents/*.md"""
    agents = {}
    if not os.path.exists(EXTERNAL_AGENTS_DIR):
        return agents
    for fname in os.listdir(EXTERNAL_AGENTS_DIR):
        if fname.endswith(".md"):
            name = fname[:-3]
            try:
                with open(os.path.join(EXTERNAL_AGENTS_DIR, fname), encoding="utf-8") as f:
                    content = f.read()
                # Извлекаем description или берём весь контент
                agents[name] = content
            except Exception:
                pass
    return agents

ALL_AGENTS = {**BUILTIN_AGENTS}
ALL_AGENTS.update(load_external_agents())

AGENT_ROUTER_PROMPT = """Ты роутер агентов ST8-AI. Определи какой агент нужен для ответа на сообщение.

Доступные агенты:
- sales-closer: закрытие сделок, клиент говорит дорого/подумаю/не сейчас
- objection-handler: работа с возражениями, нужны варианты ответов
- kp-writer: написать коммерческое предложение, КП, питч
- deal-analyst: анализ ситуации по клиенту, стратегия, следующий шаг
- st8-kp-architect: архитектура КП, структура предложения
- st8-sales-strategist: стратегия продаж, выход на клиента
- st8-horeca-consultant: вопросы по HoReCa, ресторанам, отелям
- st8-bot-developer: разработка ботов, технические вопросы
- st8-backend-architect: архитектура систем, API
- st8-security-auditor: безопасность кода
- st8-ai-director: стратегия ST8-AI, продуктовые решения
- none: общий вопрос, не требует специалиста

Ответь ТОЛЬКО именем агента без пояснений. Например: sales-closer"""


def route_to_agent(user_text, claude_client, model):
    """Определяет нужного агента через Claude"""
    try:
        response = claude_client.messages.create(
            model=model,
            max_tokens=50,
            messages=[
                {"role": "user", "content": f"{AGENT_ROUTER_PROMPT}\\n\\nСообщение: {user_text}"}
            ]
        )
        agent_name = response.content[0].text.strip().lower()
        return agent_name if agent_name in ALL_AGENTS else "none"
    except Exception:
        return "none"


def process_with_agent(user_text, history, claude_client, model):
    """Обрабатывает сообщение через нужного агента"""
    agent_name = route_to_agent(user_text, claude_client, model)
    
    system_prompt = ALL_AGENTS.get(agent_name, "")
    agent_label = f"[{agent_name}] " if agent_name != "none" else ""
    
    messages = []
    for h in history[-10:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_text})
    
    try:
        kwargs = {
            "model": model,
            "max_tokens": 1500,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
            
        response = claude_client.messages.create(**kwargs)
        reply = response.content[0].text.strip()
        return f"{agent_label}{reply}"
    except Exception as e:
        if "529" in str(e) or "overloaded" in str(e).lower():
            import time
            time.sleep(15)
            try:
                response = claude_client.messages.create(**kwargs)
                return f"{agent_label}{response.content[0].text.strip()}"
            except Exception:
                pass
        return f"[Ошибка агента {agent_name}]: {e}"
'''

PATCH_CODE = '''
    # Маршрутизация через агентов (заменяет process_incoming_message)
    reply = process_with_agent(user_text, history, claude_client, CLAUDE_MODEL)
'''

def upgrade_jarvis():
    jarvis_path = os.path.join(os.path.dirname(__file__), "jarvis.py")
    
    with open(jarvis_path, encoding="utf-8") as f:
        content = f.read()

    # 1. Проверяем что уже не добавлено
    if "ST8-AI SUPER AGENTS" in content:
        print("Агенты уже добавлены в jarvis.py")
    else:
        # Добавляем агентов после импортов (после load_dotenv строки)
        insert_after = "load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)"
        if insert_after in content:
            content = content.replace(insert_after, insert_after + "\n" + AGENTS_CODE)
            print("✓ Агенты добавлены")
        else:
            # Добавляем в конец перед __main__
            main_idx = content.find("if __name__ == '__main__'")
            if main_idx > 0:
                content = content[:main_idx] + AGENTS_CODE + "\n\n" + content[main_idx:]
                print("✓ Агенты добавлены перед __main__")

    # 2. Заменяем вызов process_incoming_message на process_with_agent
    old_call = "reply = process_incoming_message(user_text, history)"
    new_call = "reply = process_with_agent(user_text, history, claude_client, CLAUDE_MODEL)"
    
    if old_call in content:
        content = content.replace(old_call, new_call)
        print("✓ Router подключён")
    elif new_call in content:
        print("✓ Router уже подключён")
    else:
        print("⚠ Не нашёл process_incoming_message — проверь вручную")

    with open(jarvis_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("\n✅ Jarvis обновлён! Перезапусти: python jarvis.py")
    print("\nТеперь Jarvis умеет:")
    print("  → Закрывать сделки [sales-closer]")
    print("  → Работать с возражениями [objection-handler]")
    print("  → Писать КП [kp-writer]")
    print("  → Анализировать сделки [deal-analyst]")
    print("  + все 10 агентов ST8-AI из .claude/agents/")


if __name__ == "__main__":
    upgrade_jarvis()
