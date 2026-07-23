"""Tables in the database."""

from __future__ import annotations

import typing as t

import peewee as p


class Maxed(p.Model):
    """A maxed Pokemon entry."""

    id = p.AutoField()

    user_id = p.IntegerField()
    pokedex = p.IntegerField()

    shadow = p.BooleanField()
    legacy = p.BooleanField()

    count = p.IntegerField(default=0)

    @classmethod
    def by(cls, user_id: int, database: p.Database) -> list[t.Self]:
        # eagerly query data, so that database can be closed already
        return list(cls.select().where(cls.user_id == user_id).execute(database))
