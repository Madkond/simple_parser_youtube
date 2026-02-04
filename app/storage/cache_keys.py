import hashlib
import json
from typing import Any, Dict


def user_job_key(tg_id: int) -> str:
    return f"user:{tg_id}:job"


def user_last_job_time_key(tg_id: int) -> str:
    return f"user:{tg_id}:last_job_ts"


def yt_comments_cache_key(video_id: str, params: Dict[str, Any]) -> str:
    payload = json.dumps(params, sort_keys=True, ensure_ascii=True)
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"yt:comments:{video_id}:{h}"


def job_status_key(job_id: str) -> str:
    return f"job:{job_id}:status"


def job_progress_key(job_id: str) -> str:
    return f"job:{job_id}:progress"


def job_result_key(job_id: str) -> str:
    return f"job:{job_id}:result"


def job_cancel_key(job_id: str) -> str:
    return f"job:{job_id}:cancel"
