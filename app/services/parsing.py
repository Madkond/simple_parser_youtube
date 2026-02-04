import re
from typing import Optional
from urllib.parse import urlparse, parse_qs

VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def extract_video_id(url: str) -> Optional[str]:
    url = url.strip()
    if not url:
        return None

    if VIDEO_ID_RE.match(url):
        return url

    try:
        parsed = urlparse(url)
    except Exception:
        return None

    host = parsed.netloc.lower()
    path = parsed.path

    if host in {"youtu.be"}:
        vid = path.strip("/")
        return vid if VIDEO_ID_RE.match(vid) else None

    if host.endswith("youtube.com"):
        if path == "/watch":
            q = parse_qs(parsed.query)
            vid = q.get("v", [""])[0]
            return vid if VIDEO_ID_RE.match(vid) else None
        if path.startswith("/shorts/"):
            vid = path.split("/shorts/")[-1].split("/")[0]
            return vid if VIDEO_ID_RE.match(vid) else None

    return None
