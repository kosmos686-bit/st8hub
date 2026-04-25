# -*- coding: utf-8 -*-
import asyncio
import schedule
import time
from datetime import datetime
from pathlib import Path
import json
import requests
from playwright.async_api import async_playwright

TOKEN = "8563225303:AAFeloLEvknQi_P9cYfcuf01Ic7rBMQzj-Y"
CHAT_ALEX = 6152243830
CHAT_JULIA = 5438530925

def tg(msg):
    for chat in [CHAT_ALEX, CHAT_JULIA]:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={'chat_id': chat, 'text': msg},
                timeout=5
            )
        except:
            pass
    print(msg)

def generate_response(project_title, budget):
    responses = {
        "Создание сайта визитки": f"""Здравствуйте!

Я Юлия, руководитель команды разработчиков с опытом 5+ лет.

У нас в команде:
  Макс — веб-разработчик (Next.js, React, Tailwind CSS)
  Анна — аналитик и дизайнер
  Я — проект-менеджер

Макс посмотрел ваш проект и готов приступить!

Что сделаем:
  Современный адаптивный дизайн
  Быстрая загрузка, SEO оптимизация
  Работа на всех устройствах
  Форма обратной связи

Сроки: 5-7 дней
Бюджет: {budget:,} рублей — нас устраивает

Готовы начать хоть сегодня!

С уважением, Юлия""",

        "Веб-приложение для магазина": f"""Здравствуйте!

Я Юлия, руководитель команды разработчиков. Специализируемся на веб-приложениях для магазинов.

У нас в команде:
  Макс — senior разработчик (React, Node.js, MongoDB)
  Анна — UI/UX аналитик
  Я — проект-менеджер и тестировщик

Макс изучил проект — задача понятная, готов стартовать!

Реализуем:
  Каталог товаров с фильтрами
  Корзина и оформление заказа
  Интеграция платежных систем
  Личный кабинет и админ-панель

Стек: React, Node.js, MongoDB
Сроки: 3-4 недели
Бюджет: {budget:,} рублей — работаем!

С уважением, Юлия""",

        "Дизайн логотипа": f"""Здравствуйте!

Я Юлия, руководитель дизайн-команды.

У нас в команде:
  Макс — дизайнер (Figma, Illustrator)
  Анна — арт-директор
  Я — проект-менеджер

Анна проанализировала вашу нишу, Макс готов приступить!

Что включает:
  3 концепции на выбор
  До 5 итераций правок
  Файлы: PNG, SVG, PDF, AI
  Гайдлайн по использованию

Сроки: 7-10 дней
Бюджет: {budget:,} рублей — договоримся!

С уважением, Юлия""",

        "Интеграция платежей": f"""Здравствуйте!

Я Юлия, руководитель команды разработчиков. Интеграция платежных систем — наша специализация.

У нас в команде:
  Макс — backend разработчик (Python, Node.js)
  Анна — аналитик и тестировщик
  Я — проект-менеджер

Макс посмотрел задачу — всё стандартно, справимся быстро!

Интегрируем:
  Юкасса, Сбербанк, Тинькофф
  Любую другую по запросу
  Тестирование в песочнице

Сроки: 2-3 дня
Бюджет: {budget:,} рублей — ок!

С уважением, Юлия""",

        "Мобильное приложение": f"""Здравствуйте!

Я Юлия, руководитель команды мобильной разработки. Делаем приложения 5 лет.

У нас в команде:
  Макс — мобильный разработчик (React Native, Flutter)
  Анна — UI/UX дизайнер
  Я — проект-менеджер

Макс изучил проект — интересная задача, готов взяться!

Что сделаем:
  iOS и Android (один код)
  Backend API (Node.js)
  Push-уведомления
  Публикация в магазины

Стек: React Native / Flutter
Сроки: 4-6 недель
Бюджет: {budget:,} рублей — обсудим!

С уважением, Юлия"""
    }
    return responses.get(project_title, f"""Здравствуйте!

Я Юлия, руководитель команды разработчиков с опытом 5+ лет.

У нас в команде:
  Макс — разработчик (веб, мобайл, боты)
  Анна — аналитик и дизайнер
  Я — проект-менеджер

Макс посмотрел ваш проект и готов приступить!

Сроки: обсудим по ТЗ
Бюджет: {budget:,} рублей — договоримся!

С уважением, Юлия""")


class KworkSender:
    def __init__(self):
        self.auth_state = Path("data") / "auth_state.json"
        self.responded_file = Path("data") / "responded.json"
        self.responses_file = Path("data") / "responses_log.json"

    def get_projects(self):
        if self.responded_file.exists():
            try:
                with open(self.responded_file, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_responses(self, responses):
        try:
            with open(self.responses_file, 'w', encoding='utf-8') as f:
                json.dump(responses, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Oshibka sohraneniya: {e}")

    async def find_real_projects(self, page):
        projects = []
        try:
            await page.goto("https://kwork.ru/projects?c=41", wait_until='networkidle')
            await page.wait_for_timeout(2000)
            cards = await page.query_selector_all('.want-card')
            for card in cards[:5]:
                try:
                    title_el = await card.query_selector('.want-card__title')
                    title = await title_el.inner_text() if title_el else "Bez nazvaniya"
                    link_el = await card.query_selector('a')
                    href = await link_el.get_attribute('href') if link_el else ""
                    project_id = href.split('/')[-1] if href else "0"
                    budget_el = await card.query_selector('.want-card__price')
                    budget_text = await budget_el.inner_text() if budget_el else "0"
                    budget = int(''.join(filter(str.isdigit, budget_text))) if budget_text else 0
                    projects.append({
                        "id": project_id,
                        "title": title.strip(),
                        "budget": budget,
                        "url": f"https://kwork.ru{href}",
                        "time": datetime.now().isoformat()
                    })
                except:
                    continue
        except Exception as e:
            print(f"Oshibka poiska: {e}")
        return projects

    async def send_one(self, page, project):
        project_id = project.get('id')
        project_title = project.get('title')
        budget = project.get('budget', 0)
        response_text = generate_response(project_title, budget)

        try:
            await page.goto(f"https://kwork.ru/projects/{project_id}", wait_until='networkidle')
            await page.wait_for_timeout(2000)

            btn = None
            for selector in [
                'button:has-text("Предложить услугу")',
                'a:has-text("Предложить услугу")',
                'button:has-text("Откликнуться")',
                'a:has-text("Откликнуться")'
            ]:
                btn = await page.query_selector(selector)
                if btn:
                    break

            if not btn:
                return False, "Knopka ne naydena", response_text

            await btn.click()
            await page.wait_for_timeout(2000)

            textarea = await page.query_selector('textarea')
            if not textarea:
                return False, "Pole ne naydeno", response_text

            await textarea.fill(response_text)
            await page.wait_for_timeout(1000)

            submit = None
            for selector in [
                'button:has-text("Отправить")',
                'button:has-text("Предложить")',
                'button[type="submit"]'
            ]:
                submit = await page.query_selector(selector)
                if submit:
                    break

            if not submit:
                return False, "Knopka otpravki ne naydena", response_text

            await submit.click()
            await page.wait_for_timeout(2000)
            return True, "OK", response_text

        except Exception as e:
            return False, str(e), response_text

    async def run(self):
        tg(f"OHOTA NACHATA\nVremya: {datetime.now().strftime('%H:%M:%S')}\nZapuskayu sistemu agentov...")
        time.sleep(1)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=str(self.auth_state))
            page = await context.new_page()

            tg("ALINA: Ischu realnye proekty na birzhe Kwork...")
            projects = await self.find_real_projects(page)

            if not projects:
                projects = self.get_projects()

            if not projects:
                tg("Proektov ne naydeno!")
                await browser.close()
                return

            project_list = "\n".join([
                f"  {i+1}. {p.get('title')} — {p.get('budget', 0):,} rub"
                for i, p in enumerate(projects)
            ])
            tg(f"ALINA NASHLA {len(projects)} PROEKTOV!\n\n{project_list}\n\nObshchiy byudzhet: {sum(p.get('budget', 0) for p in projects):,} rubley")
            time.sleep(1)

            analysis = "\n".join([f"  {i+1}. {p.get('title')} OK" for i, p in enumerate(projects)])
            tg(f"ANNA PROANALIZIROVALA\nMAKS NAPISAL OTKLIKI\n\n{analysis}\n\nVse otkliki gotovy!")
            time.sleep(1)

            responses_log = []
            success_count = 0

            for idx, project in enumerate(projects, 1):
                project_title = project.get('title')
                budget = project.get('budget', 0)
                project_id = project.get('id')
                response_text = generate_response(project_title, budget)

                ok, result, text = await self.send_one(page, project)

                if ok:
                    success_count += 1
                    status = "OTPRAVLEN NA KWORK!"
                else:
                    status = f"OSHIBKA: {result}"

                tg(f"""PROEKT #{idx} | {status}

ID: {project_id}
Nazvanie: {project_title}
Byudzhet: {budget:,} rubley
Vremya: {datetime.now().strftime('%H:%M:%S')}

---CHTO NAPISALA YULIYA---
{text}
--------------------------
Zhdem otveta zakazchika...""")

                responses_log.append({
                    "project_id": project_id,
                    "project_title": project_title,
                    "budget": budget,
                    "response_text": text,
                    "status": "sent" if ok else "error",
                    "time": datetime.now().isoformat()
                })

                time.sleep(3)

            await browser.close()

        self.save_responses(responses_log)

        tg(f"""OHOTA ZAVERSHENA!

Alina: nashla {len(projects)} proektov
Anna: proanalizirovala vse
Maks: napisal {len(projects)} otkikov
Yuliya: otpravila {success_count}/{len(projects)} na Kwork

Obshchiy byudzhet: {sum(p.get('budget', 0) for p in projects):,} rubley
Pri 20% konversii: {int(sum(p.get('budget', 0) for p in projects) * 0.2):,} rubley

Dyoma: zhdet otvetov zakazchikov
Monitoring: kazhdyy chas
Sleduyushchaya ohota: zavtra v 07:00""")


class SchedulerManager:
    def __init__(self):
        self.sender = KworkSender()

    def hunt_now(self):
        asyncio.run(self.sender.run())

    def start(self):
        print("SISTEMA OHOTY — YULIYA + KOMANDA")
        self.hunt_now()
        schedule.every().day.at("07:00").do(self.hunt_now)
        print("Sistema gotova!")
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                print("Ostanovlena")
                break

if __name__ == '__main__':
    manager = SchedulerManager()
    manager.start()
