"""Utilities to be re-used across the bot."""

from __future__ import annotations

import typing as t

from telegram.constants import MessageLimit, ParseMode

if t.TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from telegram import Message

    type Row = Sequence[str]


def unreachable(value: t.Never) -> t.NoReturn:
    """Mark a code branch as unreachable.

    Args:
        value: value that broke some invariant

    """
    message = f"unreachable: {value}"
    panic(message)


def panic(message: str) -> t.NoReturn:
    """Throw an error on un-recoverable situation.

    Args:
        message: to be shown on exception

    Raises:
        SystemExit: always

    """
    raise SystemExit(message)


def repr_bool(value: bool) -> str:  # ruff: ignore[boolean-type-hint-positional-argument]
    """Represent a bool with an emoji.

    Args:
        value: The boolean to represent

    Returns:
        The emoji as a string

    """
    if value:
        return "✅"

    return "❌"


async def reply(
    message: Message,
    text: str,
    *,
    parse_mode: ParseMode | None = None,
) -> None:
    """Reply to a message, takes care of slicing long texts into multiple messages.

    Args:
        message: the message to which we are replying
        text: reply to be sent
        parse_mode: how to format the text

    """
    chunk = ""
    for line in text.splitlines(keepends=True):
        new_len = len(chunk) + len(line)
        if new_len >= MessageLimit.MAX_TEXT_LENGTH:
            await message.reply_text(
                chunk,
                parse_mode=parse_mode,
            )
            chunk = line
        else:
            chunk += line

    if chunk:
        await message.reply_text(
            chunk,
            parse_mode=parse_mode,
        )


def format_table(rows: Sequence[Row]) -> str:
    """Align a table of strings.

    Args:
        rows: List of rows (list of strings)

    Returns:
        The formatted table

    Raises:
        ValueError: If rows' lengths don't match

    """
    n_cols = len(rows[0])
    for row in rows:
        if n_cols != len(row):
            msg = "all rows must have the same length"
            raise ValueError(msg)

    lengths = [max(map(len, [row[i] for row in rows])) for i in range(n_cols)]

    padded_rows = [
        " | ".join(
            [row[i].ljust(lengths[i]) for i in range(n_cols)],
        )
        for row in rows
    ]
    return "\n".join(padded_rows)


def contains(haystack: str, needle: str) -> bool:
    """Check if a string contains another one.

    Args:
        haystack: container
        needle: the sub-string being searched

    Returns:
        Whether a match is found.

    """
    return needle.lower() in haystack.lower()


def search_string(ids: Iterable[int]) -> str:
    """Create a search string.

    Args:
        ids: List of Pokemon ids to be searched

    Returns:
        Filter that finds all of them.

    """
    ids = sorted(set(ids))

    groups: list[str] = []
    start = previous = ids[0]

    for current in ids[1:]:
        if current == previous + 1:
            previous = current
            continue

        groups.append(f"{start}-{previous}" if start != previous else str(start))
        start = previous = current

    groups.append(f"{start}-{previous}" if start != previous else str(start))
    return ",".join(groups)
