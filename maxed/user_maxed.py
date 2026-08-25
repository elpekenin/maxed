"""Utilities to find and store Pokémon maxed by a user."""

from __future__ import annotations

import typing as t
from dataclasses import dataclass

import sqlmodel

from maxed import pokedex, utils
from maxed.database import Maxed

if t.TYPE_CHECKING:
    from maxed.pokebattler import Counter

    type Suggestion = tuple[Counter, int]


@dataclass(frozen=True, slots=True)
class UserMaxed:
    """All Pokémon that a particular user has maxed."""

    items: list[Maxed]

    def __post_init__(self) -> None:
        """Validate that all entries belong to a single user.

        Raises:
            ValueError: if constraint is violated

        """
        user_id = self.items[0].user_id
        for item in self.items:
            if user_id != item.user_id:
                msg = "all values must belong to the same user"
                raise ValueError(msg)

    def update(self, new_item: Maxed, session: sqlmodel.Session) -> None:
        """Insert or update a database entry.

        Args:
            new_item: the entry
            session: a connection to the database

        """
        for index, item in enumerate(self.items):
            if item.id == new_item.id:
                # update in memory
                self.items[index] = new_item

                # update in db
                session.add(new_item)

                return

        # add in memory
        self.items.append(new_item)

        # add in db
        query = sqlmodel.insert(Maxed).values(
            user_id=new_item.user_id,
            pokedex=new_item.pokedex,
            shadow=new_item.shadow,
            legacy=new_item.legacy,
            count=new_item.count,
        )
        session.exec(query)

    @t.overload
    def find(
        self,
        *,
        pokedex: int,
        shadow: bool,
        legacy: bool,
    ) -> Maxed | None: ...

    @t.overload
    def find(
        self,
        *,
        pokedex: int,
    ) -> list[Maxed] | None: ...

    def find(
        self,
        *,
        pokedex: int,
        shadow: bool | None = None,
        legacy: bool | None = None,
    ) -> list[Maxed] | Maxed | None:
        """Find pokemon matching criteria.

        Args:
            pokedex: id of the Pokemon to find
            shadow: whether to look for the shadow or regular version
            legacy: whether to look for legacy moves

        Returns:
            All matches with the given filters

        Raises:
            ValueError: If ``shadow`` and ``legacy`` filters are provided yet \
            multiple matches are found

        """
        both_provided = shadow is not None and legacy is not None
        both_missing = shadow is None and legacy is None
        if not both_provided and not both_missing:
            msg = "must provide both legacy and shadow, or neither of them"
            raise ValueError(msg)

        matches: list[Maxed] = []
        for item in self.items:
            if pokedex is not None and item.pokedex != pokedex:
                continue

            if shadow is not None and item.shadow != shadow:
                continue

            if legacy is not None and item.legacy != legacy:
                continue

            matches.append(item)

        if len(matches) == 0:
            return None

        if both_provided:
            if len(matches) != 1:
                msg = "unreachable"
                raise ValueError(msg)

            return matches[0]

        return matches

    def find_match(self, attacker: Counter) -> int | None:
        """Check if a Pokemon is available.

        Args:
            attacker: the Pokemon to find

        Returns:
            The dex number of the Pokemon, if found

        """
        for item in self.items:
            pokemon = pokedex.find_by_pokedex(
                item.pokedex,
                strict=True,
            )

            if not utils.contains(attacker.name, pokemon.name):
                continue

            if utils.contains(attacker.name, "Mega ") and item.shadow:
                continue

            if utils.contains(attacker.name, "Shadow ") and not item.shadow:
                continue

            if attacker.legacy and not item.legacy:
                continue

            return pokemon.pokedex

        return None

    def get_suggestions(
        self,
        attackers: list[Counter],
        suggestions: int,
    ) -> list[Suggestion]:
        """Get the best available counters for a raid.

        Args:
            attackers: best attackers in the game
            suggestions: number of Pokemon to select from the list

        Returns:
            Best Pokemon that the user can bring to a raid

        """
        suggested: list[Suggestion] = []
        for attacker in sorted(
            attackers,
            key=lambda a: a.dps,
            reverse=True,
        ):
            if len(suggested) >= suggestions:
                break

            dex = self.find_match(attacker)
            if dex is None:
                continue

            suggestion = attacker, dex
            suggested.append(suggestion)

        return suggested
