"""HTML cleaning and text helpers shared by extractors and parsers."""

import re

from bs4 import BeautifulSoup

_UNWANTED_TAGS = (
    "script",
    "style",
    "noscript",
    "iframe",
    "svg",
    "form",
    "header",
    "footer",
    "nav",
    "aside",
)

_WHITESPACE_RE = re.compile(r"[ \t\f\v]+")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def strip_unwanted_tags(soup: BeautifulSoup) -> BeautifulSoup:
    for tag_name in _UNWANTED_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    for comment in soup.find_all(string=lambda s: s.__class__.__name__ == "Comment"):
        comment.extract()
    return soup


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    text = _WHITESPACE_RE.sub(" ", text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def word_count(text: str) -> int:
    return len(text.split()) if text else 0


def get_meta_content(
    soup: BeautifulSoup, *, name: str | None = None, prop: str | None = None
) -> str | None:
    attrs: dict[str, str] = {}
    if name:
        attrs["name"] = name
    if prop:
        attrs["property"] = prop
    tag = soup.find("meta", attrs=attrs)  # type: ignore[arg-type]
    content = tag.get("content") if tag else None
    return content.strip() if isinstance(content, str) else None
