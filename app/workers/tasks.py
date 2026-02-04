from __future__ import annotations

import json
import logging
import os
import zlib
from typing import Dict, List

from app.config import Config
from app.services.export import export_csv, export_json, export_xlsx
from app.services.filtering import apply_filters
from app.services.youtube import YouTubeClient
from app.storage.cache_keys import (
    job_cancel_key,
    job_progress_key,
    job_result_key,
    job_status_key,
    yt_comments_cache_key,
)
from app.storage.redis import get_redis_sync

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 60 * 60 * 12
JOB_TTL_SECONDS = 60 * 60 * 4


def _compress(data: List[Dict]) -> bytes:
    raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return zlib.compress(raw, level=6)


def _decompress(data: bytes) -> List[Dict]:
    raw = zlib.decompress(data)
    return json.loads(raw.decode("utf-8"))


def fetch_and_export(job_id: str, settings: Dict) -> str:
    config = Config.from_env()
    r = get_redis_sync(config.redis_url)

    def set_status(status: str) -> None:
        r.setex(job_status_key(job_id), JOB_TTL_SECONDS, status.encode("utf-8"))

    def set_progress(payload: Dict) -> None:
        r.setex(job_progress_key(job_id), JOB_TTL_SECONDS, json.dumps(payload).encode("utf-8"))

    def is_cancelled() -> bool:
        return bool(r.get(job_cancel_key(job_id)))

    try:
        set_status("running")
        set_progress({"message": "Fetching comments...", "fetched": 0, "limit": settings.get("limit", config.default_limit)})

        video_id = settings["video_id"]
        limit = int(settings.get("limit", config.default_limit))
        include_replies = bool(settings.get("include_replies", False))

        logger.info("Job %s started for video %s (limit=%s, replies=%s)", job_id, video_id, limit, include_replies)

        cache_params = {
            "limit": limit,
            "include_replies": include_replies,
        }
        cache_key = yt_comments_cache_key(video_id, cache_params)

        comments: List[Dict]
        cached = r.get(cache_key)
        if cached:
            comments = _decompress(cached)
            logger.info("Cache hit for %s", video_id)
        else:
            yt = YouTubeClient(config.yt_api_key)
            def _on_progress(count: int) -> None:
                if is_cancelled():
                    raise RuntimeError("cancelled")
                set_progress({"message": "Fetching comments...", "fetched": count, "limit": limit})

            comments = yt.fetch_comments(
                video_id=video_id,
                limit=limit,
                include_replies=include_replies,
                progress_cb=_on_progress,
            )
            r.setex(cache_key, CACHE_TTL_SECONDS, _compress(comments))

        if is_cancelled():
            raise RuntimeError("cancelled")
        set_progress({"message": "Filtering...", "fetched": len(comments), "limit": limit})

        filtered = apply_filters(
            comments,
            keywords=settings.get("keywords") or [],
            keywords_mode=settings.get("keywords_mode", "any"),
            keywords_case_sensitive=settings.get("keywords_case_sensitive", False),
            min_len=settings.get("min_len"),
            sort=settings.get("sort", "none"),
            limit=limit,
        )

        if is_cancelled():
            raise RuntimeError("cancelled")
        set_progress({"message": "Exporting...", "fetched": len(filtered), "limit": limit})

        export_dir = config.export_dir
        fmt = settings.get("format", "csv")
        fields = settings.get("fields") or ["author", "published_at", "like_count", "text"]
        try:
            if fmt == "xlsx":
                path = export_xlsx(filtered, export_dir, video_id, fields)
            elif fmt == "json":
                path = export_json(filtered, export_dir, video_id, fields)
            else:
                path = export_csv(filtered, export_dir, video_id, fields)
        except OSError as exc:
            if getattr(exc, "errno", None) == 30:
                fallback_dir = "/tmp/yt_exports"
                logger.warning("Export dir read-only: %s. Falling back to %s", export_dir, fallback_dir)
                set_progress({"message": "Export dir read-only, using /tmp", "fetched": len(filtered), "limit": limit})
                if fmt == "xlsx":
                    path = export_xlsx(filtered, fallback_dir, video_id, fields)
                elif fmt == "json":
                    path = export_json(filtered, fallback_dir, video_id, fields)
                else:
                    path = export_csv(filtered, fallback_dir, video_id, fields)
            else:
                raise

        result = {
            "file_path": path,
            "count": len(filtered),
            "format": fmt,
            "video_id": video_id,
        }
        r.setex(job_result_key(job_id), JOB_TTL_SECONDS, json.dumps(result).encode("utf-8"))
        set_status("done")
        set_progress({"message": "Done", "fetched": len(filtered), "limit": limit, "exported": True})

        logger.info("Job %s done: %s comments, file=%s", job_id, len(filtered), path)

        return path
    except Exception as exc:
        if str(exc) == "cancelled":
            set_status("cancelled")
            set_progress({"message": "Cancelled", "fetched": 0, "exported": False})
            return ""
        logger.exception("Job failed: %s", exc)
        set_status("error")
        set_progress({"message": f"Error: {exc}", "fetched": 0, "exported": False})
        raise
