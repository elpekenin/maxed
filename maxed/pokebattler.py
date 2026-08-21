"""Utilities for pokebattler.com API."""

import typing as t
from dataclasses import dataclass

import httpx
import pydantic

from maxed import pokedex

BASE_URL = "https://fight.pokebattler.com"
ENDPOINT = (
    "/raids/defenders/{boss}"
    "/levels/{tier}/attackers/levels/{level}"
    "/strategies/{attack}/{defense}"
)

# NOTE: these dataclasses are partial, the API returns more fields
#       the representation here is the useful part of it for our use-case


@dataclass(slots=True, frozen=True)
class _Defender:
    """Pokemon to be used on a raid."""

    @dataclass(slots=True, frozen=True)
    class ByMove:
        """Internal data structure."""

        @dataclass(slots=True, frozen=True)
        class Result:
            """Raid outcome."""

            estimator: float
            edps: float

        move1: str
        move2: str
        result: Result
        legacyDate: str | None = None

    pokemonId: str
    byMove: list[ByMove]


@dataclass(slots=True, frozen=True)
class _Attacker:
    """Pokémon for a raid."""

    @dataclass(slots=True, frozen=True)
    class RandomMove:
        """Internal data structure."""

        defenders: list[_Defender]

    randomMove: RandomMove


@dataclass(slots=True, frozen=True)
class _Response:
    """API response."""

    attackers: list[_Attacker]


def _pprint(val: str) -> str:
    return val.replace("_", " ").title()


@dataclass(slots=True, frozen=True)
class Counter:
    """Raid suggestion."""

    name: str
    fast_move: str
    charged_move: str
    dps: float
    legacy: bool

    @classmethod
    def adapt(cls, name: str, attacker: _Defender.ByMove) -> t.Self:
        """Adapt from `ByMove` to ``Counter``.

        Args:
            name: the attacker's name
            attacker: data, such as moveset or dps

        Returns:
            A ``Counter`` instance

        """
        mega = "_MEGA"
        if name.endswith(mega):
            name = "Mega " + name.removesuffix(mega)

        return cls(
            name=_pprint(name),
            fast_move=_pprint(attacker.move1.removesuffix("_FAST")),
            charged_move=_pprint(attacker.move2),
            dps=attacker.result.edps,
            legacy=attacker.legacyDate is not None,
        )


async def counters(boss: pokedex.Species) -> list[Counter]:
    """Suggest counters for a raid.

    Args:
        boss: the Pokémon being fought

    Returns:
        List of best Pokémon to use

    """
    url = BASE_URL + ENDPOINT.format(
        boss=boss.name.upper(),
        tier="RAID_LEVEL_5",
        level=40,
        attack="CINEMATIC_ATTACK_WHEN_POSSIBLE",
        defense="DEFENSE_RANDOM_MC",
    )

    async with httpx.AsyncClient() as client:
        raw = await client.get(url)

    adapter = pydantic.TypeAdapter(_Response)
    response = adapter.validate_python(raw.json())

    counters: list[Counter] = []

    unknown_moveset = response.attackers[0].randomMove
    for defender in unknown_moveset.defenders:
        best_moveset = min(defender.byMove, key=lambda d: d.result.estimator)

        counters.append(Counter.adapt(defender.pokemonId, best_moveset))

    return counters
