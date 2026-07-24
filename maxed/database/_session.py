from __future__ import annotations

import sqlite3
import typing as t
from contextlib import contextmanager

if t.TYPE_CHECKING:
    from collections.abc import Generator


@contextmanager
def session(file: str) -> Generator[sqlite3.Connection]:
    conn = sqlite3.Connection(file, autocommit=False)

    conn.autocommit = False

    try:
        yield conn
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e from None

    conn.commit()
    conn.close()
