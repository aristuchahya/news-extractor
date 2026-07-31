from app.extractors.base import ExtractionResult
from app.extractors.bs4_fallback import Bs4FallbackExtractor
from app.extractors.trafilatura_extractor import TrafilaturaExtractor
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ExtractorFactory:
    def __init__(self) -> None:
        self._primary = TrafilaturaExtractor()
        self._fallback = Bs4FallbackExtractor()

    def run(self, html: str, url: str) -> ExtractionResult | None:
        result = self._primary.extract(html, url)
        if result is not None:
            return result

        logger.warning("Trafilatura extraction empty, falling back to BS4")
        return self._fallback.extract(html, url)
