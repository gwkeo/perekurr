import asyncio
import time
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.payload import decode_payload

from .db import (
    init_db,
    create_lobby,
    get_lobby_by_invite,
    upsert_user,
    get_user_lobby,
    get_invite_by_lobby,
    get_lobby_members,
    get_cooldown,
    set_cooldown,
)
from .keyboards import kb_new_user, kb_lobby
from .utils import get_env, generate_invite_code


COOLDOWN_SECONDS = 300


async def start_handler(msg: Message, bot: Bot):
    # Проверка payload для авто-присоединения по ссылке t.me/bot?start=invite_xxx
    lobby_id = None
    if msg.text and len(msg.text.split()) > 1:
        payload = msg.text.split(maxsplit=1)[1]
        data = decode_payload(payload)
        if data and data.startswith("invite_"):
            code = data.replace("invite_", "", 1)
            lobby_id = await get_lobby_by_invite(code)
            if lobby_id is not None:
                await upsert_user(msg.from_user.id, lobby_id)

    if lobby_id is None:
        lobby_id = await get_user_lobby(msg.from_user.id)

    if lobby_id is None:
        await upsert_user(msg.from_user.id, None)
        await msg.answer(
            "Добро пожаловать! Создайте своё лобби и пригласите друзей.",
            reply_markup=kb_new_user(),
        )
        return

    invite_code = await get_invite_by_lobby(lobby_id)
    env = get_env()
    invite_url = f"https://t.me/{env.bot_username}?start={encode_invite(invite_code)}"
    cooldown_active = await is_cooldown_active(lobby_id)
    await msg.answer(
        "Вы в лобби. Выберите действие:",
        reply_markup=kb_lobby(invite_url, cooldown_active),
    )


def encode_invite(code: str) -> str:
    from aiogram.utils.payload import encode_payload

    return encode_payload(f"invite_{code}")


async def is_cooldown_active(lobby_id: int) -> bool:
    until_ts = await get_cooldown(lobby_id)
    return bool(until_ts and until_ts > int(time.time()))


async def on_create_invite(cb: CallbackQuery, bot: Bot):
    user_id = cb.from_user.id
    # Создать лобби и привязать пользователя
    code = generate_invite_code()
    lobby_id = await create_lobby(code)
    await upsert_user(user_id, lobby_id)

    env = get_env()
    invite_url = f"https://t.me/{env.bot_username}?start={encode_invite(code)}"
    await cb.message.edit_text(
        "Лобби создано. Делитесь ссылкой и зовите друзей!",
        reply_markup=kb_lobby(invite_url, cooldown_active=False),
    )
    await cb.answer()


async def on_change_lobby(cb: CallbackQuery, bot: Bot):
    # Отвязать пользователя от текущего лобби
    await upsert_user(cb.from_user.id, None)
    await cb.message.edit_text(
        "Вы вышли из лобби. Создайте новое или войдите по ссылке.",
        reply_markup=kb_new_user(),
    )
    await cb.answer()


async def on_start(cb: CallbackQuery, bot: Bot):
    if cb.data == "start_disabled":
        await cb.answer("Кнопка временно недоступна (кулдаун 5 минут)", show_alert=False)
        return

    lobby_id = await get_user_lobby(cb.from_user.id)
    if lobby_id is None:
        await cb.answer("Сначала войдите в лобби", show_alert=True)
        return

    if await is_cooldown_active(lobby_id):
        await cb.answer("Подождите завершения кулдауна", show_alert=False)
        return

    # Установить кулдаун
    await set_cooldown(lobby_id, int(time.time()) + COOLDOWN_SECONDS)

    # Разослать уведомление всем участникам
    members = await get_lobby_members(lobby_id)
    name = cb.from_user.full_name
    text = f"{name} позвал(а) на перекур!"
    for uid in members:
        try:
            await bot.send_message(uid, text)
        except Exception:
            pass

    # Обновить клавиатуру в текущем сообщении
    invite_code = await get_invite_by_lobby(lobby_id)
    env = get_env()
    invite_url = f"https://t.me/{env.bot_username}?start={encode_invite(invite_code)}"
    await cb.message.edit_reply_markup(reply_markup=kb_lobby(invite_url, cooldown_active=True))
    await cb.answer("Сигнал отправлен всем в лобби")


async def on_get_invite(cb: CallbackQuery, bot: Bot):
    lobby_id = await get_user_lobby(cb.from_user.id)
    if lobby_id is None:
        await cb.answer("Вы не в лобби", show_alert=True)
        return
    code = await get_invite_by_lobby(lobby_id)
    if not code:
        await cb.answer("Нет кода приглашения", show_alert=True)
        return
    env = get_env()
    url = f"https://t.me/{env.bot_username}?start={encode_invite(code)}"
    txt = (
        "Приглашение в лобби:\n"
        f"Ссылка: {url}\n"
        f"Код: {code}\n\n"
        "Друг также может отправить боту: /join " + code
    )
    await bot.send_message(cb.from_user.id, txt)
    await cb.answer("Ссылка отправлена в личные сообщения")


async def cmd_invite(msg: Message, bot: Bot):
    lobby_id = await get_user_lobby(msg.from_user.id)
    if lobby_id is None:
        await msg.answer("Вы не в лобби. Создайте или присоединитесь.")
        return
    code = await get_invite_by_lobby(lobby_id)
    env = get_env()
    url = f"https://t.me/{env.bot_username}?start={encode_invite(code)}"
    await msg.answer(f"Ссылка: {url}\nКод: {code}")


async def cmd_join(msg: Message, bot: Bot):
    args = (msg.text or "").split()
    if len(args) < 2:
        await msg.answer("Использование: /join <код>")
        return
    code = args[1].strip()
    lobby_id = await get_lobby_by_invite(code)
    if lobby_id is None:
        await msg.answer("Неверный код приглашения")
        return
    await upsert_user(msg.from_user.id, lobby_id)
    env = get_env()
    url = f"https://t.me/{env.bot_username}?start={encode_invite(code)}"
    cooldown_active = await is_cooldown_active(lobby_id)
    await msg.answer(
        "Вы присоединились к лобби.",
        reply_markup=kb_lobby(url, cooldown_active),
    )


async def main() -> None:
    env = get_env()
    await init_db()

    bot = Bot(env.bot_token)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(cmd_invite, Command(commands={"invite"}))
    dp.message.register(cmd_join, Command(commands={"join"}))
    dp.callback_query.register(on_create_invite, F.data == "create_invite")
    dp.callback_query.register(on_change_lobby, F.data == "change_lobby")
    dp.callback_query.register(on_get_invite, F.data == "get_invite")
    dp.callback_query.register(on_start, F.data.in_({"start", "start_disabled"}))

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        import uvloop  # type: ignore

        uvloop.install()
    except Exception:
        pass
    asyncio.run(main())


