#!/usr/bin/env python3
"""
deploy_platform.py — Windows-safe, всё внутри скрипта
Запуск: python deploy_platform.py
"""
import os, sys, subprocess

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
    if r.stdout.strip(): print(f"  {r.stdout.strip()}")
    if r.returncode != 0 and r.stderr.strip(): print(f"  ⚠️  {r.stderr.strip()}")
    return r.returncode == 0

def write(path, content):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"  ✅  {path}")

print("=== ST8 Resto Platform Deploy ===\n")

if not os.path.exists('unikfood.html'):
    print(f"❌ Запусти из папки репо. Сейчас: {os.getcwd()}")
    input("Enter для выхода..."); sys.exit(1)

write('sw.js', """const CACHE_VERSION = 'st8-v4';
const CACHE_NAME = `st8-resto-${CACHE_VERSION}`;
const STATIC_ASSETS = ['/st8-resto/','/st8-resto/index.html','/st8-resto/unikfood.html','/st8-resto/manifest.json','/st8-resto/icon-192.png','/st8-resto/icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(STATIC_ASSETS).catch(err => console.warn('[SW]',err))));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('st8-resto-') && k !== CACHE_NAME).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (!url.hostname.includes('github.io') && url.hostname !== 'localhost') return;
  e.respondWith(
    fetch(e.request).then(r => {
      if (r.ok) { const c = r.clone(); caches.open(CACHE_NAME).then(cache => cache.put(e.request, c)); }
      return r;
    }).catch(() => caches.match(e.request).then(cached => {
      if (cached) return cached;
      if (e.request.mode === 'navigate') return caches.match('/st8-resto/unikfood.html');
      return new Response('Offline', {status:503});
    }))
  );
});

self.addEventListener('message', e => { if (e.data === 'SKIP_WAITING') self.skipWaiting(); });
""")

write('README.md', """# ST8 Resto — CHEFF AI Технолог

> AI-платформа для управления ресторанами и food delivery.

## Продукты

| Продукт | Описание | Ссылка |
|---------|----------|--------|
| **Unikfood CHEFF** | AI-технолог для PP-доставки | [Открыть](https://kosmos686-bit.github.io/st8-resto/unikfood.html) |
| **ST8 СТРОЙ** | AI-прораб для строительных компаний | В разработке |

## Unikfood CHEFF умеет

- 📋 ТТК по ГОСТ Р 31987-2012 с КБЖУ и расчётом потерь
- 🔍 Импорт меню — CHEFF проводит технологический аудит
- 🌡️ Температурный журнал с алертами при нарушении СанПиН
- 🩺 Журнал здоровья персонала
- 👥 Профили подписчиков (цель, КБЖУ-норма, аллергии)
- 💰 ROI с учётом комиссии агрегатора

## Быстрый старт

1. Открой [unikfood.html](https://kosmos686-bit.github.io/st8-resto/unikfood.html)
2. ⚙️ → введи [Anthropic API ключ](https://console.anthropic.com/)
3. Готово

## PWA установка

**iPhone:** Safari → Поделиться → На экран "Домой"
**Android:** Chrome → меню → Установить приложение

---

Разработано ST8 AI · 2026
""")

write(os.path.join('.github','workflows','check_js.yml'), """name: Check JS Syntax
on:
  push:
    branches: [ master ]
    paths: [ '**.html' ]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python check_unikfood.py
""")

print("\nКоммит и пуш:")
run('git add .')
run('git commit -m "platform: network-first SW + README + CI"')
ok = run('git push')

print(f'\n{"="*45}')
print('✅ Готово!' if ok else '⚠️  Push не прошёл — проверь соединение')
print('='*45)
input("\nEnter для выхода...")
