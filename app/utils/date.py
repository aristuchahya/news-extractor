"""Publish-date parsing helpers.

News sites express dates in wildly inconsistent formats (ISO 8601, RFC 2822,
`DD/MM/YYYY HH:MM`, Indonesian month names, etc). This module normalizes
whatever we can find down to an ISO 8601 string in UTC.
"""

import re
from datetime import UTC, datetime

_INDONESIAN_MONTHS = {
    "januari": 1,
    "februari": 2,
    "maret": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "agustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}

_ID_DATE_RE = re.compile(
    r"(?P<day>\d{1,2})\s+(?P<month>[A-Za-z]+)\s+(?P<year>\d{4})"
    r"(?:[,\s]+(?P<hour>\d{1,2}):(?P<minute>\d{2}))?"
)

_ISO_LIKE_FORMATS = (
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
)


def parse_date(raw: str | None) -> str | None:
    """Best-effort parse of a raw date string into an ISO 8601 string."""
    if not raw:
        return None

    raw = raw.strip()
    if not raw:
        return None

    normalized = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        return _to_iso(dt)
    except ValueError:
        pass

    for fmt in _ISO_LIKE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            return _to_iso(dt)
        except ValueError:
            continue

    match = _ID_DATE_RE.search(raw.lower())
    if match:
        month = _INDONESIAN_MONTHS.get(match.group("month").lower())
        if month:
            try:
                dt = datetime(
                    year=int(match.group("year")),
                    month=month,
                    day=int(match.group("day")),
                    hour=int(match.group("hour") or 0),
                    minute=int(match.group("minute") or 0),
                )
                return _to_iso(dt)
            except ValueError:
                pass

    return None


def _to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat()


def utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()
