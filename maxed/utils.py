from __future__ import annotations

import os
import typing as t

import telegram.constants

if t.TYPE_CHECKING:
    from telegram import Update


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


async def chunk(update: Update, text: str) -> None:
    if update.message is None:
        return

    chunk = ""
    for line in text.splitlines(keepends=True):
        new_len = len(chunk) + len(line)
        if new_len >= telegram.constants.MessageLimit.MAX_TEXT_LENGTH:
            await update.message.reply_text(chunk)
            chunk = ""
        else:
            chunk += line

    if chunk:
        await update.message.reply_text(chunk)
