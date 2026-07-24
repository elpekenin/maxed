from __future__ import annotations

import enum
import typing as t
from collections import defaultdict

from maxed import pokedex, utils

from ._common import get_parser, parse_args

if t.TYPE_CHECKING:
    from telegram import Update

    from maxed.tg import Context, UserData


class StatsMode(enum.StrEnum):
    SUMMARY = "summary"
    LIST = "list"


class Stats:
    description: t.ClassVar = "Show information about maxed Pokémon."

    @staticmethod
    async def run(update: Update, ctx: Context) -> None:
        parser = get_parser(Stats)
        parser.add_argument(
            "mode",
            help="how to show the information (summary|list)",
            type=StatsMode,
        )

        args = await parse_args(parser, update, ctx)
        if args is None:
            return

        if ctx.user_data is None:
            utils.panic("user_data is None")
        user_maxed = ctx.user_data.maxed

        match args.mode:
            case StatsMode.SUMMARY:
                total = sum(maxed.count for maxed in user_maxed)
                species = sum(maxed.count > 0 for maxed in user_maxed)

                await utils.reply(update, f"{total} maxed pokemon ({species} species)")
                return

            case StatsMode.LIST:
                grouped: defaultdict[int, list[UserData.Maxed]] = defaultdict(list)

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

                await utils.reply(update, text)

            case val:
                utils.unreachable(val)
