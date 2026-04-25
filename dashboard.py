from flask import Flask, render_template_string
import json
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

def load_responded():
    responded_file = Path("data/responded.json")
    if responded_file.exists():
        return json.loads(responded_file.read_text())
    return []

@app.route('/')
def dashboard():
    responded = load_responded()
    
    today = datetime.now().date()
    today_count = len([r for r in responded if datetime.fromisoformat(r['time']).date() == today])
    
    # Генерируем карточки проектов
    projects_html = ""
    if responded:
        for r in sorted(responded, key=lambda x: x['time'], reverse=True):
            projects_html += f'''
            <div class="project-card">
                <div class="project-title">#{r['id']} - {r['title']}</div>
                
                <div class="project-info">
                    <div class="info-item">
                        <div class="info-label">💰 Бюджет</div>
                        <div class="info-value budget">{r.get('budget', 0):,} ₽</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">👤 Заказчик</div>
                        <div class="info-value">{r.get('buyer', 'Неизвестно')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">⏰ Отклик</div>
                        <div class="info-value">{datetime.fromisoformat(r['time']).strftime('%d.%m %H:%M')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">✅ Статус</div>
                        <div class="info-value">Отклик отправлен</div>
                    </div>
                </div>
                
                <div class="project-links">
                    <a href="https://kwork.ru/projects/{r['id']}" target="_blank" class="btn btn-project">
                        🔗 Открыть проект
                    </a>
                    <a href="https://kwork.ru/user/{r.get('buyer_id', '')}" target="_blank" class="btn btn-buyer">
                        👤 Профиль заказчика
                    </a>
                </div>
            </div>
            '''
    else:
        projects_html = '<div class="empty">❌ Нет проектов</div>'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Проекты Kwork</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            
            .header {{
                background: white;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }}
            
            .header h1 {{ color: #667eea; font-size: 32px; margin-bottom: 10px; }}
            .header p {{ color: #666; font-size: 16px; }}
            
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            
            .stat-number {{ font-size: 32px; font-weight: bold; color: #667eea; }}
            .stat-label {{ color: #999; margin-top: 10px; font-size: 14px; }}
            
            .projects {{
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }}
            
            .projects h2 {{ 
                color: #333; 
                margin-bottom: 20px; 
                border-bottom: 3px solid #667eea; 
                padding-bottom: 15px;
            }}
            
            .project-card {{
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 10px;
                border-left: 5px solid #667eea;
            }}
            
            .project-title {{ 
                font-weight: bold; 
                font-size: 18px;
                color: #333;
                margin-bottom: 10px;
            }}
            
            .project-info {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 15px;
            }}
            
            .info-item {{
                background: white;
                padding: 10px;
                border-radius: 5px;
            }}
            
            .info-label {{ 
                color: #999; 
                font-size: 12px; 
                text-transform: uppercase;
                margin-bottom: 5px;
            }}
            
            .info-value {{ 
                color: #333; 
                font-weight: bold;
                font-size: 14px;
            }}
            
            .budget {{ color: #4caf50; font-size: 18px; }}
            
            .project-links {{
                display: flex;
                gap: 10px;
            }}
            
            .btn {{
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                text-decoration: none;
                display: inline-block;
            }}
            
            .btn-project {{ 
                background: #667eea; 
                color: white;
            }}
            
            .btn-project:hover {{ 
                background: #5568d3;
            }}
            
            .btn-buyer {{ 
                background: #4caf50; 
                color: white;
            }}
            
            .btn-buyer:hover {{ 
                background: #45a049;
            }}
            
            .empty {{ 
                text-align: center; 
                padding: 40px; 
                color: #999;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📋 ПРОЕКТЫ KWORK</h1>
                <p>Мониторинг и управление откликами</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{today_count}</div>
                    <div class="stat-label">Откликов сегодня</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(responded)}</div>
                    <div class="stat-label">Всего откликов</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{sum(int(r.get('budget', 0)) for r in responded) if responded else 0} ₽</div>
                    <div class="stat-label">Общая сумма</div>
                </div>
            </div>
            
            <div class="projects">
                <h2>📋 АКТИВНЫЕ ПРОЕКТЫ</h2>
                {projects_html}
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html)

if __name__ == '__main__':
    print("🌐 Вебинтерфейс 'ПРОЕКТЫ KWORK' запущен!")
    print("📱 Открой в браузере: http://localhost:5000")
    app.run(debug=True, host='localhost', port=5000)
