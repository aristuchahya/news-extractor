from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def get_domain(url: str) -> str:
    
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def source_key_for_url(url: str) -> str | None:
    from app.config.constants import SUPPORTED_PARSERS

    domain = get_domain(url)
    for site_domain, key in SUPPORTED_PARSERS.items():
        if domain == site_domain or domain.endswith(f".{site_domain}"):
            return key
    return None


def resolve_url(base_url: str, maybe_relative: str | None) -> str | None:
    if not maybe_relative:
        return None

    from urllib.parse import urljoin

    return urljoin(base_url, maybe_relative)
