#!/usr/bin/env python
"""CLI script: extract article URLs and/or latest articles from a source, print JSON.

Usage:
    uv run scripts/extract.py <url-or-source> [<url-or-source> ...] [--limit N]

Each argument is either a full article URL, or a known source key (detik,
kompas, tempo, cnn, tribun, liputan6) — a source key is expanded to its latest
article URLs via a single homepage fetch (--limit caps how many, default 10).
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import extract_many  # noqa: E402


def run(inputs: list[str], limit_per_source: int) -> None:
    articles = asyncio.run(extract_many(inputs, limit_per_source=limit_per_source))
    payload = [article.model_dump() for article in articles]
    print(json.dumps(payload if len(payload) > 1 else payload[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    args = sys.argv[1:]
    limit = 10
    if "--limit" in args:
        idx = args.index("--limit")
        limit = int(args[idx + 1])
        del args[idx : idx + 2]

    if not args:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    run(args, limit)
