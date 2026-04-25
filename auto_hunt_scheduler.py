import asyncio
from playwright.async_api import async_playwright
import re
import json
from pathlib import Path
from datetime import datetime

async def hunt():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🔍 ОХОТА НА KWORK (5000-50000 ₽)")
        print("=" * 50)
        
        projects = []
        
        # БЕЗ фильтра категорий - берём все проекты
        for page_num in range(1, 4):
            url = f"https://kwork.ru/projects?page={page_num}"
            print(f"\n📄 Страница {page_num}...")
            
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(2)
            
            content = await page.content()
            
            # Ищем проекты
            project_links = re.findall(r'/projects/(\d+)', content)
            amounts = re.findall(r'(\d+(?:\s\d{3})*)\s*₽', content)
            
            print(f"   Найдено: {len(project_links)} проектов")
            
            for i, proj_id in enumerate(project_links[:15]):
                try:
                    if i >= len(amounts):
                        continue
                    
                    budget = int(amounts[i].replace(' ', ''))
                    
                    # ФИЛЬТР: 5000-80000 ₽
                    if not (5000 <= budget <= 80000):
                        continue
                    
                    # Заголовок
                    match = re.search(
                        rf'/projects/{proj_id}"[^>]*title="([^"]*)"',
                        content
                    )
                    if not match:
                        match = re.search(
                            rf'/projects/{proj_id}"[^>]*>([^<]+)<',
                            content
                        )
                    
                    title = match.group(1).strip()[:80] if match else "Проект"
                    
                    projects.append({
                        'id': proj_id,
                        'title': title,
                        'budget': budget,
                        'url': f"https://kwork.ru/projects/{proj_id}",
                        'found_at': datetime.now().isoformat(),
                        'status': 'found'
                    })
                    
                    print(f"   ✅ {budget:,} ₽ | {title}")
                
                except:
                    pass
        
        await browser.close()
        
        if projects:
            Path("data").mkdir(exist_ok=True)
            Path("data/projects.json").write_text(json.dumps(projects, indent=2, ensure_ascii=False))
            print(f"\n✅ ИТОГО: {len(projects)} проектов (5000-50000 ₽)")
        else:
            print(f"\n⚠️ Проектов в диапазоне 5000-50000 ₽ не найдено на Kwork")
            print("Может быть сейчас низкий спрос на проекты?")

asyncio.run(hunt())
