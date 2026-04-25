import asyncio
from playwright.async_api import async_playwright

async def auth_and_save():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🔐 Открываю Kwork для авторизации...")
        await page.goto("https://kwork.ru/login", wait_until="networkidle")
        
        print("\n⏳ АВТОРИЗУЙСЯ ВРУЧНУЮ В БРАУЗЕРЕ!")
        print("   1. Введи email: jul1apopova23@yandex.ru")
        print("   2. Введи пароль: Milana2016!")
        print("   3. Нажми 'Войти'")
        print("   4. Жди 30 сек пока я сохраню cookies...\n")
        
        await asyncio.sleep(30)  # Ждём авторизации
        
        # Сохраняем cookies браузера (другие чем раньше!)
        cookies = await page.context.cookies()
        
        import json
        from pathlib import Path
        
        Path("data").mkdir(exist_ok=True)
        Path("data/browser_state.json").write_text(json.dumps({
            'cookies': cookies,
            'saved_at': str(asyncio.get_event_loop().time())
        }, indent=2, default=str))
        
        print(f"✅ Сохранено {len(cookies)} cookies браузера")
        
        # Проверяем авторизацию
        await page.goto("https://kwork.ru/projects/3155207")
        await asyncio.sleep(3)
        
        buttons = await page.query_selector_all('button')
        for btn in buttons:
            text = await btn.inner_text()
            if 'Предложить' in text:
                print("✅ АВТОРИЗАЦИЯ УСПЕШНА! Видна кнопка 'Предложить'")
                break
        else:
            print("❌ Авторизация не сработала")
        
        await browser.close()

asyncio.run(auth_and_save())
