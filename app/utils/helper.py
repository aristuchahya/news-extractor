"""Small generic helpers that don't belong to a more specific util module."""


def first_non_empty[T](*values: T | None) -> T | None:
    """Return the first truthy value, or None if all are empty."""
    for value in values:
        if value:
            return value
    return None


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(item.strip())
    return result
