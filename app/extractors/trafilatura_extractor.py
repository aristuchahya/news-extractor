import json

import trafilatura

from app.config.constants import EXTRACTION_METHOD_TRAFILATURA, MIN_CONTENT_LENGTH
from app.extractors.base import BaseExtractor, ExtractionResult
from app.utils.html import clean_text
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TrafilaturaExtractor(BaseExtractor):
    name = EXTRACTION_METHOD_TRAFILATURA

    def extract(self, html: str, url: str) -> ExtractionResult | None:
        logger.info("Using Trafilatura")

        raw = trafilatura.extract(
            html,
            url=url,
            output_format="json",
            with_metadata=True,
            include_comments=False,
            include_tables=True,
            favor_recall=True,
        )

        if not raw:
            logger.warning("Trafilatura returned no content")
            return None

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Trafilatura returned malformed JSON")
            return None

        content = clean_text(data.get("text"))
        logger.info("Content Length: %d", len(content))

        if len(content) < MIN_CONTENT_LENGTH:
            logger.warning("Trafilatura content too short (%d chars)", len(content))
            return None

        return ExtractionResult(
            title=(data.get("title") or "").strip(),
            content=content,
            summary=(data.get("excerpt") or None),
            extraction_method=self.name,
        )
