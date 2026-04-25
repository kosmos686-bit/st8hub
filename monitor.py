import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import requests
import json
from pathlib import Path

class MessageMonitor:
    """Мониторит новые сообщения в сделках Kwork"""
    
    def __init__(self):
        self.name = "СИСТЕМА МОНИТОРИНГА"
        self.chat_id = 6152243830
        self.token = "8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y"
        self.messages_file = Path("data/kwork_messages.json")
    
    def send_telegram(self, message):
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
            )
        except:
            pass
    
    def save_message(self, project_id, message):
        """Сохраняет сообщение"""
        data = {}
        if self.messages_file.exists():
            data = json.loads(self.messages_file.read_text())
        
        if str(project_id) not in data:
            data[str(project_id)] = []
        
        data[str(project_id)].append({
            'message': message,
            'time': datetime.now().isoformat()
        })
        
        self.messages_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    async def check_messages(self):
        """Проверяет новые сообщения в Kwork"""
        
        print("\n🔔 МОНИТОРИНГ СООБЩЕНИЙ")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state="data/auth_state.json")
            page = await context.new_page()
            
            # Открываем сделки
            await page.goto("https://kwork.ru/seller", wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Ищем новые сообщения (красный значок)
            messages = await page.evaluate('''() => {
                const items = [];
                const deals = document.querySelectorAll('[class*="deal"]');
                
                deals.forEach(deal => {
                    const title = deal.querySelector('a')?.innerText;
                    const badge = deal.querySelector('[class*="badge"]')?.innerText;
                    
                    if (badge && badge.includes('1')) {  // Есть новое сообщение
                        items.push({
                            title: title,
                            url: deal.querySelector('a')?.href,
                            has_new: true
                        });
                    }
                });
                
                return items;
            }''')
            
            await context.close()
            await browser.close()
            
            return messages

class WorkerAgent:
    """Рабочий агент - начинает выполнение работы"""
    
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.chat_id = 6152243830
        self.token = "8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y"
    
    def send_telegram(self, message):
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
            )
        except:
            pass
    
    async def start_work(self, project, customer_message):
        """Начинает выполнение работы"""
        
        msg = f"""
🚨 <b>ВЫЗОВ! НАЧИНАЕМ РАБОТУ!</b>

💬 <b>Заказчик написал:</b>
{customer_message[:200]}

📋 <b>Проект:</b> {project['title']}
💰 <b>Сумма:</b> {project['budget']:,} ₽

🤖 <b>Включаю:</b> {self.name} ({self.role})

⏰ <b>Время начала:</b> {datetime.now().strftime('%H:%M:%S')}

📅 <b>Дедлайн:</b> 3 дня

✅ <b>Статус:</b> НАЧИНАЕМ РАБОТУ!
"""
        self.send_telegram(msg)
        print(f"✅ {self.name}: Начинаю работу над проектом #{project['id']}")

class JobDispatcher:
    """Диспетчер - определяет какого агента включить"""
    
    def __init__(self):
        self.chat_id = 6152243830
        self.token = "8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y"
    
    def send_telegram(self, message):
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
            )
        except:
            pass
    
    async def dispatch(self, project, customer_message):
        """Определяет какого агента включить на основе проекта"""
        
        print(f"\n📦 ДИСПЕТЧЕР ОПРЕДЕЛЯЕТ АГЕНТА")
        
        # Анализируем тип проекта
        if 'видео' in project['title'].lower() or 'сайт' in project['title'].lower():
            worker = WorkerAgent("Дёма", "💻 Веб-разработчик")
            work_type = "🌐 Веб-разработка"
        
        elif 'код' in project['title'].lower() or 'программ' in project['title'].lower():
            worker = WorkerAgent("Дёма", "💻 Программист")
            work_type = "💻 Программирование"
        
        elif 'дизайн' in project['title'].lower():
            worker = WorkerAgent("Саша", "🎨 Дизайнер")
            work_type = "🎨 Дизайн"
        
        else:
            worker = WorkerAgent("Дёма", "🛠️ Инженер")
            work_type = "🛠️ Разное"
        
        # Отправляем главное уведомление
        msg_dispatch = f"""
📦 <b>ДИСПЕТЧЕР: ОПРЕДЕЛИЛ АГЕНТА!</b>

📋 <b>Проект:</b> {project['title']}
💰 <b>Бюджет:</b> {project['budget']:,} ₽

🎯 <b>Тип работы:</b> {work_type}
🤖 <b>Назначен агент:</b> {worker.name}

⏳ Передаю работу {worker.name}...
"""
        self.send_telegram(msg_dispatch)
        
        await asyncio.sleep(2)
        
        # Включаем агента
        await worker.start_work(project, customer_message)

async def main():
    print("=" * 70)
    print("🔔 СИСТЕМА МОНИТОРИНГА KWORK")
    print("=" * 70)
    
    monitor = MessageMonitor()
    dispatcher = JobDispatcher()
    
    # ТЕСТОВЫЙ СЦЕНАРИЙ
    test_project = {
        'id': '903039',
        'title': 'Создать сайт визитку артиста',
        'budget': 10000
    }
    
    test_customer_message = """Привет! Очень нравится твой подход. 
    Давай начнём работу. Вот примеры других сайтов которые мне нравятся: [ссылки]
    Сроки: максимум 3 дня"""
    
    # Имитируем ответ от заказчика
    print("\n⏰ ПРОВЕРЯЮ НОВЫЕ СООБЩЕНИЯ...")
    print("✅ Найдено новое сообщение от заказчика!\n")
    
    await dispatcher.dispatch(test_project, test_customer_message)
    
    print("\n" + "=" * 70)
    print("✅ РАБОТА НАЧАЛАСЬ!")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(main())
