from app.clients.http_client import HttpClient
from app.config.constants import STATUS_FAILED, STATUS_SUCCESS
from app.exceptions.extractor_exception import ExtractionError, ExtractorError, ValidationError
from app.extractors.base import ExtractionResult
from app.extractors.factory import ExtractorFactory
from app.models.article import Article
from app.models.metadata import Metadata
from app.services.metadata_service import extract_metadata
from app.utils.date import utcnow_iso
from app.utils.helper import first_non_empty
from app.utils.html import make_soup, word_count
from app.utils.logger import get_logger
from app.utils.url import get_domain, is_valid_url, source_key_for_url

logger = get_logger(__name__)


class ExtractorService:
    def __init__(self, http_client: HttpClient | None = None) -> None:
        self._external_client = http_client
        self._factory = ExtractorFactory()

    async def extract(self, url: str) -> Article:
        logger.info("Extraction started: %s", url)

        if not is_valid_url(url):
            raise ValidationError(f"Invalid URL: {url}")

        html = await self._download(url)
        soup = make_soup(html)

        result = self._factory.run(html, url)
        if result is None:
            logger.error("Extraction failed (trafilatura + BS4 fallback both empty): %s", url)
            raise ExtractionError(f"Could not extract content from {url}")

        metadata = extract_metadata(soup, url)
        lang_attr = soup.html.get("lang") if soup.html else None
        language = lang_attr if isinstance(lang_attr, str) else None

        article = self._build_article(url, result, metadata, language)
        logger.info("Extraction Finished: %s", url)
        return article

    async def extract_safe(self, url: str) -> Article:
        try:
            return await self.extract(url)
        except ExtractorError as exc:
            logger.error("Extraction error for %s: %s", url, exc)
            return Article(
                url=url,
                status=STATUS_FAILED,
                error=str(exc),
                scrapped_at=utcnow_iso(),
            )

    async def _download(self, url: str) -> str:
        if self._external_client is not None:
            response = await self._external_client.get(url)
            return response.text

        async with HttpClient() as client:
            response = await client.get(url)
            return response.text

    def _build_article(
        self,
        url: str,
        result: ExtractionResult,
        metadata: Metadata,
        language: str | None,
    ) -> Article:
        content = result.content
        title = first_non_empty(result.title, metadata.og_title, metadata.title) or ""

        return Article(
            url=url,
            title=title,
            author=metadata.author,
            published_date=metadata.published_date,
            language=language,
            source=get_domain(url) or source_key_for_url(url),
            category=metadata.category,
            tags=metadata.tags,
            image=metadata.og_image,
            summary=first_non_empty(result.summary, metadata.description),
            content=content,
            text_length=len(content),
            word_count=word_count(content),
            extraction_method=result.extraction_method,
            scrapped_at=utcnow_iso(),
            status=STATUS_SUCCESS,
        )
