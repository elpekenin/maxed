from __future__ import annotations

import typing as t

from ._bot_data import BotData as BotData  # ruff:ignore[typing-only-first-party-import]
from ._chat_data import (
    ChatData as ChatData,  # ruff:ignore[typing-only-first-party-import]
)
from ._sqlite_persistence import SqlitePersistence as SqlitePersistence
from ._user_data import (
    UserData as UserData,  # ruff:ignore[typing-only-first-party-import]
)

if t.TYPE_CHECKING:
    from telegram.ext import Application as _App
    from telegram.ext import CallbackContext, ExtBot

    type Bot = ExtBot[None]
    type Context = CallbackContext[
        Bot,
        UserData,
        ChatData,
        BotData,
    ]

    type Application = _App[
        Bot,
        Context,
        UserData,
        ChatData,
        BotData,
        None,
    ]
