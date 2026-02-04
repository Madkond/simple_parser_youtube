from typing import Iterable, List, Optional


def apply_filters(
    comments: Iterable[dict],
    keywords: Optional[List[str]] = None,
    keywords_mode: str = "any",
    keywords_case_sensitive: bool = False,
    min_len: Optional[int] = None,
    sort: str = "none",
    limit: Optional[int] = None,
) -> List[dict]:
    items = list(comments)

    if min_len is not None:
        items = [c for c in items if len(c.get("text", "")) >= min_len]

    if keywords:
        if keywords_case_sensitive:
            kw = [k for k in keywords if k.strip()]
        else:
            kw = [k.lower() for k in keywords if k.strip()]
        if kw:
            if keywords_mode == "all":
                items = [
                    c
                    for c in items
                    if all(
                        k in (c.get("text", "") if keywords_case_sensitive else c.get("text", "").lower())
                        for k in kw
                    )
                ]
            else:
                items = [
                    c
                    for c in items
                    if any(
                        k in (c.get("text", "") if keywords_case_sensitive else c.get("text", "").lower())
                        for k in kw
                    )
                ]

    if sort == "length_desc":
        items.sort(key=lambda c: len(c.get("text", "")), reverse=True)
    elif sort == "length_asc":
        items.sort(key=lambda c: len(c.get("text", "")))
    elif sort == "likes_desc":
        items.sort(key=lambda c: int(c.get("like_count", 0)), reverse=True)
    elif sort == "date_new":
        items.sort(key=lambda c: c.get("published_at", ""), reverse=True)
    elif sort == "date_old":
        items.sort(key=lambda c: c.get("published_at", ""))

    if limit is not None:
        items = items[:limit]

    return items
