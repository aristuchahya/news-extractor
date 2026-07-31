from bs4 import BeautifulSoup

from app.parsers import generic
from app.utils.helper import dedupe_preserve_order, first_non_empty
from app.utils.html import clean_text


def parse(soup: BeautifulSoup, url: str) -> dict:
    base = generic.parse(soup, url)

    author_el = soup.select_one(".article-author-name, .read-page--author__name")
    category_el = soup.select_one(".breadcrumb a:last-of-type")
    tag_els = soup.select(".tag-link a, .article-tag-item a")

    return {
        "author": first_non_empty(
            clean_text(author_el.get_text()) if author_el else None, base["author"]
        ),
        "category": first_non_empty(
            clean_text(category_el.get_text()) if category_el else None, base["category"]
        ),
        "tags": dedupe_preserve_order([clean_text(t.get_text()) for t in tag_els] or base["tags"]),
    }
