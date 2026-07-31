from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_ENV_FILE = _PROJECT_ROOT / ".env"
if _ENV_FILE.exists():
    os.environ.setdefault("ENV_FILE", str(_ENV_FILE))

from airflow.decorators import dag, task  # noqa: E402

from app.config.constants import SOURCE_HOMEPAGES  # noqa: E402
from app.main import extract_many  # noqa: E402
from app.storage.database import ArticleDB  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

SOURCES: list[str] = sorted(SOURCE_HOMEPAGES)
DEFAULT_LIMIT_PER_SOURCE: int = int(os.getenv("CRAWLER_LIMIT_PER_SOURCE", "3"))
DEFAULT_DB_PATH: str = os.getenv("CRAWLER_DB_PATH", "/opt/airflow/data/articles.db")



@dag(
    dag_id="news_crawler_pipeline",
    description="Discover article URLs from news sources, extract content, and ingest into SQLite.",
    schedule="0 12 * * *",
    start_date=datetime(2026, 7, 31),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=8,
    tags=["news", "crawler", "extraction"],
    default_args={
        "owner": "news-extractor",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
        "depends_on_past": False,
    },
)
def news_crawler_pipeline() -> None:

    @task(task_id="discover_urls", retries=1)
    def discover_urls(source: str, limit: int = DEFAULT_LIMIT_PER_SOURCE) -> dict[str, Any]:
        logger.info("Discovering URLs for source=%s limit=%d", source, limit)

        async def _run() -> list[str]:
            from app.services.discovery_service import discover_latest_urls

            return await discover_latest_urls(source, limit=limit)

        urls = asyncio.run(_run())
        logger.info("Discovered %d URL(s) for source=%s", len(urls), source)
        return {"source": source, "urls": urls}

    @task(task_id="extract_articles", retries=1)
    def extract_articles(discovery_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        all_urls: list[str] = []
        for result in discovery_results:
            all_urls.extend(result.get("urls", []))

        if not all_urls:
            logger.warning("No URLs discovered — nothing to extract")
            return []

        logger.info(
            "Extracting %d article(s) across %d source(s)", len(all_urls), len(discovery_results)
        )

        async def _run() -> list[dict[str, Any]]:
            articles = await extract_many(all_urls, limit_per_source=DEFAULT_LIMIT_PER_SOURCE)
            return [a.model_dump() for a in articles]

        articles = asyncio.run(_run())
        success = sum(1 for a in articles if a.get("status") == "success")
        failed = sum(1 for a in articles if a.get("status") == "failed")
        logger.info("Extraction complete — %d success, %d failed", success, failed)
        return articles

    @task(task_id="ingest_to_sqlite")
    def ingest_to_sqlite(
        articles: list[dict[str, Any]], db_path: str = DEFAULT_DB_PATH
    ) -> dict[str, Any]:
        if not articles:
            logger.warning("No articles to ingest")
            return {"upserted": 0, "by_status": {}, "by_source": {}, "total_in_db": 0}

        logger.info("Ingesting %d article(s) into %s", len(articles), db_path)

        db = ArticleDB(db_path)
        try:
            db.initialize()
            upserted = db.upsert_articles(articles)
            summary = {
                "upserted": upserted,
                "by_status": db.count_by_status(),
                "by_source": db.count_by_source(),
                "total_in_db": db.total_articles(),
            }
        finally:
            db.close()

        logger.info("Ingest summary: %s", json.dumps(summary, ensure_ascii=False))
        return summary

    discovered = discover_urls.expand(source=SOURCES)
    extracted = extract_articles(discovered)
    ingest_to_sqlite(extracted)


news_crawler_pipeline()
