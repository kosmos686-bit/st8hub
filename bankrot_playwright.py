from playwright.sync_api import sync_playwright
import pandas as pd
import time

def parse_efrs_au():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("🌐 Захожу на главную...")
        page.goto("https://bankrot.fedresurs.ru/")
        time.sleep(3)
        
        # Ищем кнопку "Арбитражные управляющие"
        print("🔍 Ищу раздел 'Арбитражные управляющие'...")
        
        try:
            link = page.locator('text=Арбитражные управляющие').first
            link.click()
            print("✅ Перешел в раздел АУ")
        except:
            page.goto("https://bankrot.fedresurs.ru/ManagePersons/Search")
            print("⚠️ Прямой переход")
        
        time.sleep(4)
        
        try:
            page.wait_for_selector("table", timeout=15000)
        except:
            print("❌ Таблица не загрузилась")
            browser.close()
            return []
        
        rows = page.locator("table tbody tr").all()
        
        results = []
        for row in rows[:5]:
            cells = row.locator("td").all()
            if len(cells) >= 4:
                results.append({
                    "ФИО": cells[0].inner_text().strip(),
                    "ИНН": cells[1].inner_text().strip(),
                    "СРО": cells[2].inner_text().strip(),
                    "Статус": cells[3].inner_text().strip()
                })
        
        browser.close()
        return results

def parse_efrs_debtors():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("🌐 Ищу должников...")
        page.goto("https://bankrot.fedresurs.ru/Debtors/Search")
        time.sleep(4)
        
        try:
            page.wait_for_selector("table", timeout=15000)
        except:
            print("❌ Таблица не загрузилась")
            browser.close()
            return []
        
        rows = page.locator("table tbody tr").all()
        
        results = []
        for row in rows:
            cells = row.locator("td").all()
            if len(cells) >= 3:
                category = cells[2].inner_text().strip()
                if "Крупное" in category or "Среднее" in category:
                    results.append({
                        "Название": cells[0].inner_text().strip(),
                        "ИНН": cells[1].inner_text().strip(),
                        "Категория": category
                    })
                    if len(results) >= 5:
                        break
        
        browser.close()
        return results

if __name__ == "__main__":
    print("=== Парсинг ЕФРС через браузер ===\n")
    
    au_data = parse_efrs_au()
    if au_data:
        df_au = pd.DataFrame(au_data)
        df_au.to_excel("au_playwright.xlsx", index=False)
        print(f"\n✅ АУ сохранено: {len(df_au)} записей")
        print(df_au.to_string())
    
    print("\n" + "="*50 + "\n")
    
    debtor_data = parse_efrs_debtors()
    if debtor_data:
        df_debt = pd.DataFrame(debtor_data)
        df_debt.to_excel("debtors_playwright.xlsx", index=False)
        print(f"\n✅ Должников сохранено: {len(df_debt)} записей")
        print(df_debt.to_string())