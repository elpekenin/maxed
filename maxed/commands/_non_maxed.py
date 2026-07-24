from __future__ import annotations

import enum
import typing as t

from telegram.constants import ParseMode

from maxed import pokedex, utils

from ._common import get_parser, parse_args

if t.TYPE_CHECKING:
    from telegram import Update

    from maxed.tg import Context, UserData


class NonMaxedMode(enum.StrEnum):
    FAMILIES = "families"
    SPECIES = "species"


def has_maxed(dex: int, user_maxed: list[UserData.Maxed]) -> bool:
    return any(maxed.pokedex == dex for maxed in user_maxed)


def group_ids(ids: list[int]) -> str:
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


class NonMaxed:
    description: t.ClassVar = "Show information about non-maxed Pokémon."

    @staticmethod
    async def run(update: Update, ctx: Context) -> None:
        if update.effective_message is None or update.effective_user is None:
            return

        parser = get_parser(NonMaxed)
        parser.add_argument(
            "mode",
            help="what to show (families|species)",
            type=NonMaxedMode,
        )

        args = await parse_args(parser, update, ctx)
        if args is None:
            return

        if ctx.user_data is None:
            utils.panic("user_data is None")

        user_maxed = ctx.user_data.maxed

        missing: list[int] = []

        match args.mode:
            case NonMaxedMode.FAMILIES:
                for family in pokedex.families:
                    if any(
                        has_maxed(species.pokedex, user_maxed) for species in family
                    ):
                        continue

                    missing.extend(species.pokedex for species in family)

            case NonMaxedMode.SPECIES:
                for family in pokedex.families:
                    missing.extend(
                        [
                            species.pokedex
                            for species in family
                            if not has_maxed(species.pokedex, user_maxed)
                        ],
                    )

            case val:
                utils.unreachable(val)

        filter_text = group_ids(missing)
        await utils.reply(
            update,
            f"`{filter_text}`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
