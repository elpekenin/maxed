from __future__ import annotations

import argparse
import asyncio
import typing as t

from telegram.constants import ChatAction, ParseMode

from maxed import database, dialgadex, pokedex, utils

from ._common import get_parser, parse_args

if t.TYPE_CHECKING:
    from telegram import Update

    from maxed.telegram_types import DatabaseContext

    type Suggestion = tuple[dialgadex.Counter, int]


async def get_counters(pokemon: pokedex.Species) -> list[dialgadex.Counter]:
    results = await asyncio.gather(
        *(dialgadex.best_counters(typ) for typ in pokemon.best_counter_types()),
    )

    counters: list[dialgadex.Counter] = []
    for result in results:
        counters.extend(result)

    return counters


def contains(haystack: str, needle: str) -> bool:
    return needle.lower() in haystack.lower()


def is_available(
    counter: dialgadex.Counter,
    user_maxed: list[database.Maxed],
    lookup_cache: dict[int, pokedex.Species],
) -> tuple[t.Literal[True], int] | tuple[t.Literal[False], None]:
    for maxed in user_maxed:
        pokemon = lookup_cache.get(maxed.pokedex)
        if pokemon is None:
            pokemon = pokedex.find_by_pokedex(maxed.pokedex, strict=True)
            lookup_cache[maxed.pokedex] = pokemon

        if not contains(counter.name, pokemon.name):
            continue

        if contains(counter.name, "Mega ") and maxed.shadow:
            continue

        if contains(counter.name, "Shadow ") and not maxed.shadow:
            continue

        if ("*" in counter.fast or "*" in counter.charged) and not maxed.legacy:
            continue

        return True, maxed.pokedex

    return False, None


def get_suggestions(
    counters: list[dialgadex.Counter],
    user_maxed: list[database.Maxed],
    n_suggestions: int,
) -> list[Suggestion]:
    lookup_cache: dict[int, pokedex.Species] = {}

    suggestions: list[Suggestion] = []
    for counter in sorted(counters, key=lambda counter: counter.dps, reverse=True):
        if len(suggestions) >= n_suggestions:
            break

        available, dex = is_available(counter, user_maxed, lookup_cache)
        if available:
            if dex is None:
                utils.panic("impossible")

            suggestion = counter, dex
            suggestions.append(suggestion)

    return suggestions


def max_len(rows: list[tuple[str, str, str]], col_index: int) -> int:
    row = max(rows, key=lambda row: len(row[col_index]))
    return len(row[col_index])


def format_table(suggestions: list[Suggestion]) -> str:
    rows: list[tuple[str, str, str]] = []

    for counter, _ in suggestions:
        rows.append(
            (
                counter.name,
                f"{counter.fast} {counter.charged}",
                str(counter.dps),
            ),
        )

    name_len = max_len(rows, 0)
    moves_len = max_len(rows, 1)
    dps_len = max_len(rows, 2)

    return "\n".join(
        f"{name.ljust(name_len)} | {moves.ljust(moves_len)} | {dps.ljust(dps_len)}"
        for name, moves, dps in rows
    )


class Counters:
    description: t.ClassVar = "Show best counters against given Pokémon."

    @staticmethod
    async def run(update: Update, ctx: DatabaseContext) -> None:
        if update.message is None or update.effective_user is None:
            return

        parser = get_parser(Counters)
        parser.add_argument("pokemon_name", help="the defending Pokémon")
        parser.add_argument(
            "suggestions",
            help="number of different counters to suggest",
            type=int,
            nargs=argparse.OPTIONAL,
            default=8,
        )

        args = await parse_args(parser, update, ctx)
        if args is None:
            return

        pokemon = pokedex.find_by_name(args.pokemon_name)
        if pokemon is None:
            await update.message.reply_text(f"unknown pokemon: {args.pokemon_name}")
            return

        await ctx.bot.send_chat_action(
            chat_id=update.message.chat.id,
            action=ChatAction.TYPING,
        )

        counters = await get_counters(pokemon)

        with ctx.database as db:
            user_maxed = database.Maxed.by(update.effective_user.id, db)

        suggestions = get_suggestions(counters, user_maxed, args.suggestions)

        ids = {i for _, i in suggestions}
        lookup = ",".join(str(i) for i in sorted(ids))

        await update.message.reply_text(
            "\n".join(
                [
                    "Best available counters are:",
                    "```",
                    format_table(suggestions),
                    "```",
                    "",
                    f"Filter: ```{lookup}```",
                ],
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
