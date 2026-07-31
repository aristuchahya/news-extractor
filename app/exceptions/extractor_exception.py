class ExtractorError(Exception):
    """Base class for all news-extractor errors."""


class NetworkError(ExtractorError):
    """Raised when the HTML could not be downloaded (timeout, connection error, HTTP error)."""


class ValidationError(ExtractorError):
    """Raised when the input URL or request payload is invalid."""


class ExtractionError(ExtractorError):
    """Raised when both trafilatura and the BS4 fallback fail to produce content."""
