"""Callback handlers for interactive Telegram button flows."""

from __future__ import annotations

import dataclasses as d
import typing as t
from copy import copy

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from maxed import database, pokedex, utils

if t.TYPE_CHECKING:
    from peewee import Database
    from telegram import Update

    from maxed.telegram_types import DatabaseContext

    type CallbackEvent = ChangeSettings | StorePokemon | ChangePokemon | Close


@d.dataclass(slots=True)
class Data:
    pokemon: pokedex.Species
    shadow: bool = d.field(default=False, kw_only=True)
    legacy: bool = d.field(default=False, kw_only=True)

    def text(self, db: Database, user_id: int) -> str:
        maxed = (
            database.Maxed.select()
            .where(
                database.Maxed.user_id == user_id,
                database.Maxed.pokedex == self.pokemon.pokedex,
                database.Maxed.shadow == self.shadow,
                database.Maxed.legacy == self.legacy,
            )
            .first(db)
        )

        shadow = "Shadow" if self.shadow else "Regular"
        legacy = "with" if self.legacy else "without"
        count = maxed.count if maxed is not None else 0

        return f"{shadow} {self.pokemon.name} {legacy} legacy: {count}"

    def toggle(self, field: t.Literal["shadow", "legacy"]) -> ChangeSettings:
        new_settings = copy(self)
        setattr(new_settings, field, not getattr(self, field))
        return ChangeSettings(new_settings)

    def keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Shadow " + utils.repr_bool(self.shadow),
                        callback_data=self.toggle("shadow"),
                    ),
                    InlineKeyboardButton(
                        "Legacy " + utils.repr_bool(self.legacy),
                        callback_data=self.toggle("legacy"),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "-5",
                        callback_data=StorePokemon(data=self, diff=-5),
                    ),
                    InlineKeyboardButton(
                        "-1",
                        callback_data=StorePokemon(data=self, diff=-1),
                    ),
                    InlineKeyboardButton(
                        "+1",
                        callback_data=StorePokemon(data=self, diff=+1),
                    ),
                    InlineKeyboardButton(
                        "+5",
                        callback_data=StorePokemon(data=self, diff=+5),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "⬅️",
                        callback_data=ChangePokemon(data=self, direction="prev"),
                    ),
                    InlineKeyboardButton(
                        "➡️",
                        callback_data=ChangePokemon(data=self, direction="next"),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "Close",
                        callback_data=Close(self),
                    ),
                ],
            ],
        )

    async def message(
        self,
        update: Update,
        ctx: DatabaseContext,
        mode: t.Literal["send", "edit", "close"],
    ) -> None:
        if update.effective_user is None:
            return

        match mode:
            case "send":
                if update.message is None:
                    return

                with ctx.database as db:
                    await update.message.reply_text(
                        self.text(db, update.effective_user.id),
                        reply_markup=self.keyboard(),
                    )
            case "edit":
                if update.effective_message is None:
                    return

                with ctx.database as db:
                    await update.effective_message.edit_text(
                        self.text(db, update.effective_user.id),
                        reply_markup=self.keyboard(),
                    )
            case "close":
                if update.effective_message is None:
                    return

                with ctx.database as db:
                    await update.effective_message.edit_text(
                        self.text(db, update.effective_user.id),
                    )
            case _:
                utils.unreachable(mode)


@d.dataclass(slots=True)
class ChangeSettings:
    new_settings: Data


@d.dataclass(slots=True)
class StorePokemon:
    data: Data
    diff: int


@d.dataclass(slots=True)
class ChangePokemon:
    data: Data
    direction: t.Literal["prev", "next"]


@d.dataclass(slots=True)
class Close:
    data: Data


async def callback_query_handler(update: Update, ctx: DatabaseContext) -> None:
    if (
        update.callback_query is None
        or update.callback_query.data is None
        or update.effective_message is None
        or update.effective_user is None
    ):
        return

    event = t.cast("CallbackEvent", update.callback_query.data)

    if isinstance(event, ChangeSettings):
        await event.new_settings.message(update, ctx, "edit")
    elif isinstance(event, StorePokemon):
        with ctx.database as db:
            maxed: database.Maxed | None = (
                database.Maxed.select()
                .where(
                    database.Maxed.user_id == update.effective_user.id,
                    database.Maxed.pokedex == event.data.pokemon.pokedex,
                    database.Maxed.shadow == event.data.shadow,
                    database.Maxed.legacy == event.data.legacy,
                )
                .first(db)
            )

            if maxed is None:
                database.Maxed.insert(
                    user_id=update.effective_user.id,
                    pokedex=event.data.pokemon.pokedex,
                    shadow=event.data.shadow,
                    legacy=event.data.legacy,
                    count=event.diff,
                ).execute(db)
            else:
                _ = (
                    database.Maxed.update(count=maxed.count + event.diff)
                    .where(database.Maxed.id == maxed.id)
                    .execute(db)
                )

        await event.data.message(update, ctx, "edit")
    elif isinstance(event, ChangePokemon):
        diff = -1 if event.direction == "prev" else 1
        new_dex = event.data.pokemon.pokedex + diff

        new_pokemon = pokedex.find_by_pokedex(new_dex, strict=True)
        await Data(new_pokemon).message(update, ctx, "edit")
    elif isinstance(event, Close):
        await event.data.message(update, ctx, "close")
    else:
        utils.unreachable(type(event))
