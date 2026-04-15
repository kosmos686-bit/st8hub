import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

def try_parse_sro(domain, name):
    """Пробуем парсить конкретное СРО"""
    urls = [
        f"https://{domain}/members/",
        f"https://{domain}/members.php",
        f"https://{domain}/reestr/",
        f"https://{domain}/"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0"
    }
    
    for url in urls:
        try:
            print(f"   Пробую {url}...")
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                
                # Ищем таблицу с ФИО
                rows = soup.select("table tr, .member-row, .au-item")
                
                results = []
                for row in rows[1:6]:  # Первые 5
                    cells = row.find_all(["td", "div"])
                    if len(cells) >= 2:
                        text = cells[0].get_text(strip=True)
                        if len(text) > 10 and " " in text:  # Похоже на ФИО
                            results.append({
                                "ФИО": text,
                                "СРО": name,
                                "Источник": domain
                            })
                
                if results:
                    return results
        except:
            continue
    
    return None

def main():
    # Список СРО АУ Москвы (разные домены)
    sro_list = [
        ("sau-m.ru", "СРО АУ Москва"),
        ("sroau-mo.ru", "СРО АУ Московская область"), 
        ("fa-up.ru", "Федеральная ассоциация УП"),
        ("up-msk.ru", "УП Москва"),
        ("sro-au.ru", "СРО АУ (альтернативный)")
    ]
    
    all_results = []
    
    print("🔍 Пробуем разные СРО АУ...")
    
    for domain, sro_name in sro_list:
        print(f"\n➡️ {sro_name} ({domain})")
        data = try_parse_sro(domain, sro_name)
        
        if data:
            print(f"   ✅ Найдено {len(data)} записей")
            all_results.extend(data)
        else:
            print(f"   ❌ Не доступен")
        
        time.sleep(1)
    
    if all_results:
        df = pd.DataFrame(all_results)
        filename = f"bolshakova_sro_found_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(filename, index=False)
        print(f"\n✅ Сохранено {len(df)} записей в {filename}")
        print(df.to_string())
    else:
        print("\n❌ Все СРО недоступны с текущего IP")
        print("🔄 Последняя попытка: kad.arbitr.ru (судебные дела)...")
        # Fallback можно добавить

if __name__ == "__main__":
    main()