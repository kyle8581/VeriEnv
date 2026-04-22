from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


@dataclass
class LocalSqliteDb:
    """
    Convenience helper for *local* SQLite access.

    This is not used for remote environments; it exists for local debugging,
    inspection, and admin scripts.
    """

    path: str | Path

    def _connect(self) -> sqlite3.Connection:
        p = Path(self.path).expanduser().resolve()
        return sqlite3.connect(str(p))

    def scalar(self, sql: str, params: Iterable[Any] | None = None) -> Any:
        params = params or ()
        with self._connect() as con:
            cur = con.execute(sql, tuple(params))
            row = cur.fetchone()
            return row[0] if row else None

    def rows(self, sql: str, params: Iterable[Any] | None = None) -> list[tuple[Any, ...]]:
        params = params or ()
        with self._connect() as con:
            cur = con.execute(sql, tuple(params))
            return list(cur.fetchall())

    def dict_rows(self, sql: str, params: Iterable[Any] | None = None) -> list[Mapping[str, Any]]:
        params = params or ()
        with self._connect() as con:
            con.row_factory = sqlite3.Row
            cur = con.execute(sql, tuple(params))
            return [dict(r) for r in cur.fetchall()]

