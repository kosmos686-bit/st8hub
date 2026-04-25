import asyncio
from playwright.async_api import async_playwright

async def auth():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Идём на Kwork
        await page.goto("https://kwork.ru/projects?c=41")
        
        # Ждём пока ты вручную авторизуешься (откроется окно браузера)
        print("🔐 Авторизуйся в браузере вручную...")
        print("⏳ Жди 30 секунд...")
        await asyncio.sleep(30)
        
        # Берём cookies
        cookies = await page.context.cookies()
        
        import json
        from pathlib import Path
        
        Path("data").mkdir(exist_ok=True)
        Path("data/kwork_cookies.json").write_text(
            json.dumps([{'name': c['name'], 'value': c['value']} for c in cookies], indent=2)
        )
        
        print(f"✅ Сохранено {len(cookies)} cookies!")
        
        await browser.close()

asyncio.run(auth())
