from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def kb_new_user() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Создать ссылку-приглашение", callback_data="create_invite")],
        ]
    )


def kb_lobby(invite_url: str, cooldown_active: bool) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Смена лобби", callback_data="change_lobby")],
        [InlineKeyboardButton(text="Получить ссылку-приглашение", callback_data="get_invite")],
    ]
    if cooldown_active:
        buttons.append([InlineKeyboardButton(text="Старт (ждите 5 мин)", callback_data="start_disabled")])
    else:
        buttons.append([InlineKeyboardButton(text="Позвать на перекур", callback_data="start")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


