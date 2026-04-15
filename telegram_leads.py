import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

# Bot token and chat IDs
BOT_TOKEN = os.getenv('BOT_TOKEN', '8350702558:AAGCG8lcabW97NA-DBR1gmvo8oB0pJdf8Ms')
CHAT_IDS = ['6152243830', '5438530925']

async def send_lead_card(company_name, lpr, phone, email, telegram_social, site, segment, telegram_touch, max_touch, chat_ids=None):
    """
    Отправляет карточку лида в Telegram.

    :param company_name: Название компании
    :param lpr: ЛПР (имя, должность)
    :param phone: Телефон
    :param email: Email
    :param telegram_social: Telegram/соцсети
    :param site: Сайт
    :param segment: Сегмент
    :param telegram_touch: Текст касания Telegram
    :param max_touch: Текст касания Мессенджер Макс
    :param chat_ids: Список chat_id для отправки
    """
    bot = Bot(token=BOT_TOKEN)
    if chat_ids is None:
        chat_ids = CHAT_IDS

    # Формируем сообщение
    message = f"""
🏢 Компания: {company_name}
👤 ЛПР: {lpr}
📞 Контакт: {phone or 'требует уточнения'}
📧 Email: {email or 'требует уточнения'}
💬 Telegram/соцсети: {telegram_social or 'требует уточнения'}
🌐 Сайт: {site or 'требует уточнения'}
📂 Сегмент: {segment}

✉️ Текст касания Telegram:
{telegram_touch}

📱 Текст касания Мессенджер Макс:
{max_touch}

———————————————
    """.strip()

    for chat_id in chat_ids:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

# Пример использования
async def main():
    # Пример лида (Lucky Group)
    await send_lead_card(
        company_name="Lucky Group",
        lpr="Богдан Панченко, COO / руководитель развития",
        phone="+7 (495) 123-45-67",
        email="bogdan@luckygroup.ru",
        telegram_social="@bogdan_panchenko",
        site="luckygroup.ru",
        segment="HoReCa",
        telegram_touch="Привет, Богдан! Это Алексей из ST8-AI. Видим, что Lucky Group активно растёт, и часто именно рост сети выявляет узкие места в автоматизации маркетинга, CRM и управлении заказами. Есть 5 минут, чтобы обсудить, как мы помогаем сетям удерживать гостей и ускорять повторные продажи?",
        max_touch="Здравствуйте, Богдан. Меня зовут Алексей Гагарин, ST8-AI. Предлагаю обсудить решение для Lucky Group по объединению операционной аналитики, автоматизации MCRM и AI-ретеншну. Быстрый разговор сегодня/завтра?"
    )
    print("Карточка лида отправлена в Telegram!")

if __name__ == "__main__":
    asyncio.run(main())