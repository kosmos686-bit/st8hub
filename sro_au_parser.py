import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

def parse_sro_au():
    """
    Парсинг с sroau.ru — официальный сайт СРО АУ.
    Нет Cloudflare, нет банов, чистый HTML.
    """
    base_url = "https://sroau.ru"
    # Список членов СРО с фильтром по Москве
    url = "https://sroau.ru/members/?region=77&status=active"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    print("🔍 Парсим СРО АУ (sroau.ru)...")
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Ищем таблицу или карточки с членами СРО
        results = []
        
        # Вариант 1: таблица
        rows = soup.select("table tbody tr")
        if not rows:
            # Вариант 2: div-карточки
            rows = soup.select(".member-item, .au-card, .item-member")
        
        print(f"   Найдено строк: {len(rows)}")
        
        for i, row in enumerate(rows[:30]):  # Первые 30
            try:
                # Извлекаем данные (адаптируем под реальную структуру сайта)
                name = row.select_one(".name, .fio, td:nth-child(1)").get_text(strip=True) if row.select_one(".name, .fio, td:nth-child(1)") else ""
                inn = row.select_one(".inn, td:nth-child(2)").get_text(strip=True) if row.select_one(".inn, td:nth-child(2)") else ""
                sro = "СРО АУ"  # Текущий сайт
                
                if name and len(name) > 5:  # Фильтр пустых
                    results.append({
                        "ФИО": name,
                        "ИНН": inn,
                        "СРО": sro,
                        "Регион": "Москва",
                        "Статус": "Активен",
                        "Источник": base_url
                    })
            except Exception as e:
                continue
        
        if results:
            df = pd.DataFrame(results)
            filename = f"bolshakova_sro_au_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"
            df.to_excel(filename, index=False)
            print(f"✅ Сохранено {len(df)} АУ в {filename}")
            return df
        else:
            print("⚠️ Не удалось распарсить структуру (сайт изменился)")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

if __name__ == "__main__":
    parse_sro_au()