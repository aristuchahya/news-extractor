from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.clients.http_client import HttpClient
from app.config.constants import (
    ARTICLE_LINK_PATTERNS,
    ARTICLE_LIST_CONTAINER_SELECTORS,
    SOURCE_HOMEPAGES,
)
from app.exceptions.extractor_exception import ValidationError
from app.utils.helper import dedupe_preserve_order
from app.utils.html import make_soup
from app.utils.logger import get_logger

logger = get_logger(__name__)


def list_sources() -> list[str]:
    return sorted(SOURCE_HOMEPAGES)


async def discover_latest_urls(
    source: str,
    limit: int = 20,
    http_client: HttpClient | None = None,
) -> list[str]:

    source = source.strip().lower()
    if source not in SOURCE_HOMEPAGES:
        raise ValidationError(f"Unknown source '{source}'. Supported: {', '.join(list_sources())}")

    homepage = SOURCE_HOMEPAGES[source]
    pattern = ARTICLE_LINK_PATTERNS[source]

    logger.info("Discovering latest articles for source=%s from %s", source, homepage)

    if http_client is not None:
        response = await http_client.get(homepage)
        html = response.text
    else:
        async with HttpClient() as client:
            response = await client.get(homepage)
            html = response.text

    soup = make_soup(html)

    container_selector = ARTICLE_LIST_CONTAINER_SELECTORS.get(source)
    search_root: BeautifulSoup | Tag = soup
    if container_selector:
        container = soup.select_one(container_selector)
        if container is not None:
            search_root = container
        else:
            logger.warning(
                "Container selector '%s' not found for source=%s, searching whole page",
                container_selector,
                source,
            )

    urls = []
    for anchor in search_root.find_all("a", href=True):
        href = anchor["href"]
        if not isinstance(href, str) or not pattern.search(href):
            continue
        urls.append(urljoin(homepage, href).split("?")[0])

    unique_urls = dedupe_preserve_order(urls)[:limit]
    logger.info("Found %d latest article URLs for source=%s", len(unique_urls), source)
    return unique_urls
