import time
import telebot
from telebot import types

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


def encode_invite(code: str) -> str:
    # Простая кодировка для deep linking
    import base64
    import urllib.parse
    payload = f"invite_{code}"
    encoded = base64.urlsafe_b64encode(payload.encode()).decode().rstrip('=')
    return urllib.parse.quote(encoded)


def decode_invite(encoded: str) -> str:
    # Декодировка для deep linking
    import base64
    import urllib.parse
    try:
        decoded = urllib.parse.unquote(encoded)
        # Добавляем padding если нужно
        missing_padding = len(decoded) % 4
        if missing_padding:
            decoded += '=' * (4 - missing_padding)
        payload = base64.urlsafe_b64decode(decoded).decode()
        return payload
    except Exception:
        return ""


def is_cooldown_active(lobby_id: int) -> bool:
    until_ts = get_cooldown(lobby_id)
    return bool(until_ts and until_ts > int(time.time()))


def start_handler(msg: types.Message):
    # Проверка payload для авто-присоединения по ссылке t.me/bot?start=invite_xxx
    lobby_id = None
    if msg.text and len(msg.text.split()) > 1:
        payload = msg.text.split(maxsplit=1)[1]
        data = decode_invite(payload)
        if data and data.startswith("invite_"):
            code = data.replace("invite_", "", 1)
            lobby_id = get_lobby_by_invite(code)
            if lobby_id is not None:
                upsert_user(msg.from_user.id, lobby_id)

    if lobby_id is None:
        lobby_id = get_user_lobby(msg.from_user.id)

    if lobby_id is None:
        upsert_user(msg.from_user.id, None)
        bot.send_message(
            msg.chat.id,
            "Добро пожаловать! Создайте своё лобби и пригласите друзей.",
            reply_markup=kb_new_user(),
        )
        return

    invite_code = get_invite_by_lobby(lobby_id)
    env = get_env()
    invite_url = f"https://t.me/{env.bot_username}?start={encode_invite(invite_code)}"
    cooldown_active = is_cooldown_active(lobby_id)
    bot.send_message(
        msg.chat.id,
        "Вы в лобби. Выберите действие:",
        reply_markup=kb_lobby(invite_url, cooldown_active),
    )


def on_create_invite(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    # Создать лобби и привязать пользователя
    code = generate_invite_code()
    lobby_id = create_lobby(code)
    upsert_user(user_id, lobby_id)

    env = get_env()
    invite_url = f"https://t.me/{env.bot_username}?start={encode_invite(code)}"
    bot.edit_message_text(
        "Лобби создано. Делитесь ссылкой и зовите друзей!",
        cb.message.chat.id,
        cb.message.message_id,
        reply_markup=kb_lobby(invite_url, cooldown_active=False),
    )
    bot.answer_callback_query(cb.id)


def on_change_lobby(cb: types.CallbackQuery):
    # Отвязать пользователя от текущего лобби
    upsert_user(cb.from_user.id, None)
    bot.edit_message_text(
        "Вы вышли из лобби. Создайте новое или войдите по ссылке.",
        cb.message.chat.id,
        cb.message.message_id,
        reply_markup=kb_new_user(),
    )
    bot.answer_callback_query(cb.id)


def on_start(cb: types.CallbackQuery):
    if cb.data == "start_disabled":
        bot.answer_callback_query(cb.id, "Кнопка временно недоступна (кулдаун 5 минут)", show_alert=False)
        return

    lobby_id = get_user_lobby(cb.from_user.id)
    if lobby_id is None:
        bot.answer_callback_query(cb.id, "Сначала войдите в лобби", show_alert=True)
        return

    if is_cooldown_active(lobby_id):
        bot.answer_callback_query(cb.id, "Подождите завершения кулдауна", show_alert=False)
        return

    # Установить кулдаун
    set_cooldown(lobby_id, int(time.time()) + COOLDOWN_SECONDS)

    # Разослать уведомление всем участникам
    members = get_lobby_members(lobby_id)
    name = cb.from_user.full_name or cb.from_user.first_name or "Пользователь"
    text = f"{name} позвал(а) на перекур!"
    for uid in members:
        try:
            bot.send_message(uid, text)
        except Exception:
            pass

    # Обновить клавиатуру в текущем сообщении
    invite_code = get_invite_by_lobby(lobby_id)
    env = get_env()
    invite_url = f"https://t.me/{env.bot_username}?start={encode_invite(invite_code)}"
    bot.edit_message_reply_markup(
        cb.message.chat.id,
        cb.message.message_id,
        reply_markup=kb_lobby(invite_url, cooldown_active=True)
    )
    bot.answer_callback_query(cb.id, "Сигнал отправлен всем в лобби")


def on_get_invite(cb: types.CallbackQuery):
    lobby_id = get_user_lobby(cb.from_user.id)
    if lobby_id is None:
        bot.answer_callback_query(cb.id, "Вы не в лобби", show_alert=True)
        return
    code = get_invite_by_lobby(lobby_id)
    if not code:
        bot.answer_callback_query(cb.id, "Нет кода приглашения", show_alert=True)
        return
    env = get_env()
    url = f"https://t.me/{env.bot_username}?start={encode_invite(code)}"
    txt = (
        "Приглашение в лобби:\n"
        f"Ссылка: {url}\n"
        f"Код: {code}\n\n"
        "Друг также может отправить боту: /join " + code
    )
    bot.send_message(cb.from_user.id, txt)
    bot.answer_callback_query(cb.id, "Ссылка отправлена в личные сообщения")


def cmd_invite(msg: types.Message):
    lobby_id = get_user_lobby(msg.from_user.id)
    if lobby_id is None:
        bot.send_message(msg.chat.id, "Вы не в лобби. Создайте или присоединитесь.")
        return
    code = get_invite_by_lobby(lobby_id)
    env = get_env()
    url = f"https://t.me/{env.bot_username}?start={encode_invite(code)}"
    bot.send_message(msg.chat.id, f"Ссылка: {url}\nКод: {code}")


def cmd_join(msg: types.Message):
    args = (msg.text or "").split()
    if len(args) < 2:
        bot.send_message(msg.chat.id, "Использование: /join <код>")
        return
    code = args[1].strip()
    lobby_id = get_lobby_by_invite(code)
    if lobby_id is None:
        bot.send_message(msg.chat.id, "Неверный код приглашения")
        return
    upsert_user(msg.from_user.id, lobby_id)
    env = get_env()
    url = f"https://t.me/{env.bot_username}?start={encode_invite(code)}"
    cooldown_active = is_cooldown_active(lobby_id)
    bot.send_message(
        msg.chat.id,
        "Вы присоединились к лобби.",
        reply_markup=kb_lobby(url, cooldown_active),
    )


def main():
    global bot
    env = get_env()
    init_db()

    bot = telebot.TeleBot(env.bot_token)

    @bot.message_handler(commands=['start'])
    def handle_start(msg):
        start_handler(msg)

    @bot.message_handler(commands=['invite'])
    def handle_invite(msg):
        cmd_invite(msg)

    @bot.message_handler(commands=['join'])
    def handle_join(msg):
        cmd_join(msg)

    @bot.callback_query_handler(func=lambda call: call.data == "create_invite")
    def handle_create_invite(call):
        on_create_invite(call)

    @bot.callback_query_handler(func=lambda call: call.data == "change_lobby")
    def handle_change_lobby(call):
        on_change_lobby(call)

    @bot.callback_query_handler(func=lambda call: call.data == "get_invite")
    def handle_get_invite(call):
        on_get_invite(call)

    @bot.callback_query_handler(func=lambda call: call.data in ["start", "start_disabled"])
    def handle_start_callback(call):
        on_start(call)

    bot.polling(none_stop=True, skip_pending=True)


if __name__ == "__main__":
    main()


