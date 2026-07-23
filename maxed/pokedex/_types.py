"""Types describing Pokémons."""

from __future__ import annotations

import enum
from dataclasses import dataclass


@dataclass(slots=True)
class Species:
    pokedex: int
    name: str
    primary: Type
    secondary: Type | None = None

    def best_counter_types(self) -> list[Type]:
        effectiveness = {
            attacker: (
                attacker.multiplier(self.primary) * attacker.multiplier(self.secondary)
            )
            for attacker in Type
        }

        max_value = max(effectiveness.values())

        return [key for key, val in effectiveness.items() if val == max_value]


class Type(enum.StrEnum):
    normal = "normal"
    fire = "fire"
    water = "water"
    electric = "electric"
    grass = "grass"
    ice = "ice"
    fighting = "fighting"
    poison = "poison"
    ground = "ground"
    flying = "flying"
    psychic = "psychic"
    bug = "bug"
    rock = "rock"
    ghost = "ghost"
    dragon = "dragon"
    dark = "dark"
    steel = "steel"
    fairy = "fairy"

    def multiplier(self, other: Type | None) -> float:
        inmune = 0.39
        not_very_effective = 0.625
        regular = 1
        super_effective = 1.6

        # this is for the secondary type, which is `None` on single-type pokémon
        if other is None:
            return regular

        return {
            # super effective
            (Type.fire, Type.grass): super_effective,
            (Type.fire, Type.ice): super_effective,
            (Type.fire, Type.bug): super_effective,
            (Type.fire, Type.steel): super_effective,
            (Type.water, Type.fire): super_effective,
            (Type.water, Type.ground): super_effective,
            (Type.water, Type.rock): super_effective,
            (Type.electric, Type.water): super_effective,
            (Type.electric, Type.flying): super_effective,
            (Type.grass, Type.water): super_effective,
            (Type.grass, Type.ground): super_effective,
            (Type.grass, Type.rock): super_effective,
            (Type.ice, Type.grass): super_effective,
            (Type.ice, Type.ground): super_effective,
            (Type.ice, Type.flying): super_effective,
            (Type.ice, Type.dragon): super_effective,
            (Type.fighting, Type.normal): super_effective,
            (Type.fighting, Type.ice): super_effective,
            (Type.fighting, Type.rock): super_effective,
            (Type.fighting, Type.dark): super_effective,
            (Type.fighting, Type.steel): super_effective,
            (Type.poison, Type.grass): super_effective,
            (Type.poison, Type.fairy): super_effective,
            (Type.ground, Type.fire): super_effective,
            (Type.ground, Type.electric): super_effective,
            (Type.ground, Type.poison): super_effective,
            (Type.ground, Type.rock): super_effective,
            (Type.ground, Type.steel): super_effective,
            (Type.flying, Type.grass): super_effective,
            (Type.flying, Type.fighting): super_effective,
            (Type.flying, Type.bug): super_effective,
            (Type.psychic, Type.fighting): super_effective,
            (Type.psychic, Type.poison): super_effective,
            (Type.bug, Type.grass): super_effective,
            (Type.bug, Type.psychic): super_effective,
            (Type.bug, Type.dark): super_effective,
            (Type.rock, Type.fire): super_effective,
            (Type.rock, Type.ice): super_effective,
            (Type.rock, Type.flying): super_effective,
            (Type.rock, Type.bug): super_effective,
            (Type.ghost, Type.psychic): super_effective,
            (Type.ghost, Type.ghost): super_effective,
            (Type.dragon, Type.dragon): super_effective,
            (Type.dark, Type.psychic): super_effective,
            (Type.dark, Type.ghost): super_effective,
            (Type.steel, Type.ice): super_effective,
            (Type.steel, Type.rock): super_effective,
            (Type.steel, Type.fairy): super_effective,
            (Type.fairy, Type.fighting): super_effective,
            (Type.fairy, Type.dragon): super_effective,
            (Type.fairy, Type.dark): super_effective,
            # not very effective
            (Type.normal, Type.rock): not_very_effective,
            (Type.normal, Type.steel): not_very_effective,
            (Type.fire, Type.fire): not_very_effective,
            (Type.fire, Type.water): not_very_effective,
            (Type.fire, Type.rock): not_very_effective,
            (Type.fire, Type.dragon): not_very_effective,
            (Type.water, Type.water): not_very_effective,
            (Type.water, Type.grass): not_very_effective,
            (Type.water, Type.dragon): not_very_effective,
            (Type.electric, Type.electric): not_very_effective,
            (Type.electric, Type.grass): not_very_effective,
            (Type.electric, Type.dragon): not_very_effective,
            (Type.grass, Type.fire): not_very_effective,
            (Type.grass, Type.grass): not_very_effective,
            (Type.grass, Type.poison): not_very_effective,
            (Type.grass, Type.flying): not_very_effective,
            (Type.grass, Type.bug): not_very_effective,
            (Type.grass, Type.dragon): not_very_effective,
            (Type.grass, Type.steel): not_very_effective,
            (Type.ice, Type.fire): not_very_effective,
            (Type.ice, Type.water): not_very_effective,
            (Type.ice, Type.ice): not_very_effective,
            (Type.ice, Type.steel): not_very_effective,
            (Type.fighting, Type.poison): not_very_effective,
            (Type.fighting, Type.flying): not_very_effective,
            (Type.fighting, Type.psychic): not_very_effective,
            (Type.fighting, Type.bug): not_very_effective,
            (Type.fighting, Type.fairy): not_very_effective,
            (Type.poison, Type.poison): not_very_effective,
            (Type.poison, Type.ground): not_very_effective,
            (Type.poison, Type.rock): not_very_effective,
            (Type.poison, Type.ghost): not_very_effective,
            (Type.ground, Type.grass): not_very_effective,
            (Type.ground, Type.bug): not_very_effective,
            (Type.flying, Type.electric): not_very_effective,
            (Type.flying, Type.rock): not_very_effective,
            (Type.flying, Type.steel): not_very_effective,
            (Type.psychic, Type.psychic): not_very_effective,
            (Type.psychic, Type.steel): not_very_effective,
            (Type.bug, Type.fire): not_very_effective,
            (Type.bug, Type.fighting): not_very_effective,
            (Type.bug, Type.poison): not_very_effective,
            (Type.bug, Type.flying): not_very_effective,
            (Type.bug, Type.ghost): not_very_effective,
            (Type.bug, Type.steel): not_very_effective,
            (Type.bug, Type.fairy): not_very_effective,
            (Type.rock, Type.fighting): not_very_effective,
            (Type.rock, Type.ground): not_very_effective,
            (Type.rock, Type.steel): not_very_effective,
            (Type.ghost, Type.dark): not_very_effective,
            (Type.dragon, Type.steel): not_very_effective,
            (Type.dark, Type.fighting): not_very_effective,
            (Type.dark, Type.dark): not_very_effective,
            (Type.dark, Type.fairy): not_very_effective,
            (Type.steel, Type.fire): not_very_effective,
            (Type.steel, Type.water): not_very_effective,
            (Type.steel, Type.electric): not_very_effective,
            (Type.steel, Type.steel): not_very_effective,
            (Type.fairy, Type.poison): not_very_effective,
            (Type.fairy, Type.steel): not_very_effective,
            (Type.fairy, Type.fire): not_very_effective,
            # inmune
            (Type.normal, Type.ghost): inmune,
            (Type.fighting, Type.ghost): inmune,
            (Type.poison, Type.steel): inmune,
            (Type.ground, Type.flying): inmune,
            (Type.psychic, Type.dark): inmune,
            (Type.ghost, Type.normal): inmune,
            (Type.dragon, Type.fairy): inmune,
            (Type.electric, Type.ground): inmune,
        }.get((self, other), regular)
