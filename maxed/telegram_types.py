from __future__ import annotations

import typing as t
from dataclasses import dataclass

from telegram.ext import CallbackContext, ContextTypes, ExtBot

from maxed import database
from maxed.utils import panic

if t.TYPE_CHECKING:
    from telegram.ext import Application as _App

    type Application = _App[
        ExtBot[None],
        DatabaseContext,
        UserData,
        ChatData,
        BotData,
        None,
    ]


class UserData: ...


class ChatData: ...


@dataclass
class BotData:
    database_file: str | None = None


class DatabaseContext(CallbackContext[ExtBot[None], UserData, ChatData, BotData]):
    def __init__(
        self,
        application: Application,
        chat_id: int | None = None,
        user_id: int | None = None,
    ) -> None:
        super().__init__(
            application=application,
            chat_id=chat_id,
            user_id=user_id,
        )

        if application.bot_data.database_file is None:
            panic("db_file not set")

        self.database = database.session(application.bot_data.database_file)


context_types = ContextTypes(
    context=DatabaseContext,
    bot_data=BotData,
    chat_data=ChatData,
    user_data=UserData,
)
