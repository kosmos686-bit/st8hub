"""
Автоматизация Google Search Console для st8-ai.ru
====================================================

Что делает:
1. Отправляет sitemap.xml (если он есть на сайте)
2. Запрашивает индексацию главной страницы через URL Inspection API
3. Показывает текущий статус индексации

ПОДГОТОВКА (один раз, вручную):
1. console.cloud.google.com -> создать проект
2. Library -> найти "Search Console API" -> Enable
3. IAM & Admin -> Service Accounts -> Create Service Account
4. У созданного аккаунта: Keys -> Add Key -> Create new key -> JSON -> скачать
5. Скопировать email вида xxx@project-id.iam.gserviceaccount.com
6. В search.google.com/search-console -> Настройки -> Пользователи и разрешения
   -> Добавить пользователя -> вставить этот email -> права "Владелец"

ЗАПУСК:
    python gsc_automate.py /путь/к/service-account-key.json
"""

import sys
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

SITE_URL = "https://st8-ai.ru/"          # ресурс в формате URL-prefix
SITE_DOMAIN = "sc-domain:st8-ai.ru"       # ресурс в формате domain (как на скриншоте)
SITEMAP_URL = "https://st8-ai.ru/sitemap.xml"
PAGES_TO_CHECK = [
    "https://st8-ai.ru/",
    "https://st8-ai.ru/horeca.html",
    "https://st8-ai.ru/proizvodstvo.html",
    "https://st8-ai.ru/retail.html",
    "https://st8-ai.ru/logistika.html",
    "https://st8-ai.ru/ofisy.html",
]

SCOPES = ["https://www.googleapis.com/auth/webmasters"]


def get_service(key_path):
    creds = service_account.Credentials.from_service_account_file(
        key_path, scopes=SCOPES
    )
    return build("searchconsole", "v1", credentials=creds)


def list_verified_sites(service):
    sites = service.sites().list().execute()
    print("\n📋 Доступные ресурсы для этого service account:")
    for s in sites.get("siteEntry", []):
        print(f"   - {s['siteUrl']} (роль: {s['permissionLevel']})")
    return [s["siteUrl"] for s in sites.get("siteEntry", [])]


def submit_sitemap(service, site_url, sitemap_url):
    try:
        service.sitemaps().submit(siteUrl=site_url, feedpath=sitemap_url).execute()
        print(f"✅ Sitemap отправлен: {sitemap_url}")
        return True
    except Exception as e:
        print(f"⚠️  Не удалось отправить sitemap: {e}")
        return False


def list_sitemaps(service, site_url):
    try:
        result = service.sitemaps().list(siteUrl=site_url).execute()
        entries = result.get("sitemap", [])
        if not entries:
            print("ℹ️  Sitemap-ов пока не найдено на этом ресурсе.")
        for sm in entries:
            print(f"   sitemap: {sm.get('path')} | последняя загрузка: {sm.get('lastDownloaded', 'н/д')}")
    except Exception as e:
        print(f"⚠️  Не удалось получить список sitemap: {e}")


def inspect_url(service, site_url, page_url):
    """URL Inspection API — показывает статус индексации конкретной страницы."""
    try:
        body = {
            "inspectionUrl": page_url,
            "siteUrl": site_url,
        }
        result = service.urlInspection().index().inspect(body=body).execute()
        status = result.get("inspectionResult", {}).get("indexStatusResult", {})
        print(f"\n🔍 Статус страницы {page_url}:")
        print(f"   Verdict: {status.get('verdict', 'н/д')}")
        print(f"   Coverage state: {status.get('coverageState', 'н/д')}")
        print(f"   Последнее сканирование: {status.get('lastCrawlTime', 'ещё не сканировалась')}")
        print(f"   Индексируется: {status.get('indexingState', 'н/д')}")
        return result
    except Exception as e:
        print(f"⚠️  Не удалось проверить URL: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python gsc_automate.py /путь/к/key.json")
        sys.exit(1)

    key_path = sys.argv[1]
    service = get_service(key_path)

    sites = list_verified_sites(service)
    if not sites:
        print("\n❌ Ресурсов не найдено. Проверь, что service account добавлен как "
              "'Владелец' в Search Console -> Настройки -> Пользователи и разрешения.")
        sys.exit(1)

    # Определяем, какой формат ресурса реально подтверждён
    target_site = None
    for candidate in (SITE_DOMAIN, SITE_URL):
        if candidate in sites:
            target_site = candidate
            break
    if not target_site:
        target_site = sites[0]
        print(f"\nℹ️  Использую первый найденный ресурс: {target_site}")

    print(f"\n▶️  Работаю с ресурсом: {target_site}")

    submit_sitemap(service, target_site, SITEMAP_URL)
    list_sitemaps(service, target_site)

    print(f"\n▶️  Проверяю {len(PAGES_TO_CHECK)} URL...")
    for page_url in PAGES_TO_CHECK:
        inspect_url(service, target_site, page_url)

    print("\n✅ Готово. Обычно данные по индексации Google обновляет с задержкой "
          "до 1-2 дней после первых действий на новом ресурсе.")
