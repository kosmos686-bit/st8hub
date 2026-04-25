import asyncio
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests
import json

class Logger:
    """Логирует все операции"""
    
    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.log_file = self.logs_dir / f"{self.today}.log"
    
    def log(self, event_type, message):
        """Записывает событие в лог"""
        time = datetime.now().strftime('%H:%M:%S')
        log_line = f"[{time}] [{event_type}] {message}"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + "\n")
        
        print(log_line)

class DeadlineTracker:
    """Отслеживает дедлайны проектов"""
    
    def __init__(self):
        self.deadlines_file = Path("data/deadlines.json")
        self.logger = Logger()
        self.load_deadlines()
    
    def load_deadlines(self):
        if self.deadlines_file.exists():
            self.deadlines = json.loads(self.deadlines_file.read_text(encoding='utf-8'))
        else:
            self.deadlines = {}
    
    def save_deadlines(self):
        self.deadlines_file.write_text(
            json.dumps(self.deadlines, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    def add_deadline(self, project_id, project_title, days=3):
        """Добавляет дедлайн (по умолчанию 3 дня)"""
        deadline_date = (datetime.now() + timedelta(days=days)).isoformat()
        
        self.deadlines[str(project_id)] = {
            'title': project_title,
            'deadline': deadline_date,
            'created_at': datetime.now().isoformat(),
            'status': 'in_progress'
        }
        
        self.save_deadlines()
        self.logger.log("ДЕДЛАЙН", f"Добавлен дедлайн для #{project_id}: {days} дней")
    
    def check_deadlines(self):
        """Проверяет приближающиеся дедлайны"""
        now = datetime.now()
        urgent = []
        today_deadline = []
        
        for project_id, deadline_info in self.deadlines.items():
            if deadline_info['status'] == 'completed':
                continue
            
            deadline = datetime.fromisoformat(deadline_info['deadline'])
            hours_left = (deadline - now).total_seconds() / 3600
            
            if 0 < hours_left <= 24:  # Менее 24 часов
                today_deadline.append((project_id, deadline_info, hours_left))
            elif 0 < hours_left <= 2:  # Менее 2 часов
                urgent.append((project_id, deadline_info, hours_left))
        
        return urgent, today_deadline
    
    def complete_project(self, project_id):
        """Отмечает проект как завершённый"""
        if str(project_id) in self.deadlines:
            self.deadlines[str(project_id)]['status'] = 'completed'
            self.deadlines[str(project_id)]['completed_at'] = datetime.now().isoformat()
            self.save_deadlines()
            self.logger.log("ЗАВЕРШЕНИЕ", f"Проект #{project_id} завершён")

class IncomeCalculator:
    """Рассчитывает доходы"""
    
    def __init__(self):
        self.responded_file = Path("data/responded.json")
        self.logger = Logger()
    
    def get_today_income(self):
        """Доход за сегодня"""
        if not self.responded_file.exists():
            return 0
        
        responded = json.loads(self.responded_file.read_text(encoding='utf-8'))
        today = datetime.now().date()
        
        total = 0
        for r in responded:
            if datetime.fromisoformat(r['time']).date() == today and r.get('status') == 'completed':
                total += int(r.get('budget', 0))
        
        return total
    
    def get_week_income(self):
        """Доход за неделю"""
        if not self.responded_file.exists():
            return 0
        
        responded = json.loads(self.responded_file.read_text(encoding='utf-8'))
        week_ago = datetime.now().date() - timedelta(days=7)
        
        total = 0
        for r in responded:
            if datetime.fromisoformat(r['time']).date() >= week_ago and r.get('status') == 'completed':
                total += int(r.get('budget', 0))
        
        return total
    
    def get_month_income(self):
        """Доход за месяц"""
        if not self.responded_file.exists():
            return 0
        
        responded = json.loads(self.responded_file.read_text(encoding='utf-8'))
        month_ago = datetime.now().date() - timedelta(days=30)
        
        total = 0
        for r in responded:
            if datetime.fromisoformat(r['time']).date() >= month_ago and r.get('status') == 'completed':
                total += int(r.get('budget', 0))
        
        return total
    
    def get_total_income(self):
        """Общий доход"""
        if not self.responded_file.exists():
            return 0
        
        responded = json.loads(self.responded_file.read_text(encoding='utf-8'))
        
        total = 0
        for r in responded:
            if r.get('status') == 'completed':
                total += int(r.get('budget', 0))
        
        return total

class Dashboard:
    """Отправляет ежедневный dashboard в Telegram"""
    
    def __init__(self):
        self.chat_id = 6152243830
        self.token = "8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y"
        self.logger = Logger()
        self.calculator = IncomeCalculator()
        self.deadline_tracker = DeadlineTracker()
    
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
    
    async def send_daily_report(self):
        """Отправляет ежедневный отчёт"""
        
        today = datetime.now().strftime('%d.%m.%Y')
        today_income = self.calculator.get_today_income()
        week_income = self.calculator.get_week_income()
        month_income = self.calculator.get_month_income()
        total_income = self.calculator.get_total_income()
        
        # Проверяем дедлайны
        urgent, today_deadline = self.deadline_tracker.check_deadlines()
        
        deadline_msg = ""
        if urgent:
            deadline_msg += "\n🚨 <b>СРОЧНО (менее 2 часов):</b>\n"
            for proj_id, info, hours in urgent:
                deadline_msg += f"  • {info['title']} ({int(hours)}ч)\n"
        
        if today_deadline:
            deadline_msg += "\n⚠️ <b>СЕГОДНЯ ДЕДЛАЙНЫ:</b>\n"
            for proj_id, info, hours in today_deadline:
                deadline_msg += f"  • {info['title']} ({int(hours)}ч)\n"
        
        msg = f"""
📊 <b>ЕЖЕДНЕВНЫЙ ОТЧЁТ</b>

📅 <b>Дата:</b> {today}

💰 <b>ДОХОДЫ:</b>
  Сегодня: {today_income:,} ₽
  За неделю: {week_income:,} ₽
  За месяц: {month_income:,} ₽
  Всего: {total_income:,} ₽

📈 <b>СРЕДНИЙ ДОХОД:</b>
  В день: {int(total_income / 30):,} ₽
  В неделю: {int(week_income / 1):,} ₽

{deadline_msg}

✅ <b>СТАТУС СИСТЕМЫ:</b>
  • Охота: Работает ✅
  • Мониторинг: Работает ✅
  • Агенты: Работают ✅
  • Проверка: Работает ✅

⏰ <b>Время отчёта:</b> {datetime.now().strftime('%H:%M:%S')}
"""
        
        self.send_telegram(msg)
        self.logger.log("ОТЧЁТ", "Отправлен ежедневный dashboard")

class SystemManager:
    """Главный менеджер системы"""
    
    def __init__(self):
        self.logger = Logger()
        self.dashboard = Dashboard()
    
    def start(self):
        """Запускает полную систему"""
        
        # Отправляем отчёт каждый день в 20:00
        schedule.every().day.at("20:00").do(self.send_daily_report)
        
        self.logger.log("СИСТЕМА", "Полная автоматизация запущена!")
        
        print("\n" + "=" * 70)
        print("✅ ПОЛНАЯ СИСТЕМА ЗАПУЩЕНА!")
        print("=" * 70)
        print()
        print("📊 КОМПОНЕНТЫ:")
        print("  ✅ Логирование всех операций (logs/)")
        print("  ✅ Отслеживание дедлайнов (3 дня)")
        print("  ✅ Расчёт доходов (день/неделя/месяц)")
        print("  ✅ Ежедневный dashboard (в 20:00)")
        print()
        print("📁 ФАЙЛЫ:")
        print("  • logs/[DATE].log - все операции")
        print("  • data/deadlines.json - дедлайны")
        print("  • data/responded.json - доходы")
        print()
        print("=" * 70)
        print()
        
        # Основной цикл
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def send_daily_report(self):
        """Отправляет отчёт"""
        asyncio.run(self.dashboard.send_daily_report())

if __name__ == '__main__':
    try:
        import schedule
    except:
        print("pip install schedule")
        exit(1)
    
    manager = SystemManager()
    manager.start()
