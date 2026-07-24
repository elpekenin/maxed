from __future__ import annotations

import pickle  # ruff:ignore[suspicious-pickle-import]
import typing as t

from telegram.ext import BasePersistence, ContextTypes
from telegram.ext._utils.types import (  # ruff:ignore[import-private-name]
    ConversationDict,
)

from maxed import database

if t.TYPE_CHECKING:
    import sqlite3

    from telegram.ext._utils.types import BD, CCT, CD, UD, CDCData, ConversationKey
    from typing_extensions import ContextManager


class IntegrityError(Exception): ...


def serialize(data: object) -> bytes:
    return pickle.dumps(data)


def deserialize[T](_: type[T], blob: bytes) -> T:
    return pickle.loads(blob)  # ruff:ignore[suspicious-pickle-usage]


class SqlitePersistence(BasePersistence["UD", "CD", "BD"]):
    def __init__(
        self,
        database_file: str,
        context_types: ContextTypes[CCT, UD, CD, BD],
    ) -> None:
        super().__init__()

        self.database_file = database_file
        self.context_types = context_types

        with self.session() as db:
            db.execute(
                """
                    CREATE TABLE IF NOT EXISTS user_data (
                        user_id INTEGER PRIMARY KEY NOT NULL,
                        data BLOB NOT NULL
                    ) STRICT;
                """,
            )

            db.execute(
                """
                    CREATE TABLE IF NOT EXISTS chat_data (
                        chat_id INTEGER PRIMARY KEY NOT NULL,
                        data BLOB NOT NULL
                    ) STRICT;
                """,
            )

            db.execute(
                """
                    CREATE TABLE IF NOT EXISTS bot_data (
                        data BLOB NOT NULL
                    ) STRICT;
                """,
            )

            db.execute(
                """
                    CREATE TABLE IF NOT EXISTS conversations (
                        name TEXT NOT NULL,
                        state BLOB NOT NULL
                    ) STRICT;
                """,
            )

    def session(self) -> ContextManager[sqlite3.Connection]:
        return database.session(self.database_file)

    async def get_bot_data(self) -> BD:
        with self.session() as db:
            row = db.execute("SELECT * FROM bot_data").fetchone()
            if row is None:
                return self.context_types.bot_data()

            # it is a single-element tuple
            return deserialize(self.context_types.bot_data, row[0])

    async def update_bot_data(self, data: BD) -> None:
        with self.session() as db:
            db.execute("DELETE FROM bot_data")
            db.execute(
                "INSERT INTO bot_data (data) VALUES (?)",
                [serialize(data)],
            )

    async def refresh_bot_data(self, bot_data: BD) -> None:
        _ = self
        _ = bot_data

    async def get_user_data(self) -> dict[int, UD]:
        ret: dict[int, UD] = {}

        with self.session() as db:
            rows = db.execute("SELECT * FROM user_data").fetchall()
            for user_id, blob in rows:
                ret[user_id] = deserialize(self.context_types.user_data, blob)

        return ret

    async def update_user_data(self, user_id: int, data: UD) -> None:
        await self.drop_user_data(user_id)
        with self.session() as db:
            db.execute(
                "INSERT INTO user_data (user_id, data) VALUES (?, ?)",
                [user_id, serialize(data)],
            )

    async def refresh_user_data(self, user_id: int, user_data: UD) -> None:
        _ = self
        _ = user_id
        _ = user_data

    async def drop_user_data(self, user_id: int) -> None:
        with self.session() as db:
            db.execute("DELETE FROM user_data WHERE user_id = ?", [user_id])

    async def get_chat_data(self) -> dict[int, CD]:
        ret: dict[int, CD] = {}

        with self.session() as db:
            rows = db.execute("SELECT * FROM chat_data").fetchall()
            for chat_id, blob in rows:
                ret[chat_id] = deserialize(self.context_types.chat_data, blob)

        return ret

    async def update_chat_data(self, chat_id: int, data: CD) -> None:
        await self.drop_chat_data(chat_id)
        with self.session() as db:
            db.execute(
                "INSERT INTO chat_data (chat_id, data) VALUES (?, ?)",
                [chat_id, serialize(data)],
            )

    async def refresh_chat_data(self, chat_id: int, chat_data: CD) -> None:
        _ = self
        _ = chat_id
        _ = chat_data

    async def drop_chat_data(self, chat_id: int) -> None:
        with self.session() as db:
            db.execute("DELETE FROM chat_data WHERE chat_id = ?", [chat_id])

    async def get_callback_data(self) -> None:
        _ = self

    async def update_callback_data(self, data: CDCData) -> None:
        _ = self
        _ = data

    async def get_conversations(self, name: str) -> ConversationDict:
        with self.session() as db:
            row = db.execute(
                "SELECT state FROM conversations WHERE name = ?",
                [name],
            ).fetchone()

            if row is None:
                return {}

            return deserialize(ConversationDict, row[0])

    async def update_conversation(
        self,
        name: str,
        key: ConversationKey,
        new_state: object | None,
    ) -> None:
        with self.session() as db:
            row = db.execute(
                "SELECT state FROM conversations WHERE name = ?",
                [name],
            ).fetchone()

            blob: bytes | None = row[0] if row is not None else None
            state: ConversationDict = (
                deserialize(
                    ConversationDict,
                    blob,
                )
                if blob is not None
                else {}
            )

            if state[key] == new_state:
                return

            state[key] = new_state

            db.execute(
                "DELETE FROM conversation WHERE name = ?",
                [name],
            )
            db.execute(
                "INSERT INTO conversations (name, state) VALUES (?, ?)",
                [name, serialize(state)],
            )

    async def flush(self) -> None:
        # other methods update database at the moment, nothing to flush
        _ = self
