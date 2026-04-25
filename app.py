"""ST8 AI — application entry point.

Starts APScheduler and registers all agents.
Run with: python app.py
"""

import time
from apscheduler.schedulers.background import BackgroundScheduler

from agents import st8_ceo_assistant

scheduler = BackgroundScheduler()

# Register agents
st8_ceo_assistant.init(scheduler)

if __name__ == '__main__':
    scheduler.start()
    print('[app] Scheduler started. CEO briefing: 08:00 MSK. Ctrl+C to stop.')
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print('[app] Scheduler stopped.')
