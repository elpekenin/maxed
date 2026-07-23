from __future__ import annotations

import typing as t
from contextlib import contextmanager

import peewee as p

if t.TYPE_CHECKING:
    from collections.abc import Generator


@contextmanager
def session(file: str) -> Generator[p.Database]:
    db = p.SqliteDatabase(file, autocommit=False)

    db.begin()

    try:
        yield db
    except Exception as e:
        db.rollback()
        db.close()
        raise e from None

    db.commit()
    db.close()
