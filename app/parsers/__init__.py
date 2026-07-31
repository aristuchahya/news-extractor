"""Registry mapping a site key (see app.config.constants.SUPPORTED_PARSERS) to its parser module."""

from app.parsers import cnn, detik, generic, kompas, liputan6, tempo

_REGISTRY = {
    "detik": detik,
    "kompas": kompas,
    "tempo": tempo,
    "cnn": cnn,
    "liputan6": liputan6,
}


def get_parser(site_key: str | None):
    if site_key is None:
        return generic
    return _REGISTRY.get(site_key, generic)
