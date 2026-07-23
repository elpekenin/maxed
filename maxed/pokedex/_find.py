from __future__ import annotations

import typing as t

from ._data import families

if t.TYPE_CHECKING:
    from ._types import Species


class PokemonNotFoundError(Exception): ...


def find_by_name(name: str) -> Species | None:
    for family in families:
        for species in family:
            if species.name.lower() == name.lower():
                return species

    return None


@t.overload
def find_by_pokedex(pokedex: int, *, strict: t.Literal[True]) -> Species: ...


@t.overload
def find_by_pokedex(
    pokedex: int,
    *,
    strict: t.Literal[False] = ...,
) -> Species | None: ...


def find_by_pokedex(pokedex: int, *, strict: bool = True) -> Species | None:
    for family in families:
        for species in family:
            if species.pokedex == pokedex:
                return species

    if strict:
        msg = f"could not find pokemon with pokedex {pokedex}"
        raise PokemonNotFoundError(msg)

    return None
