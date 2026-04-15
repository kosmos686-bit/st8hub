import pandas as pd
import requests

def download_au_registry():
    """Скачиваем реестр АУ с data.gov.ru (открытые данные)"""
    url = "https://data.gov.ru/opendata/7704786035-arbitrazhnieupravliaushie/data-20250401T000000.json"
    
    print("📥 Скачиваю реестр АУ...")
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            
            results = []
            for item in data:
                # Фильтр: только Москва (регион 77 или "Москва" в адресе)
                region = item.get("region", "")
                if "77" in str(region) or "Москва" in str(item.get("address", "")):
                    results.append({
                        "ФИО": item.get("name", ""),
                        "ИНН": item.get("inn", ""),
                        "СРО": item.get("sro_name", ""),
                        "Регион": item.get("region_name", "Москва"),
                        "Статус": "Активен" if item.get("is_active") else "Исключен",
                        "Номер_в_реестре": item.get("register_number", ""),
                        "Дата_регистрации": item.get("registration_date", "")
                    })
            
            df = pd.DataFrame(results)
            df = df[df["Статус"] == "Активен"]
            
            # Берем первые 30 для Большаковой
            df_top = df.head(30)
            
            filename = f"bolshakova_au_official_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"
            df_top.to_excel(filename, index=False)
            
            print(f"✅ Сохранено {len(df_top)} АУ из Москвы в {filename}")
            print("\n📊 Первые 5 записей:")
            print(df_top.head()[["ФИО", "СРО"]].to_string())
            
            return df_top
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

if __name__ == "__main__":
    download_au_registry()