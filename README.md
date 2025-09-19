# Cign Smoke Break Bot

Простой Telegram-бот на aiogram v3 с лобби для «перекуров»:

- Создание лобби и инвайт-ссылки
- Присоединение по ссылке-приглашению или коду
- Кнопки: «позвать на перекур» (Старт), «смена лобби», «получить ссылку-приглашение»
- Кулдаун 5 минут на кнопку Старт для всех участников лобби
- Команды: `/invite`, `/join <код>`

## Требования

- Python 3.9, 3.10 или 3.11 (рекомендуется 3.10)
- Telegram Bot Token

## Запуск

1. Установить зависимости:

```bash
python3.10 -m venv .venv  # или python3.9, python3.11
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

2. Создать файл .env:

```env
BOT_TOKEN=123456:ABC...
BOT_USERNAME=your_bot_username   # без @
```

3. Запустить бота:

```bash
python -m bot
```

## Использование

- `/start` - начать работу с ботом
- `/invite` - получить ссылку и код текущего лобби
- `/join <код>` - присоединиться к лобби по коду
- Кнопка «Получить ссылку-приглашение» - отправит ссылку и код в личные сообщения

## Структура БД

SQLite через aiosqlite, две таблицы:

- users: id (PK, Telegram ID), lobby_id (nullable)
- lobbies: id (PK), invite_code (TEXT UNIQUE)

Можно менять схему по необходимости.


