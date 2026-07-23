from __future__ import annotations

import typing as t

from maxed import pokedex

from ._callback import Data
from ._common import get_parser, parse_args

if t.TYPE_CHECKING:
    from telegram import Update

    from maxed.telegram_types import DatabaseContext


class Add:
    description: t.ClassVar = "Register a new maxed Pokémon."

    @staticmethod
    async def run(update: Update, ctx: DatabaseContext) -> None:
        if update.message is None or update.message.from_user is None:
            return

        parser = get_parser(Add)
        parser.add_argument("pokemon_name", help="the Pokémon being added")

        args = await parse_args(parser, update, ctx)
        if args is None:
            return

        pokemon = pokedex.find_by_name(args.pokemon_name)
        if pokemon is None:
            await update.message.reply_text(f"unknown pokemon: {args.pokemon_name}")
            return

        state = Data(pokemon)
        await state.message(update, ctx, "send")
