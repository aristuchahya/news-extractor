

import re

DEFAULT_USER_AGENT = "NewsExtractor/1.0 (+https://github.com/news-extractor)"

DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}

EXTRACTION_METHOD_TRAFILATURA = "trafilatura"
EXTRACTION_METHOD_BS4 = "bs4_fallback"

STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"

MIN_CONTENT_LENGTH = 200
"""Below this character count, trafilatura output is treated as empty and BS4 fallback kicks in."""

SUPPORTED_PARSERS = {
    "detik.com": "detik",
    "kompas.com": "kompas",
    "tempo.co": "tempo",
    "cnnindonesia.com": "cnn",
    "tribunnews.com": "tribun",
    "liputan6.com": "liputan6",
}

SOURCE_HOMEPAGES = {
    "detik": "https://news.detik.com",
    "kompas": "https://www.kompas.com",
    "tempo": "https://www.tempo.co",
    "cnn": "https://www.cnnindonesia.com",
    "liputan6": "https://www.liputan6.com",
}

ARTICLE_LINK_PATTERNS = {
    "detik": re.compile(r"/d-\d+/"),
    "kompas": re.compile(r"/read/\d{4}/\d{2}/\d{2}/\d+/"),
    "tempo": re.compile(r"^/[a-z0-9-]+/[a-z0-9-]+-\d{6,}$"),
    "cnn": re.compile(r"/\d{14}-\d+-\d+/"),
    "liputan6": re.compile(r"/read/\d+/"),
}


TEMPO_SESSION_COOKIE_NAME = "n_token"
