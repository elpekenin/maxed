"""Database tables."""

from __future__ import annotations

import sqlmodel


class Maxed(sqlmodel.SQLModel, table=True):
    """A maxed Pokémon species."""

    id: int = sqlmodel.Field(primary_key=True)

    user_id: int

    pokedex: int
    shadow: bool
    legacy: bool

    count: int
