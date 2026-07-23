from __future__ import annotations

import enum
import typing as t
from collections import defaultdict

from maxed import database, pokedex, utils

from ._common import get_parser, parse_args

if t.TYPE_CHECKING:
    from telegram import Update

    from maxed.telegram_types import DatabaseContext


class StatsMode(enum.StrEnum):
    SUMMARY = "summary"
    LIST = "list"


class Stats:
    description: t.ClassVar = "Show information about maxed Pokémon."

    @staticmethod
    async def run(update: Update, ctx: DatabaseContext) -> None:
        if update.message is None or update.effective_user is None:
            return

        parser = get_parser(Stats)
        parser.add_argument(
            "mode",
            help="how to show the information (summary|list)",
            type=StatsMode,
        )

        args = await parse_args(parser, update, ctx)
        if args is None:
            return

        with ctx.database as db:
            user_maxed = database.Maxed.by(update.effective_user.id, db)

        match args.mode:
            case StatsMode.SUMMARY:
                total = sum(maxed.count for maxed in user_maxed)
                species = sum(maxed.count > 0 for maxed in user_maxed)

                await update.message.reply_text(
                    f"{total} maxed pokemon ({species} species)",
                )
                return

            case StatsMode.LIST:
                grouped: defaultdict[int, list[database.Maxed]] = defaultdict(list)

                for maxed in user_maxed:
                    grouped[maxed.pokedex].append(maxed)

                text = ""
                for dex_number, group in grouped.items():
                    pokemon = pokedex.find_by_pokedex(dex_number, strict=True)

                    rows: list[str] = []
                    for maxed in group:
                        shadow = "Shadow" if maxed.shadow else "Regular"
                        legacy = "*" if maxed.legacy else ""

                        rows.append(f"{shadow}{legacy} {maxed.count}")

                    sort = sorted(rows)
                    sep = "\n  "

                    text += f"{pokemon.name.title()}{sep}{sep.join(sort)}\n\n"

                await utils.chunk(update, text)

            case val:
                utils.unreachable(val)
