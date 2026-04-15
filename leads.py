import requests
import pandas as pd
import time
import json
from datetime import datetime

def get_fns_token(session: requests.Session, query: str, region: str = "77") -> str:
    """Получаем токен сессии ФНС (обязательный шаг)"""
    url = "https://egrul.nalog.ru/"
    data = {
        "query": query,
        "region": region if region else "99"  # 99 = все регионы
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://egrul.nalog.ru/"
    }
    
    try:
        r = session.post(url, data=data, headers=headers, timeout=15)
        if r.status_code == 200:
            result = r.json()
            return result.get("t")
    except Exception as e:
        print(f"Ошибка получения токена: {e}")
    return None

def search_fns_companies(query: str, region: str = "77") -> list:
    """
    Поиск компаний через API ФНС (egrul.nalog.ru)
    Возвращает список словарей с данными
    """
    session = requests.Session()
    
    # Шаг 1: Получаем токен
    token = get_fns_token(session, query, region)
    if not token:
        return []
    
    time.sleep(0.5)  # Небольшая пауза
    
    # Шаг 2: Получаем результаты по токену
    url = f"https://egrul.nalog.ru/search-result/{token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://egrul.nalog.ru/"
    }
    
    try:
        r = session.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            rows = data.get("rows", [])
            
            companies = []
            for row in rows:
                company = {
                    "Название": row.get("n", ""),
                    "ИНН": row.get("i", ""),
                    "ОГРН": row.get("o", ""),
                    "КПП": row.get("p", ""),
                    "Регион": row.get("r", ""),
                    "Статус": "Действующее" if row.get("s") == "1" else "Недействующее",
                    "Дата_регистрации": row.get("d", ""),
                    "ОКВЭД": row.get("k", ""),
                    "Адрес": row.get("a", "")
                }
                companies.append(company)
            
            return companies
    except Exception as e:
        print(f"Ошибка запроса: {e}")
    
    return []

def main():
    # Отрасли для поиска (профиль Большаковой: МСП, консалтинг, аудит, налоги)
    search_queries = [
        "аудит",
        "бухгалтерские услуги", 
        "налоговый консультант",
        "управленческий учет",
        "консалтинг",
        "юридические услуги",
        "сопровождение банкротства",
        " due diligence"
    ]
    
    all_companies = []
    
    print("=== Поиск компаний для базы лидов ===")
    
    for query in search_queries:
        print(f"\n🔍 Поиск: '{query}'...")
        companies = search_fns_companies(query, region="77")  # Москва
        print(f"   Найдено: {len(companies)}")
        
        all_companies.extend(companies)
        time.sleep(1)  # Пауза между запросами (вежливость к API)
    
    # Убираем дубли по ИНН
    df = pd.DataFrame(all_companies)
    if not df.empty:
        initial_count = len(df)
        df.drop_duplicates(subset=["ИНН"], keep="first", inplace=True)
        df = df[df["Статус"] == "Действующее"]  # Только активные
        
        # Фильтр по ОКВЭД (69.20 - бухгалтерский учет, 70.22 - консалтинг, 66.19 - финансы)
        # Раскомментируй если нужно:
        # df = df[df["ОКВЭД"].str.startswith(("69", "70", "66"), na=False)]
        
        final_count = len(df)
        
        # Сохраняем в Excel
        filename = f"bolshakova_leads_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n✅ ГОТОВО!")
        print(f"📊 Начальное количество: {initial_count}")
        print(f"📊 Уникальных компаний: {final_count}")
        print(f"📁 Сохранено в: {filename}")
        print(f"\nТоп-5 записей:")
        print(df.head()[["Название", "ИНН", "ОКВЭД"]].to_string(index=False))
    else:
        print("❌ Ничего не найдено. Проверь подключение или попробуй другие запросы.")

if __name__ == "__main__":
    main()