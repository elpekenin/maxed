"""Shared command context and callback data helpers."""

from __future__ import annotations

import argparse
import typing as t

from maxed import utils

if t.TYPE_CHECKING:
    from telegram import Update

    from maxed import tg

    class Command(t.Protocol):
        description: t.ClassVar[str]

        @staticmethod
        async def run(update: Update, ctx: tg.Context) -> None: ...


def get_parser(cls: type[Command]) -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        "/" + utils.snake_case(cls.__name__),
        description=cls.description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        exit_on_error=False,
        add_help=False,
    )


async def parse_args(
    parser: argparse.ArgumentParser,
    update: Update,
    ctx: tg.Context,
) -> argparse.Namespace | None:
    try:
        return parser.parse_args(ctx.args or [])
    except argparse.ArgumentError:
        await utils.reply(update, parser.format_help())
        return None
