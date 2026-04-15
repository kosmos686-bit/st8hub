from playwright.sync_api import sync_playwright
import pandas as pd
import time

def parse_stealth():
    with sync_playwright() as p:
        # Запускаем браузер с аргументами "человечности"
        browser = p.chromium.launch(
            headless=False,  # Видимый браузер (не фоновый)
            args=[
                "--incognito",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--window-size=1920,1080",
                "--start-maximized",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
        )
        
        # Создаем контекст (чистый, как инкогнито)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0",
            permissions=["geolocation"]
        )
        
        page = context.new_page()
        
        # Убираем следы автоматизации
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ru-RU', 'ru', 'en-US', 'en']
            });
        """)
        
        print("🕵️ Открываю bankrot.fedresurs.ru в инкогнито...")
        
        try:
            page.goto("https://bankrot.fedresurs.ru/", wait_until="domcontentloaded", timeout=20000)
            time.sleep(5)
            
            # Проверяем, не 403 ли
            title = page.title()
            content = page.content()
            
            if "403" in title or "Forbidden" in content or "Error" in title:
                print("❌ Сайт вернул 403 (IP в бане)")
                print("💡 Решение: Переключись на мобильный интернет (раздача с телефона)")
                browser.close()
                return None
            
            print(f"✅ Сайт открылся! Заголовок: {title[:50]}")
            print("📸 Делаю скриншот...")
            page.screenshot(path="bankrot_test.png")
            
            # Ищем ссылку на АУ
            print("🔍 Ищу раздел 'Арбитражные управляющие'...")
            
            # Кликаем по меню если есть
            try:
                au_link = page.locator("text=Арбитражные управляющие").first
                if au_link.is_visible():
                    au_link.click()
                    print("✅ Перешел в раздел АУ")
                    time.sleep(3)
            except:
                print("⚠️ Не нашел ссылку, пробую прямой URL...")
                page.goto("https://bankrot.fedresurs.ru/ManagePersons/Search", timeout=15000)
                time.sleep(3)
            
            # Ждем таблицу
            try:
                page.wait_for_selector("table", timeout=10000)
                print("✅ Таблица загрузилась!")
            except:
                print("⚠️ Таблица не появилась вовремя")
            
            # Собираем данные (первые 5 строк)
            rows = page.locator("table tbody tr").all()
            print(f"   Найдено строк: {len(rows)}")
            
            results = []
            for row in rows[:5]:
                try:
                    cells = row.locator("td").all()
                    if len(cells) >= 4:
                        fio = cells[0].inner_text().strip()
                        inn = cells[1].inner_text().strip()
                        sro = cells[2].inner_text().strip()
                        status = cells[3].inner_text().strip()
                        
                        if fio and len(fio) > 3:
                            results.append({
                                "ФИО": fio,
                                "ИНН": inn,
                                "СРО": sro,
                                "Статус": status
                            })
                except:
                    continue
            
            if results:
                df = pd.DataFrame(results)
                filename = f"bolshakova_stealth_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"
                df.to_excel(filename, index=False)
                print(f"\n✅ Сохранено {len(results)} записей в {filename}")
                print(df.to_string())
            else:
                print("⚠️ Не удалось собрать данные из таблицы")
                
            browser.close()
            return results
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            browser.close()
            return None

if __name__ == "__main__":
    parse_stealth()