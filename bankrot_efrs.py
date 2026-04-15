import requests
import pandas as pd
from datetime import datetime
import time

def get_session():
    """Создаем сессию с правильными cookies"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
    })
    # Первый запрос для получения cookies
    session.get("https://bankrot.fedresurs.ru/", timeout=10)
    time.sleep(1)
    return session

def get_bankrot_au(session, page: int = 1, region: str = "77") -> list:
    url = "https://bankrot.fedresurs.ru/ManagePersons/PersonsList"
    
    params = {
        "page": page,
        "pageSize": 100,
        "searchString": "",
        "regionId": region,
        "sortField": "Name",
        "sortDirection": "asc"
    }
    
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://bankrot.fedresurs.ru/ManagePersons"
    }
    
    try:
        r = session.get(url, params=params, headers=headers, timeout=15)
        
        # Проверяем, не вернулся ли HTML вместо JSON (защита)
        if r.headers.get('content-type', '').startswith('text/html'):
            print(f"   ⚠️ Страница {page}: получен HTML (блокировка), пропускаем")
            return []
            
        if r.status_code == 200:
            try:
                data = r.json()
                persons = data.get("Data", [])
                
                results = []
                for p in persons:
                    au = {
                        "ФИО": p.get("Name", ""),
                        "ИНН": p.get("Inn", ""),
                        "Регион": p.get("RegionName", ""),
                        "СРО": p.get("SroName", ""),
                        "Статус": "Активен" if p.get("IsActive") else "Исключен",
                        "Номер_АУ": p.get("ManagePersonNumber", ""),
                        "Телефон": p.get("Phone", ""),
                        "Email": p.get("Email", ""),
                        "Ссылка": f"https://bankrot.fedresurs.ru/ManagePersons/Details/{p.get('Id')}"
                    }
                    results.append(au)
                return results
            except Exception as e:
                print(f"   ⚠️ Ошибка JSON на странице {page}: {str(e)[:50]}")
                return []
    except Exception as e:
        print(f"   ⚠️ Сетевая ошибка страницы {page}: {str(e)[:50]}")
    return []

def get_companies_in_bankruptcy(session, region: str = "77", pages: int = 3) -> list:
    """Собираем должников"""
    all_debtors = []
    
    for page in range(1, pages + 1):
        url = "https://bankrot.fedresurs.ru/Debtors/DebtorsList"
        
        params = {
            "page": page,
            "pageSize": 100,
            "searchString": "",
            "regionId": region,
            "type": "LegalPerson"
        }
        
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://bankrot.fedresurs.ru/Debtors"
        }
        
        try:
            r = session.get(url, params=params, headers=headers, timeout=15)
            
            if r.headers.get('content-type', '').startswith('text/html'):
                print(f"   ⚠️ Должники стр.{page}: HTML вместо JSON")
                continue
                
            if r.status_code == 200:
                data = r.json()
                debtors = data.get("Data", [])
                
                for d in debtors:
                    category = d.get("Category", "")
                    # Только крупные и средние
                    if category in ["Крупное предприятие", "Среднее предприятие"]:
                        debtor = {
                            "Название": d.get("Name", ""),
                            "ИНН": d.get("Inn", ""),
                            "ОГРН": d.get("Ogrn", ""),
                            "Регион": d.get("RegionName", ""),
                            "Категория": category,
                            "АУ": d.get("ArbitrageManagerName", ""),
                            "Тип_процедуры": d.get("BankrutType", ""),
                            "Дата_начала": d.get("DateStart", ""),
                            "Ссылка": f"https://bankrot.fedresurs.ru/Debtors/Details/{d.get('Id')}"
                        }
                        all_debtors.append(debtor)
                        
                print(f"   Страница {page}: +{len([d for d in debtors if d.get('Category') in ['Крупное предприятие', 'Среднее предприятие']])} крупных")
                time.sleep(1.5)
                
        except Exception as e:
            print(f"   ⚠️ Ошибка должники стр.{page}: {str(e)[:50]}")
    
    return all_debtors

def main():
    print("=== ЕФРС Банкротов: Сбор данных ===\n")
    
    # Создаем сессию
    print("🔌 Подключение к ЕФРС...")
    session = get_session()
    print("✅ Сессия создана\n")
    
    # 1. Собираем АУ
    print("🔍 Сбор арбитражных управляющих (Москва)...")
    au_list = []
    
    for page in range(1, 6):
        persons = get_bankrot_au(session, page=page, region="77")
        if persons:
            au_list.extend(persons)
            print(f"   Страница {page}: +{len(persons)} АУ")
        time.sleep(1)
    
    # Сохраняем АУ
    if au_list:
        df_au = pd.DataFrame(au_list)
        df_au = df_au.drop_duplicates(subset=["ИНН"])
        df_au = df_au[df_au["Статус"] == "Активен"]
        
        # Фильтр по крупным СРО (опционально, раскомментируй если нужно):
        # big_sro = ["Московское саморегулируемое", "Промышленное СРО", "САУ \"Президент\""]
        # df_au = df_au[df_au["СРО"].str.contains('|'.join(big_sro), na=False)]
        
        filename_au = f"bolshakova_au_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df_au.to_excel(filename_au, index=False)
        print(f"\n✅ АУ сохранено: {len(df_au)} записей → {filename_au}")
    
    # 2. Должники
    print("\n🔍 Сбор крупных должников...")
    debtors = get_companies_in_bankruptcy(session, region="77", pages=3)
    
    if debtors:
        df_debtors = pd.DataFrame(debtors)
        filename_debtors = f"bolshakova_debtors_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df_debtors.to_excel(filename_debtors, index=False)
        print(f"\n✅ Должников сохранено: {len(df_debtors)} → {filename_debtors}")
        print("\n📊 Топ-10 по размеру:")
        print(df_debtors.head(10)[["Название", "Категория", "АУ"]].to_string())
    else:
        print("⚠️ Не удалось собрать должников (возможно, защита от ботов)")
    
    print("\n🎯 Готово!")
    if not au_list and not debtors:
        print("⚠️ ЕФРС блокирует парсинг. Альтернативы:")
        print("   1. Использовать официальную выгрузку (data.gov.ru)")
        print("   2. Парсить через selenium/playwright")
        print("   3. Купить готовую базу АУ (много продавцов на фрилансе)")

if __name__ == "__main__":
    main()