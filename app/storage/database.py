from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.utils.logger import get_logger

logger = get_logger(__name__)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    url               TEXT    NOT NULL UNIQUE,
    title             TEXT,
    author            TEXT,
    published_date    TEXT,
    language          TEXT,
    source            TEXT,
    category          TEXT,
    tags              TEXT,
    image             TEXT,
    summary           TEXT,
    content           TEXT,
    extraction_method TEXT,
    status            TEXT,
    scrapped_at       TEXT,
    created_at        TEXT    DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_articles_url          ON articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_source       ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_status       ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_scrapped_at  ON articles(scrapped_at);
"""

_UPSERT_SQL = """
INSERT INTO articles (
    url, title, author, published_date, language, source,
    category, tags, image, summary, content,
    extraction_method, scrapped_at, status
) VALUES (
    :url, :title, :author, :published_date, :language, :source,
    :category, :tags, :image, :summary, :content,
    :extraction_method, :scrapped_at, :status
)
ON CONFLICT(url) DO UPDATE SET
    title             = excluded.title,
    author            = excluded.author,
    published_date    = excluded.published_date,
    language          = excluded.language,
    source            = excluded.source,
    category          = excluded.category,
    tags              = excluded.tags,
    image             = excluded.image,
    summary           = excluded.summary,
    content           = excluded.content,
    extraction_method = excluded.extraction_method,
    scrapped_at       = excluded.scrapped_at,
    status            = excluded.status
"""


class ArticleDB:
    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self._db_path),
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=10,
        )
        # DELETE journal mode — single .db file, no -wal/-shm, works with
        # Docker bind mounts and external tools (DBeaver, sqlite3 CLI, etc.).
        self._conn.execute("PRAGMA journal_mode=DELETE")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA_SQL)
        self._conn.commit()
        logger.info("Database initialized at %s", self._db_path)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed")

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database not initialized — call .initialize() first")
        return self._conn

    def upsert_articles(self, articles: list[dict[str, Any]]) -> int:
        """Insert or update articles. Returns the number of rows affected."""
        rows = _prepare_rows(articles)
        if not rows:
            logger.info("No articles to upsert")
            return 0

        with self.conn:
            cursor = self.conn.executemany(_UPSERT_SQL, rows)

        count = cursor.rowcount
        logger.info("Upserted %d article(s) (affected %d row(s))", len(rows), count)
        return count

    def count_by_status(self) -> dict[str, int]:
        rows = self.conn.execute(
            "SELECT status, COUNT(*) FROM articles GROUP BY status"
        ).fetchall()
        return {status: count for status, count in rows}

    def count_by_source(self) -> dict[str, int]:
        rows = self.conn.execute(
            "SELECT source, COUNT(*) FROM articles GROUP BY source ORDER BY COUNT(*) DESC"
        ).fetchall()
        return {source: count for source, count in rows}

    def recent_articles(self, limit: int = 10) -> list[dict[str, Any]]:
        cursor = self.conn.execute(
            "SELECT url, title, source, scrapped_at, status "
            "FROM articles ORDER BY scrapped_at DESC LIMIT ?",
            (limit,),
        )
        return [
            {"url": r[0], "title": r[1], "source": r[2], "scrapped_at": r[3], "status": r[4]}
            for r in cursor.fetchall()
        ]

    def total_articles(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]

def _prepare_rows(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Article dicts to rows suitable for SQLite (tags → JSON string)."""
    rows: list[dict[str, Any]] = []
    for a in articles:
        tags = a.get("tags", [])
        row = {**a, "tags": json.dumps(tags, ensure_ascii=False) if tags else "[]"}
        rows.append(row)
    return rows
