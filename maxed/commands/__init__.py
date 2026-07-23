"""Telegram command handlers for the bot."""

from __future__ import annotations

import typing as t

from ._add import Add as Add
from ._callback import callback_query_handler as callback_query_handler
from ._counters import Counters as Counters
from ._non_maxed import NonMaxed as NonMaxed
from ._stats import Stats as Stats

if t.TYPE_CHECKING:
    from ._common import Command as Command
