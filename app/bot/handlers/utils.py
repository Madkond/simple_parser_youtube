import json
import time
from typing import Any, Dict

from app.storage.cache_keys import user_job_key, user_last_job_time_key

DEFAULT_SETTINGS = {
    "video_id": None,
    "format": "csv",
    "sort": "none",
    "keywords": [],
    "keywords_mode": "any",
    "keywords_case_sensitive": False,
    "min_len": None,
    "limit": 500,
    "include_replies": False,
    "fields": ["author", "published_at", "like_count", "text"],
    "last_job_id": None,
}


async def get_user_settings(r, tg_id: int) -> Dict[str, Any]:
    raw = await r.get(user_job_key(tg_id))
    if not raw:
        return DEFAULT_SETTINGS.copy()
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return DEFAULT_SETTINGS.copy()
    merged = DEFAULT_SETTINGS.copy()
    merged.update(data)
    return merged


async def set_user_settings(r, tg_id: int, settings: Dict[str, Any], ttl: int = 60 * 60 * 24) -> None:
    await r.setex(user_job_key(tg_id), ttl, json.dumps(settings).encode("utf-8"))


async def set_last_job_ts(r, tg_id: int, ts: float, ttl: int = 60 * 60 * 24) -> None:
    await r.setex(user_last_job_time_key(tg_id), ttl, str(ts).encode("utf-8"))


async def get_last_job_ts(r, tg_id: int) -> float:
    raw = await r.get(user_last_job_time_key(tg_id))
    if not raw:
        return 0.0
    try:
        return float(raw.decode("utf-8"))
    except Exception:
        return 0.0


def format_settings(settings: Dict[str, Any]) -> str:
    keywords = ", ".join(settings.get("keywords", [])) or "—"
    sort = settings.get("sort", "none")
    sort_label = {
        "none": "без сортировки",
        "length_desc": "по длине ↓",
        "length_asc": "по длине ↑",
        "likes_desc": "по лайкам ↓",
        "date_new": "по дате (новые)",
        "date_old": "по дате (старые)",
    }.get(sort, sort)
    fields = ", ".join(settings.get("fields", [])) or "—"
    return (
        "Текущие настройки:\n"
        f"- Формат: {settings.get('format', 'csv')}\n"
        f"- Лимит: {settings.get('limit', 500)}\n"
        f"- Сортировка: {sort_label}\n"
        f"- Ключевые слова: {keywords}\n"
        f"- Replies: {'да' if settings.get('include_replies') else 'нет'}\n"
        f"- Поля: {fields}"
    )
