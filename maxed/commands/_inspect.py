from __future__ import annotations

import typing as t

from maxed import utils

from ._common import get_parser, parse_args

if t.TYPE_CHECKING:
    from telegram import Update

    from maxed.tg import Context


class Inspect:
    description: t.ClassVar = "view data about a given user."

    @staticmethod
    async def run(update: Update, ctx: Context) -> None:
        if not utils.is_admin(update.effective_user):
            await utils.reply(update, "no permission")
            return

        parser = get_parser(Inspect)
        parser.add_argument("user_id", help="the user", type=int)

        args = await parse_args(parser, update, ctx)
        if args is None:
            return

        user_id = int(args.user_id)

        user_data = ctx.application.user_data.get(user_id)
        if user_data is None:
            await utils.reply(update, f"no user_data found for {user_id}")
            return

        n = sum(m.count for m in user_data.maxed)
        await utils.reply(update, f"user has {n} maxed pokemon")
