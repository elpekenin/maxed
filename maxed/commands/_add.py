from __future__ import annotations

import typing as t

from maxed import pokedex, utils

from ._callback import Data
from ._common import get_parser, parse_args

if t.TYPE_CHECKING:
    from telegram import Update

    from maxed.tg import Context


class Add:
    description: t.ClassVar = "Register a new maxed Pokémon."

    @staticmethod
    async def run(update: Update, ctx: Context) -> None:
        parser = get_parser(Add)
        parser.add_argument("pokemon_name", help="the Pokémon being added")

        args = await parse_args(parser, update, ctx)
        if args is None:
            return

        pokemon = pokedex.find_by_name(args.pokemon_name)
        if pokemon is None:
            await utils.reply(update, f"unknown pokemon: {args.pokemon_name}")
            return

        state = Data(pokemon)
        await state.message(update, ctx, "send")
