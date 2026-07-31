from bs4 import BeautifulSoup, Tag

from app.config.constants import EXTRACTION_METHOD_BS4, MIN_CONTENT_LENGTH
from app.extractors.base import BaseExtractor, ExtractionResult
from app.utils.html import clean_text, make_soup, strip_unwanted_tags
from app.utils.logger import get_logger

logger = get_logger(__name__)

_CANDIDATE_SELECTORS = (
    "article",
    "[itemprop='articleBody']",
    ".detail__body-text",
    ".read__content",
    ".article-content",
    "#article-content",
    ".content-article",
)


class Bs4FallbackExtractor(BaseExtractor):
    name = EXTRACTION_METHOD_BS4

    def extract(self, html: str, url: str) -> ExtractionResult | None:
        logger.warning("Fallback to BS4")

        soup = strip_unwanted_tags(make_soup(html))

        container = self._find_container(soup)
        if container is None:
            logger.warning("BS4 fallback found no suitable container")
            return None

        paragraphs = [clean_text(p.get_text(" ", strip=True)) for p in container.find_all("p")]
        paragraphs = [p for p in paragraphs if p]
        content = (
            "\n\n".join(paragraphs)
            if paragraphs
            else clean_text(container.get_text(" ", strip=True))
        )

        if len(content) < MIN_CONTENT_LENGTH:
            logger.warning("BS4 fallback content too short (%d chars)", len(content))
            return None

        title = self._find_title(soup)
        summary = paragraphs[0] if paragraphs else None

        return ExtractionResult(
            title=title,
            content=content,
            summary=summary,
            extraction_method=self.name,
        )

    def _find_container(self, soup: BeautifulSoup) -> Tag | None:
        for selector in _CANDIDATE_SELECTORS:
            found = soup.select_one(selector)
            if found is not None and len(found.find_all("p")) >= 2:
                return found

        candidates = soup.find_all(["div", "section"])
        best: Tag | None = None
        best_len = 0
        for candidate in candidates:
            paragraphs = candidate.find_all("p", recursive=False)
            text_len = sum(len(p.get_text(strip=True)) for p in paragraphs)
            if text_len > best_len:
                best_len = text_len
                best = candidate

        return best if best_len >= MIN_CONTENT_LENGTH else soup.body

    def _find_title(self, soup: BeautifulSoup) -> str:
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return clean_text(h1.get_text(strip=True))

        if soup.title and soup.title.get_text(strip=True):
            return clean_text(soup.title.get_text(strip=True))

        return ""
