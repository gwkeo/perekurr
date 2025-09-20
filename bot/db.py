import sqlite3
from typing import Optional, List


DB_PATH = "cign.db"


CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    lobby_id INTEGER
);
"""


CREATE_LOBBIES = """
CREATE TABLE IF NOT EXISTS lobbies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invite_code TEXT UNIQUE NOT NULL
);
"""


CREATE_COOLDOWNS = """
CREATE TABLE IF NOT EXISTS cooldowns (
    lobby_id INTEGER PRIMARY KEY,
    until_ts INTEGER NOT NULL
);
"""


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as db:
        db.execute(CREATE_USERS)
        db.execute(CREATE_LOBBIES)
        db.execute(CREATE_COOLDOWNS)
        db.commit()


def upsert_user(user_id: int, lobby_id: Optional[int]) -> None:
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT INTO users(id, lobby_id) VALUES(?, ?)\n"
            "ON CONFLICT(id) DO UPDATE SET lobby_id=excluded.lobby_id",
            (user_id, lobby_id),
        )
        db.commit()


def get_user_lobby(user_id: int) -> Optional[int]:
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute("SELECT lobby_id FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        return row[0] if row and row[0] is not None else None


def create_lobby(invite_code: str) -> int:
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute(
            "INSERT INTO lobbies(invite_code) VALUES(?)",
            (invite_code,),
        )
        db.commit()
        return cur.lastrowid


def get_lobby_by_invite(invite_code: str) -> Optional[int]:
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute(
            "SELECT id FROM lobbies WHERE invite_code=?",
            (invite_code,),
        )
        row = cur.fetchone()
        return int(row[0]) if row else None


def get_invite_by_lobby(lobby_id: int) -> Optional[str]:
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute(
            "SELECT invite_code FROM lobbies WHERE id=?",
            (lobby_id,),
        )
        row = cur.fetchone()
        return str(row[0]) if row else None


def get_lobby_members(lobby_id: int) -> List[int]:
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute(
            "SELECT id FROM users WHERE lobby_id=?",
            (lobby_id,),
        )
        rows = cur.fetchall()
        return [int(r[0]) for r in rows]


def set_cooldown(lobby_id: int, until_ts: int) -> None:
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT INTO cooldowns(lobby_id, until_ts) VALUES(?, ?)\n"
            "ON CONFLICT(lobby_id) DO UPDATE SET until_ts=excluded.until_ts",
            (lobby_id, until_ts),
        )
        db.commit()


def get_cooldown(lobby_id: int) -> Optional[int]:
    with sqlite3.connect(DB_PATH) as db:
        cur = db.execute(
            "SELECT until_ts FROM cooldowns WHERE lobby_id=?",
            (lobby_id,),
        )
        row = cur.fetchone()
        return int(row[0]) if row else None


