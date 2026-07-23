"""Entrypoint of the application."""

from __future__ import annotations

import argparse
import typing as t

from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
)

from maxed import commands, utils
from maxed import telegram_types as ttypes

if t.TYPE_CHECKING:
    from telegram import Update

all_commands: list[type[commands.Command]] = [
    commands.Add,
    commands.Counters,
    commands.NonMaxed,
    commands.Stats,
]


async def set_commands(app: ttypes.Application) -> None:
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


async def fallback(update: Update, _: ttypes.DatabaseContext) -> None:
    if update.effective_message is None:
        return

    await update.effective_message.reply_text("could not understand you")


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("database_file")

    arguments = parser.parse_args(args)

    app: ttypes.Application = (
        ApplicationBuilder()
        .context_types(ttypes.context_types)
        .job_queue(None)
        .token(utils.env("BOT_TOKEN"))
        .arbitrary_callback_data(arbitrary_callback_data=True)
        .post_init(set_commands)
        .build()
    )
    app.bot_data.database_file = t.cast("str", arguments.database_file)

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
