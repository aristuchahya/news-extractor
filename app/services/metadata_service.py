from bs4 import BeautifulSoup

from app.config.constants import SUPPORTED_PARSERS
from app.models.metadata import Metadata
from app.parsers import get_parser
from app.utils.date import parse_date
from app.utils.helper import first_non_empty
from app.utils.html import get_meta_content
from app.utils.logger import get_logger
from app.utils.url import get_domain

logger = get_logger(__name__)


def _site_key_for(url: str) -> str | None:
    domain = get_domain(url)
    for site_domain, key in SUPPORTED_PARSERS.items():
        if domain == site_domain or domain.endswith(f".{site_domain}"):
            return key
    return None


def extract_metadata(soup: BeautifulSoup, url: str) -> Metadata:
    canonical_tag = soup.find("link", rel="canonical")
    canonical_href = canonical_tag.get("href") if canonical_tag else None
    canonical_url = canonical_href if isinstance(canonical_href, str) else None

    keywords_raw = get_meta_content(soup, name="keywords")
    keywords = [k.strip() for k in keywords_raw.split(",")] if keywords_raw else []

    site_key = _site_key_for(url)
    parser = get_parser(site_key)
    site_data = parser.parse(soup, url)

    published_raw = (
        get_meta_content(soup, prop="article:published_time")
        or get_meta_content(soup, name="publishdate")
        or get_meta_content(soup, name="date")
    )

    page_title = soup.title.get_text(strip=True) if soup.title else None

    return Metadata(
        title=get_meta_content(soup, name="title") or page_title,
        description=get_meta_content(soup, name="description")
        or get_meta_content(soup, prop="og:description"),
        keywords=keywords,
        canonical_url=canonical_url,
        og_title=get_meta_content(soup, prop="og:title"),
        og_description=get_meta_content(soup, prop="og:description"),
        og_image=get_meta_content(soup, prop="og:image"),
        og_site_name=get_meta_content(soup, prop="og:site_name"),
        og_type=get_meta_content(soup, prop="og:type"),
        robots=get_meta_content(soup, name="robots"),
        author=site_data.get("author"),
        published_date=parse_date(first_non_empty(published_raw)),
        category=site_data.get("category"),
        tags=site_data.get("tags") or [],
    )
