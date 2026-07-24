"""Entrypoint of the application."""

from __future__ import annotations

import argparse
import typing as t

import dotenv
from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
)

from maxed import commands, tg, utils

if t.TYPE_CHECKING:
    from telegram import Update

all_commands: list[type[commands.Command]] = [
    commands.Add,
    commands.Counters,
    commands.Inspect,
    commands.NonMaxed,
    commands.Stats,
]


async def set_commands(app: tg.Application) -> None:
    await app.bot.delete_my_commands()
    await app.bot.set_my_commands(
        [
            BotCommand(
                utils.snake_case(command.__name__),
                command.description,
            )
            for command in all_commands
        ],
    )


async def fallback(update: Update, _: tg.Context) -> None:
    await utils.reply(update, "could not understand you")


def main(args: list[str] | None = None) -> int:
    dotenv.load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("database_file")

    arguments = parser.parse_args(args)

    context_types = ContextTypes(
        bot_data=tg.BotData,
        chat_data=tg.ChatData,
        user_data=tg.UserData,
    )

    app: tg.Application = (
        ApplicationBuilder()
        .context_types(context_types)
        .job_queue(None)
        .token(utils.env("BOT_TOKEN"))
        .arbitrary_callback_data(True)  # ruff:ignore[boolean-positional-value-in-call]
        .persistence(
            tg.SqlitePersistence(
                arguments.database_file,
                context_types,
            ),
        )
        .post_init(set_commands)
        .build()
    )

    app.add_handler(CallbackQueryHandler(commands.callback_query_handler))
    for command in all_commands:
        app.add_handler(
            CommandHandler(
                utils.snake_case(command.__name__),
                command.run,
            ),
        )

    app.add_handler(MessageHandler(filters=None, callback=fallback))

    app.run_polling()

    return 0


if __name__ == "__main__":
    ret = main()
    raise SystemExit(ret)
