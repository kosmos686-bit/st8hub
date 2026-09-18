"""
Автоматизация Яндекс.Вебмастера для st8-ai.ru
====================================================

Что делает:
1. Находит host_id сайта st8-ai.ru в твоём аккаунте Яндекс.Вебмастер
2. Добавляет/проверяет sitemap.xml
3. Запрашивает переобход (recrawl) главной страницы
4. Показывает текущую сводку по индексированию

ПОДГОТОВКА (один раз, вручную, ~2 минуты):
1. Зайти на https://oauth.yandex.ru/client/new
2. Создать приложение:
   - Название: любое, например "st8-seo-bot"
   - Платформа: "Веб-сервисы"
   - Callback URL: https://oauth.yandex.ru/verification_code
   - Доступы (Права): найти "Яндекс.Вебмастер" -> отметить все доступные
     (webmaster:hosts, webmaster:read, webmaster:write, webmaster:verify)
3. Сохранить приложение, скопировать Client ID
4. Перейти по ссылке (подставив свой Client ID):
   https://oauth.yandex.ru/authorize?response_type=token&client_id=ТВОЙ_CLIENT_ID
5. Разрешить доступ -> скопировать access_token из адресной строки
   (после "access_token=" и до "&")

ЗАПУСК:
    python yandex_webmaster_automate.py ТВОЙ_OAUTH_ТОКЕН

Если токен не передан аргументом, скрипт читает его из файла
yandex_token.txt рядом со скриптом (создать вручную один раз,
записав туда сам токен без переносов строк и пробелов).
"""

import os
import sys
import requests
from urllib.parse import quote

TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yandex_token.txt")


def resolve_token(argv):
    if len(argv) >= 2:
        return argv[1]
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            token = f.read().strip()
        if token:
            print(f"ℹ️  Токен прочитан из {TOKEN_FILE}")
            return token
    return None

SITE_URL = "https://st8-ai.ru/"
SITEMAP_PATH = "https://st8-ai.ru/sitemap.xml"
PAGES_TO_CHECK = [
    "https://st8-ai.ru/",
    "https://st8-ai.ru/horeca.html",
    "https://st8-ai.ru/proizvodstvo.html",
    "https://st8-ai.ru/retail.html",
    "https://st8-ai.ru/logistika.html",
    "https://st8-ai.ru/ofisy.html",
]

BASE = "https://api.webmaster.yandex.net/v4"


def get_headers(token):
    return {
        "Authorization": f"OAuth {token}",
        "Content-Type": "application/json",
    }


def get_user_id(token):
    r = requests.get(f"{BASE}/user", headers=get_headers(token))
    r.raise_for_status()
    return r.json()["user_id"]


def list_hosts(token, user_id):
    r = requests.get(f"{BASE}/user/{user_id}/hosts", headers=get_headers(token))
    r.raise_for_status()
    hosts = r.json().get("hosts", [])
    print("\n📋 Сайты, добавленные в этот аккаунт Яндекс.Вебмастер:")
    for h in hosts:
        print(f"   - {h['unicode_host_url']} (host_id: {h['host_id']}, статус проверки: {h.get('verified', 'н/д')})")
    return hosts


def find_host_id(hosts, site_url):
    target = site_url.rstrip("/").replace("https://", "").replace("http://", "")
    for h in hosts:
        candidate = h["unicode_host_url"].rstrip("/").replace("https://", "").replace("http://", "")
        if target in candidate or candidate in target:
            return h["host_id"]
    return None


def add_sitemap(token, user_id, host_id, sitemap_url):
    host_id_q = quote(host_id, safe="")
    body = {"url": sitemap_url}
    r = requests.post(
        f"{BASE}/user/{user_id}/hosts/{host_id_q}/user-added-sitemaps",
        headers=get_headers(token),
        json=body,
    )
    if r.status_code in (200, 201, 202):
        print(f"✅ Sitemap отправлен: {sitemap_url}")
        return True
    elif r.status_code == 409:
        print(f"ℹ️  Sitemap уже был добавлен ранее: {sitemap_url}")
        return True
    else:
        print(f"⚠️  Не удалось отправить sitemap ({r.status_code}): {r.text}")
        return False


def list_sitemaps(token, user_id, host_id):
    host_id_q = quote(host_id, safe="")
    r = requests.get(f"{BASE}/user/{user_id}/hosts/{host_id_q}/user-added-sitemaps", headers=get_headers(token))
    if r.status_code == 200:
        sitemaps = r.json().get("sitemaps", [])
        if not sitemaps:
            print("ℹ️  Sitemap-ов пока не найдено на этом ресурсе.")
        for sm in sitemaps:
            print(f"   sitemap: {sm.get('sitemap_url')} | добавлен: {sm.get('added_date', 'н/д')}")
    else:
        print(f"⚠️  Не удалось получить список sitemap: {r.text}")


def request_recrawl(token, user_id, host_id, page_url):
    host_id_q = quote(host_id, safe="")
    body = {"url": page_url}
    r = requests.post(
        f"{BASE}/user/{user_id}/hosts/{host_id_q}/recrawl/queue",
        headers=get_headers(token),
        json=body,
    )
    if r.status_code in (200, 201, 202):
        data = r.json()
        print(f"\n🔍 Запрос на переобход отправлен для {page_url}")
        print(f"   task_id: {data.get('task_id', 'н/д')}")
        print(f"   Осталось запросов на сегодня: {data.get('quota_remainder', data.get('daily_quota', {}).get('remaining', 'н/д'))}")
        return data
    else:
        print(f"⚠️  Не удалось запросить переобход ({r.status_code}): {r.text}")
        return None


def get_summary(token, user_id, host_id):
    host_id_q = quote(host_id, safe="")
    r = requests.get(f"{BASE}/user/{user_id}/hosts/{host_id_q}/summary", headers=get_headers(token))
    if r.status_code == 200:
        data = r.json()
        print("\n📊 Сводка по сайту:")
        print(f"   Страниц в поиске: {data.get('searchable_pages_count', 'н/д')}")
        print(f"   Всего проиндексировано: {data.get('total_pages_count', 'н/д')}")
    else:
        print(f"⚠️  Не удалось получить сводку: {r.text}")


if __name__ == "__main__":
    token = resolve_token(sys.argv)
    if not token:
        print("Использование: python yandex_webmaster_automate.py ТВОЙ_OAUTH_ТОКЕН")
        print(f"(или сохрани токен в {TOKEN_FILE})")
        sys.exit(1)

    try:
        user_id = get_user_id(token)
    except Exception as e:
        print(f"❌ Не удалось авторизоваться. Проверь токен. Ошибка: {e}")
        sys.exit(1)

    print(f"✅ Авторизация успешна (user_id: {user_id})")

    hosts = list_hosts(token, user_id)
    if not hosts:
        print("\n❌ В аккаунте нет добавленных сайтов. Сначала добавь st8-ai.ru "
              "на https://webmaster.yandex.ru и подтверди права.")
        sys.exit(1)

    host_id = find_host_id(hosts, SITE_URL)
    if not host_id:
        print(f"\n❌ Не нашёл {SITE_URL} среди добавленных сайтов. "
              f"Проверь, что сайт точно подтверждён в этом аккаунте.")
        sys.exit(1)

    print(f"\n▶️  Работаю с host_id: {host_id}")

    add_sitemap(token, user_id, host_id, SITEMAP_PATH)
    list_sitemaps(token, user_id, host_id)

    print(f"\n▶️  Запрашиваю переобход для {len(PAGES_TO_CHECK)} URL...")
    for page_url in PAGES_TO_CHECK:
        request_recrawl(token, user_id, host_id, page_url)

    get_summary(token, user_id, host_id)

    print("\n✅ Готово. Переобход и переиндексация занимают обычно от нескольких часов до пары дней.")
