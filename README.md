# Cign Smoke Break Bot

Простой Telegram-бот на aiogram v3 с лобби для «перекуров»:

- Создание лобби и инвайт-ссылки
- Присоединение по ссылке-приглашению
- Кнопки: «позвать на перекур» (Старт), «смена лобби», «ссылка приглашение в лобби»
- Кулдаун 5 минут на кнопку Старт для всех участников лобби

## Запуск

1. Установить зависимости:

```bash
python -m venv .venv
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

## Структура БД

SQLite через aiosqlite, две таблицы:

- users: id (PK, Telegram ID), lobby_id (nullable)
- lobbies: id (PK), invite_code (TEXT UNIQUE)

Можно менять схему по необходимости.


