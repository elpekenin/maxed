"""Callback handlers for interactive Telegram button flows."""

from __future__ import annotations

import dataclasses as d
import typing as t
import uuid

from vitrine import Button, Screen
import vitrine.callbacks as c

from maxed import pokedex, utils

if t.TYPE_CHECKING:
    from maxed.user_maxed import UserMaxed

    type Event = ChangeConfig | UpdateCounter | ChangePokemon | CloseMenu


class CustomCallbackData(c.CallbackData):
    """Change pack/unpack to allow arbitrarily-long payloads."""

    _values: t.ClassVar[dict[str, t.Self]] = {}

    def pack(self) -> str:  # ruff:ignore[undocumented-public-method]
        for _ in range(50):
            unique_uuid = uuid.uuid4().hex
            if unique_uuid not in self._values:
                break
        else:
            msg = "could not find a free UUID"
            raise c.CallbackDataError(msg)

        # vitrine wants the prefix + separator
        key = f"{self.__prefix__}{c.KEYED_SEP}{unique_uuid}"

        self._values[key] = self
        return key

    @classmethod
    def unpack(cls, data: str) -> t.Self:  # ruff:ignore[undocumented-public-method]
        value = cls._values.get(data)
        if value is None:
            msg = "key not found"
            raise c.CallbackDataError(msg)

        cls._values.pop(data)
        return value


class ChangeConfig(CustomCallbackData, prefix="config"):
    """Change configuration (shadow, legacy)."""

    new_state: State


class ChangePokemon(CustomCallbackData, prefix="poke"):
    """Change Pokemon."""

    state: State
    direction: t.Literal["prev", "next"]


class UpdateCounter(CustomCallbackData, prefix="set"):
    """Update a counter in database."""

    state: State
    diff: int


class CloseMenu(CustomCallbackData, prefix="end"):
    """Close the menu."""

    state: State


@d.dataclass(slots=True, frozen=True)
class State:
    """Inline keyboard state."""

    pokemon: pokedex.Species
    shadow: bool = d.field(default=False, kw_only=True)
    legacy: bool = d.field(default=False, kw_only=True)


def _text(state: State, user_maxed: UserMaxed) -> str:
    maxed = user_maxed.find(
        pokedex=state.pokemon.pokedex,
        shadow=state.shadow,
        legacy=state.legacy,
    )

    shadow = "Shadow" if state.shadow else "Regular"
    legacy = "with" if state.legacy else "without"
    count = 0 if maxed is None else maxed.count

    return f"{shadow} {state.pokemon.name} {legacy} legacy: {count}"


def toggle(state: State, field: t.Literal["shadow", "legacy"]) -> ChangeConfig:
    """Update a field.

    Args:
        state: current config
        field: being toggled

    Returns:
        State after the change.

    """
    new_settings = State(
        pokemon=state.pokemon,
        shadow=not state.shadow if field == "shadow" else state.shadow,
        legacy=not state.legacy if field == "legacy" else state.legacy,
    )

    return ChangeConfig(new_state=new_settings)


def screen(state: State, user_maxed: UserMaxed) -> Screen:
    """Create a keyboard for the given state.

    Args:
        state: current config
        user_maxed: user's owned Pokémon

    Returns:
        Inline keyboard to be displayed

    """
    return Screen(
        _text(state, user_maxed),
        [
            [
                Button(
                    "Shadow " + utils.repr_bool(state.shadow),
                    callback=toggle(state, "shadow"),
                ),
                Button(
                    "Legacy " + utils.repr_bool(state.legacy),
                    callback=toggle(state, "legacy"),
                ),
            ],
            [
                Button(
                    "-5",
                    callback=UpdateCounter(state=state, diff=-5),
                ),
                Button(
                    "-1",
                    callback=UpdateCounter(state=state, diff=-1),
                ),
                Button(
                    "+1",
                    callback=UpdateCounter(state=state, diff=+1),
                ),
                Button(
                    "+5",
                    callback=UpdateCounter(state=state, diff=+5),
                ),
            ],
            [
                Button(
                    "⬅️",
                    callback=ChangePokemon(state=state, direction="prev"),
                ),
                Button(
                    "➡️",
                    callback=ChangePokemon(state=state, direction="next"),
                ),
            ],
            [
                Button(
                    "Close",
                    callback=CloseMenu(state=state),
                ),
            ],
        ],
    )
