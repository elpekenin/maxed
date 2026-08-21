"""Entrypoint of the application."""

from __future__ import annotations

import argparse
import enum
import os
import typing as t
from collections import defaultdict

import dotenv
import sqlmodel
from telegram.constants import ChatAction, ParseMode
from vitrine import REMOVE_REPLY_KEYBOARD, Bot

from maxed import callback, pokebattler, pokedex, utils
from maxed.database import Maxed
from maxed.user_maxed import UserMaxed

if t.TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    import sqlalchemy
    from telegram import Chat, Message, Update, User
    from telegram.ext import ContextTypes
    from vitrine import Screen


dotenv.load_dotenv()
bot = Bot(
    token=os.getenv("BOT_TOKEN") or "",
    strict_types=True,
)

# ###
# commands
# ###


@bot.command(description="register a new maxed Pokémon")
async def add(
    pokemon_name: str,
    *,
    message: Message,
    user_maxed: UserMaxed,
) -> Screen | None:
    """Register a new maxed Pokémon.

    Returns:
        Inline keyboard to be shown.

    """
    pokemon = pokedex.find_by_name(pokemon_name)
    if pokemon is None:
        await utils.reply(message, f"unknown pokemon: {pokemon_name}")
        return None

    state = callback.State(pokemon)
    return callback.screen(state, user_maxed)


@bot.command(description="show best counters against given Pokémon")
async def counters(  # ruff:ignore[too-many-arguments]
    pokemon_name: str,
    suggestions: int = 8,
    *,
    user_maxed: UserMaxed,
    context: ContextTypes.DEFAULT_TYPE,
    chat: Chat,
    message: Message,
) -> None:
    """Find best counters against a raid."""
    pokemon = pokedex.find_by_name(pokemon_name)
    if pokemon is None:
        await utils.reply(message, f"unknown pokemon: {pokemon_name}")
        return

    await context.bot.send_chat_action(
        chat_id=chat.id,
        action=ChatAction.TYPING,
    )

    attackers = await pokebattler.counters(pokemon)

    suggested = user_maxed.get_suggestions(
        attackers,
        suggestions,
    )

    if len(suggested) == 0:
        await utils.reply(message, "you dont have good counters yet")
        return

    ids = {i for _, i in suggested}
    lookup = utils.search_string(ids)

    await utils.reply(
        message,
        "\n".join(
            [
                "Your best counters are:",
                "```",
                utils.format_table(
                    [
                        (
                            s.name + ("*" if s.legacy else ""),
                            f"{s.fast_move}, {s.charged_move}",
                            str(s.dps),
                        )
                        for s, _ in suggested
                    ],
                ),
                "```",
                f"Filter: `{lookup}`",
            ],
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


class _NonMaxedMode(enum.StrEnum):
    FAMILIES = "families"
    SPECIES = "species"


@bot.command(description="show information about non-maxed Pokémon")
async def non_maxed(
    mode: _NonMaxedMode,
    *,
    message: Message,
    user_maxed: UserMaxed,
) -> None:
    """Display non-maxed Pokémon."""
    missing: list[int] = []
    match mode:
        case _NonMaxedMode.FAMILIES:
            for family in pokedex.families:
                if all(
                    user_maxed.find(pokedex=species.pokedex) is None
                    for species in family
                ):
                    missing.extend(species.pokedex for species in family)

        case _NonMaxedMode.SPECIES:
            for family in pokedex.families:
                missing.extend(
                    [
                        species.pokedex
                        for species in family
                        if user_maxed.find(pokedex=species.pokedex) is None
                    ],
                )

        case val:
            utils.unreachable(val)

    filter_text = utils.search_string(missing)
    await utils.reply(
        message,
        f"`{filter_text}`",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


class _StatsMode(enum.StrEnum):
    SUMMARY = "summary"
    LIST = "list"


@bot.command(description="show information about maxed Pokémon")
async def stats(
    mode: _StatsMode,
    *,
    message: Message,
    user_maxed: UserMaxed,
) -> None:
    """Display maxed Pokémon."""
    match mode:
        case _StatsMode.SUMMARY:
            total = sum(item.count for item in user_maxed.items)
            species = sum(maxed.count > 0 for maxed in user_maxed.items)

            await utils.reply(message, f"{total} maxed pokemon ({species} species)")
            return

        case _StatsMode.LIST:
            grouped: defaultdict[int, list[Maxed]] = defaultdict(list)

            for maxed in user_maxed.items:
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

            await utils.reply(message, text)

        case val:
            utils.unreachable(val)


@bot.callback(callback.ChangeConfig)
async def change_config(  # ruff:ignore[unused-async]
    data: callback.ChangeConfig,
    *,
    user_maxed: UserMaxed,
) -> Screen | None:
    """Change the selected config (shadow/legacy).

    Args:
        data: query payload
        user_maxed: information about the user

    Returns:
        New set of buttons to be shown to the user

    """
    return callback.screen(data.new_state, user_maxed)


@bot.callback(callback.UpdateCounter)
async def update_counter(  # ruff:ignore[unused-async]
    data: callback.UpdateCounter,
    *,
    user: User,
    user_maxed: UserMaxed,
    session: sqlmodel.Session,
) -> Screen | None:
    """Update a database counter.

    Args:
        data: query payload
        user: who used the button
        user_maxed: information about the user

    Returns:
        New set of buttons to be shown to the user

    """
    item = user_maxed.find(
        pokedex=data.state.pokemon.pokedex,
        shadow=data.state.shadow,
        legacy=data.state.legacy,
    ) or Maxed(
        id=-1,
        user_id=user.id,
        pokedex=data.state.pokemon.pokedex,
        shadow=data.state.shadow,
        legacy=data.state.legacy,
        count=0,
    )

    item.count += data.diff

    user_maxed.update(item, session)

    return callback.screen(data.state, user_maxed)


@bot.callback(callback.ChangePokemon)
async def change_pokemon(  # ruff:ignore[unused-async]
    data: callback.ChangePokemon,
    *,
    user_maxed: UserMaxed,
) -> Screen | None:
    """Change the selected Pokémon species.

    Args:
        data: query payload
        user_maxed: information about the user

    Returns:
        New set of buttons to be shown to the user

    """
    diff = -1 if data.direction == "prev" else 1
    new_dex = data.state.pokemon.pokedex + diff

    new_pokemon = pokedex.find_by_pokedex(new_dex, strict=True)
    return callback.screen(callback.State(new_pokemon), user_maxed)


@bot.callback(callback.CloseMenu)
async def close_menu() -> Screen:  # ruff:ignore[unused-async]
    """Close button menu.

    Returns:
        New set of buttons (none) to be shown to the user.

    """
    return Screen("See you later", reply_keyboard=REMOVE_REPLY_KEYBOARD)


# ###
# providers
# ###


@bot.provide("session")
async def _session(  # ruff:ignore[unused-async]
    engine: sqlalchemy.Engine,
) -> AsyncGenerator[sqlmodel.Session]:
    """Session to the database.

    Args:
        engine: database configuration

    Yields:
        A transaction-based connection to the database

    """
    session = sqlmodel.Session(engine)
    try:
        yield session
    except:
        session.close()
        raise
    else:
        session.commit()
        session.close()


@bot.provide("message")
async def _message(update: Update) -> Message:  # ruff:ignore[unused-async]
    """Message that triggered an update.

    Args:
        update: being processed

    Returns:
        The message object

    Raises:
        ValueError: if update did not originate from a message

    """
    if update.effective_message is None:
        raise ValueError

    return update.effective_message


@bot.provide("user")
async def _user(update: Update) -> User:  # ruff:ignore[unused-async]
    """Chat who triggered an update.

    Args:
        update: being processed

    Returns:
        The user object

    Raises:
        ValueError: if update did not originate from a user

    """
    if update.effective_user is None:
        raise ValueError

    return update.effective_user


@bot.provide("chat")
async def _chat(update: Update) -> Chat:  # ruff:ignore[unused-async]
    """Chat where the update triggered.

    Args:
        update: being processed

    Returns:
        The chat object

    Raises:
        ValueError: if update did not originate in a chat

    """
    if update.effective_chat is None:
        raise ValueError

    return update.effective_chat


@bot.provide("user_maxed")
async def _user_maxed(  # ruff:ignore[unused-async]
    user: User,
    session: sqlmodel.Session,
) -> UserMaxed:
    """List of Pokémon maxed by the user.

    Args:
        user: who invoked the command
        session: a connection to the database

    Returns:
        The Pokémon maxed by this user

    """
    query = sqlmodel.select(Maxed).where(
        Maxed.user_id == user.id,
    )

    items = session.exec(query).all()

    return UserMaxed(list(items))


def main() -> int:
    """Entrypoint of the bot.

    Returns:
        Exitcode of the application.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("database_file")

    args = parser.parse_args()
    engine = sqlmodel.create_engine(f"sqlite:///{args.database_file}")
    sqlmodel.SQLModel.metadata.create_all(engine)
    bot.provide_value("engine", engine)

    bot.run()

    return 0


if __name__ == "__main__":
    ret = main()
    raise SystemExit(ret)
