"""Library entrypoint / programmatic API for the News Extractor service.

This project extracts content for a given URL — it does not operate a general
crawler. The one exception is `extract_latest_by_source`, which fetches a known
source's homepage a single time (no pagination, no recursion) to discover
today's article links, then extracts each. Import these to integrate with a
REST API, Kafka consumer, NSQ handler, or any other pipeline.
"""

import asyncio

from app.clients.http_client import HttpClient
from app.config.constants import STATUS_FAILED
from app.exceptions.extractor_exception import ExtractorError
from app.models.article import Article
from app.services.discovery_service import discover_latest_urls, list_sources
from app.services.extractor_service import ExtractorService
from app.utils.date import utcnow_iso
from app.utils.logger import get_logger
from app.utils.url import is_valid_url

logger = get_logger(__name__)


async def extract_article(url: str) -> Article:
    """Extract a single article. Raises ExtractorError subclasses on failure."""
    service = ExtractorService()
    return await service.extract(url)


async def extract_articles(urls: list[str]) -> list[Article]:
    """Extract many articles concurrently, sharing one connection pool.
    Never raises per-URL — failures are reported via Article.status == "failed".
    """
    async with HttpClient() as client:
        service = ExtractorService(http_client=client)
        return await asyncio.gather(*(service.extract_safe(url) for url in urls))


async def extract_latest_by_source(source: str, limit: int = 10) -> list[Article]:
    """Discover the latest article URLs on `source`'s homepage (single fetch) and
    extract each. Raises ValidationError for an unknown source; per-URL extraction
    failures are reported via Article.status == "failed", not raised.
    """
    async with HttpClient() as client:
        urls = await discover_latest_urls(source, limit=limit, http_client=client)
        service = ExtractorService(http_client=client)
        return await asyncio.gather(*(service.extract_safe(url) for url in urls))


async def extract_many(inputs: list[str], limit_per_source: int = 10) -> list[Article]:
    """Extract a mix of article URLs and source keys (e.g. "detik") in one batch,
    sharing a single connection pool. A source key expands to its latest article
    URLs via one homepage fetch. Never raises — every input, resolvable or not,
    ends up as an Article with status "success" or "failed".
    """
    known_sources = set(list_sources())

    async with HttpClient() as client:
        service = ExtractorService(http_client=client)

        async def resolve(item: str) -> list[str] | None:
            if is_valid_url(item):
                return [item]
            key = item.strip().lower()
            if key in known_sources:
                return await discover_latest_urls(key, limit=limit_per_source, http_client=client)
            return None

        resolved_lists = await asyncio.gather(*(resolve(item) for item in inputs))

        urls: list[str] = []
        unresolved: list[Article] = []
        for item, resolved in zip(inputs, resolved_lists, strict=True):
            if resolved is not None:
                urls.extend(resolved)
            else:
                unresolved.append(
                    Article(
                        url=item,
                        status=STATUS_FAILED,
                        error=(
                            f"'{item}' is not a valid URL or a known source "
                            f"({', '.join(sorted(known_sources))})"
                        ),
                        scrapped_at=utcnow_iso(),
                    )
                )

        extracted = await asyncio.gather(*(service.extract_safe(url) for url in urls))
        return [*extracted, *unresolved]


def main() -> None:
    """Demo entrypoint: extract a sample URL and print the JSON result."""
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else "https://news.detik.com/"
    article = asyncio.run(extract_article(url))
    print(article.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
