import json

from bs4 import BeautifulSoup

from app.utils.helper import dedupe_preserve_order
from app.utils.html import get_meta_content
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _extract_json_ld(soup: BeautifulSoup) -> dict:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue

        candidates = data if isinstance(data, list) else [data]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            if candidate.get("@type") in ("NewsArticle", "Article", "BlogPosting"):
                return candidate
            if "@graph" in candidate:
                for node in candidate["@graph"]:
                    if isinstance(node, dict) and node.get("@type") in (
                        "NewsArticle",
                        "Article",
                        "BlogPosting",
                    ):
                        return node
    return {}


def _author_from_json_ld(data: dict) -> str | None:
    author = data.get("author")
    if isinstance(author, dict):
        return author.get("name")
    if isinstance(author, list) and author:
        first = author[0]
        return first.get("name") if isinstance(first, dict) else str(first)
    if isinstance(author, str):
        return author
    return None


def parse(soup: BeautifulSoup, url: str) -> dict:
    json_ld = _extract_json_ld(soup)

    author = (
        _author_from_json_ld(json_ld)
        or get_meta_content(soup, name="author")
        or get_meta_content(soup, prop="article:author")
    )

    category = json_ld.get("articleSection") or get_meta_content(soup, prop="article:section")

    tags: list[str] = []
    keywords = json_ld.get("keywords")
    if isinstance(keywords, str):
        tags.extend(k.strip() for k in keywords.split(","))
    elif isinstance(keywords, list):
        tags.extend(str(k) for k in keywords)

    for tag in soup.find_all("meta", attrs={"property": "article:tag"}):
        content = tag.get("content")
        if isinstance(content, str):
            tags.append(content)

    return {
        "author": author.strip() if author else None,
        "category": category.strip() if isinstance(category, str) else category,
        "tags": dedupe_preserve_order(tags),
    }
