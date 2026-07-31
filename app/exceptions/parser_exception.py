class ParserError(Exception):
    """Base class for parser-level failures. Never fatal — extraction falls back to generic."""


class UnsupportedSiteError(ParserError):
    """Raised internally when no site-specific parser matches a URL's domain."""
