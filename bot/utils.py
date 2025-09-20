import os
import secrets


class Env:
    def __init__(self, bot_token: str, bot_username: str):
        self.bot_token = bot_token
        self.bot_username = bot_username


def get_env() -> Env:
    from dotenv import load_dotenv

    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    username = os.getenv("BOT_USERNAME", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is required in .env")
    if not username:
        raise RuntimeError("BOT_USERNAME is required in .env")
    return Env(bot_token=token, bot_username=username)


def generate_invite_code() -> str:
    return secrets.token_urlsafe(8)


