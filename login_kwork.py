import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path

async def login_kwork():
    email = "jul1apopova23@yandex.ru"
    password = "Milana2016!"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=False чтобы видеть
        page = await browser.new_page()
        
        print("🔐 Заходим на Kwork...")
        await page.goto("https://kwork.ru/login", wait_until="networkidle")
        
        # Вводим email
        print("📧 Вводим email...")
        await page.fill('input[type="email"]', email)
        await asyncio.sleep(0.5)
        
        # Вводим пароль
        print("🔑 Вводим пароль...")
        await page.fill('input[type="password"]', password)
        await asyncio.sleep(0.5)
        
        # Нажимаем "Войти"
        print("🚀 Нажимаем кнопку входа...")
        await page.click('button[type="submit"]')
        
        # Ждём загрузки
        print("⏳ Ждём загрузки (10 сек)...")
        await asyncio.sleep(10)
        
        # Проверяем авторизовались ли
        if "login" in page.url:
            print("❌ Ошибка авторизации!")
            await browser.close()
            return False
        
        print("✅ Авторизовались!")
        
        # Берём ВСЕ cookies
        cookies = await page.context.cookies()
        
        # Сохраняем
        Path("data").mkdir(exist_ok=True)
        cookies_dict = {c['name']: c['value'] for c in cookies}
        Path("data/kwork_cookies.json").write_text(json.dumps(cookies_dict, indent=2))
        
        print(f"✅ Сохранено {len(cookies)} cookies!")
        
        # Закрываем браузер
        await browser.close()
        
        # ВАЖНО: Стираем пароль из памяти
        password = ""
        email = ""
        
        return True

# Запускаем
result = asyncio.run(login_kwork())
if result:
    print("\n✅ ГОТОВО! Cookies сохранены. Теперь можно запустить охоту:")
    print("   python auto_hunt_scheduler.py")
else:
    print("\n❌ Не удалось авторизоваться")
