"""Callback handlers for interactive Telegram button flows."""

from __future__ import annotations

import dataclasses as d
import typing as t
from copy import copy

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from maxed import pokedex, utils
from maxed.tg import UserData

if t.TYPE_CHECKING:
    from telegram import Update

    from maxed.tg import Context

    type CallbackEvent = ChangeSettings | StorePokemon | ChangePokemon | Close


@d.dataclass(slots=True)
class Data:
    pokemon: pokedex.Species
    shadow: bool = d.field(default=False, kw_only=True)
    legacy: bool = d.field(default=False, kw_only=True)

    def text(self, user_data: UserData) -> str:
        index = user_data.index(
            pokedex=self.pokemon.pokedex,
            shadow=self.shadow,
            legacy=self.legacy,
        )

        shadow = "Shadow" if self.shadow else "Regular"
        legacy = "with" if self.legacy else "without"
        count = user_data.maxed[index].count if index is not None else 0

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
        ctx: Context,
        mode: t.Literal["send", "edit", "close"],
    ) -> None:
        if update.effective_message is None:
            return

        if ctx.user_data is None:
            utils.panic("user_data is None")

        match mode:
            case "send":
                await update.effective_message.reply_text(
                    self.text(ctx.user_data),
                    reply_markup=self.keyboard(),
                )
            case "edit":
                await update.effective_message.edit_text(
                    self.text(ctx.user_data),
                    reply_markup=self.keyboard(),
                )
            case "close":
                await update.effective_message.edit_text(
                    self.text(ctx.user_data),
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


async def callback_query_handler(update: Update, ctx: Context) -> None:
    if update.callback_query is None or update.callback_query.data is None:
        return

    event = t.cast("CallbackEvent", update.callback_query.data)

    if isinstance(event, ChangeSettings):
        await event.new_settings.message(update, ctx, "edit")
    elif isinstance(event, StorePokemon):
        if ctx.user_data is None:
            utils.panic("user_data is None")

        index = ctx.user_data.index(
            pokedex=event.data.pokemon.pokedex,
            shadow=event.data.shadow,
            legacy=event.data.legacy,
        )

        maxed = (
            ctx.user_data.maxed[index]
            if index is not None
            else UserData.Maxed(
                pokedex=event.data.pokemon.pokedex,
                shadow=event.data.shadow,
                legacy=event.data.legacy,
            )
        )

        maxed.count += event.diff

        if not ctx.user_data.store(maxed):
            await utils.reply(update, "update could not be stored")

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
