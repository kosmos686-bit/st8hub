# -*- coding: utf-8 -*-
import json
from pathlib import Path
from datetime import datetime

class ResponseLogger:
    """Логирует все отклики Макса"""
    
    def __init__(self):
        self.responses_file = Path("data") / "responses_log.json"
    
    def log_response(self, project_id, project_title, budget, response_text):
        """Сохраняет отклик Макса"""
        
        responses = []
        if self.responses_file.exists():
            with open(self.responses_file, 'r', encoding='utf-8') as f:
                responses = json.load(f)
        
        responses.append({
            "project_id": project_id,
            "project_title": project_title,
            "budget": budget,
            "response_text": response_text,
            "time": datetime.now().isoformat()
        })
        
        with open(self.responses_file, 'w', encoding='utf-8-sig') as f:
            json.dump(responses, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Отклик сохранён в data/responses_log.json")

# Использование:
logger = ResponseLogger()
logger.log_response(
    "903039",
    "Создание сайта визитки",
    10000,
    "Здравствуйте! Я специалист по веб-разработке с опытом 5+ лет. Создам вам красивый сайт визитку в срок. Стоимость 10000 рублей. Готов к обсуждению."
)
