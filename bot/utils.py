import os
import secrets
from dataclasses import dataclass


@dataclass
class Env:
    bot_token: str
    bot_username: str


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


