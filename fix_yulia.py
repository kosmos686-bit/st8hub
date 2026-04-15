code = open('jarvis.py', encoding='utf-8').read()
old = 'asyncio.run(bot.send_message(chat_id=YULIA_CHAT_ID, text=full_msg))'
new = (
    'import urllib.parse\n'
    '        data = urllib.parse.urlencode({"chat_id": YULIA_CHAT_ID, "text": full_msg}).encode()\n'
    '        req = urllib.request.Request(f"https://api.telegram.org/bot{JARVIS_BOT_TOKEN}/sendMessage", data=data)\n'
    '        urllib.request.urlopen(req, timeout=10)'
)
result = code.replace(old, new)
open('jarvis.py', 'w', encoding='utf-8').write(result)
print('OK' if old not in result else 'NOT FOUND - строка не найдена')
