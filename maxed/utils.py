from __future__ import annotations

import os
import typing as t

from telegram.constants import MessageLimit, ParseMode

if t.TYPE_CHECKING:
    from telegram import Update, User


def unreachable(value: t.Never) -> t.NoReturn:
    message = f"unreachable: {value}"
    raise panic(message)


def panic(message: str) -> t.NoReturn:
    raise SystemExit(message)


def snake_case(txt: str) -> str:
    out = ""

    for c in txt:
        lower = c.lower()
        if c != lower:
            out += "_" + lower
        else:
            out += c

    return out.lstrip("_")


def repr_bool(value: bool) -> str:  # ruff: ignore[boolean-type-hint-positional-argument]
    if value:
        return "✅"

    return "❌"


def env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        panic(f"missing ${name}")

    return value


async def reply(
    update: Update,
    text: str,
    *,
    parse_mode: ParseMode | None = None,
) -> None:
    if update.effective_message is None:
        return

    chunk = ""
    for line in text.splitlines(keepends=True):
        new_len = len(chunk) + len(line)
        if new_len >= MessageLimit.MAX_TEXT_LENGTH:
            await update.effective_message.reply_text(
                chunk,
                parse_mode=parse_mode,
            )
            chunk = line
        else:
            chunk += line

    if chunk:
        await update.effective_message.reply_text(
            chunk,
            parse_mode=parse_mode,
        )


def is_admin(user: User | None) -> bool:
    if user is None:
        return False

    admins = env("ADMINS")
    return str(user.id) in admins
