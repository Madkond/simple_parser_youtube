from __future__ import annotations

import logging
from typing import Dict, Iterator, List, Optional

import requests

BASE_URL = "https://www.googleapis.com/youtube/v3"

logger = logging.getLogger(__name__)


class YouTubeAPIError(RuntimeError):
    pass


class YouTubeClient:
    def __init__(self, api_key: str, timeout: int = 20):
        self.api_key = api_key
        self.timeout = timeout

    def _request(self, endpoint: str, params: Dict) -> Dict:
        url = f"{BASE_URL}/{endpoint}"
        params = {**params, "key": self.api_key}
        resp = requests.get(url, params=params, timeout=self.timeout)
        if resp.status_code != 200:
            raise YouTubeAPIError(f"YouTube API error {resp.status_code}: {resp.text}")
        return resp.json()

    def _normalize_comment(self, item: Dict, video_id: str, parent_id: Optional[str]) -> Dict:
        snippet = item.get("snippet", {})
        return {
            "comment_id": item.get("id"),
            "parent_id": parent_id,
            "author": snippet.get("authorDisplayName"),
            "published_at": snippet.get("publishedAt"),
            "like_count": snippet.get("likeCount", 0),
            "text": snippet.get("textDisplay") or snippet.get("textOriginal") or "",
            "reply_count": snippet.get("totalReplyCount", 0),
            "video_id": video_id,
        }

    def fetch_comments(
        self,
        video_id: str,
        limit: int = 500,
        include_replies: bool = False,
        progress_cb=None,
    ) -> List[Dict]:
        params = {
            "part": "snippet,replies" if include_replies else "snippet",
            "videoId": video_id,
            "maxResults": 100,
            "textFormat": "plainText",
            "order": "time",
        }
        collected: List[Dict] = []
        page_token = None

        while True:
            if page_token:
                params["pageToken"] = page_token
            elif "pageToken" in params:
                params.pop("pageToken")

            data = self._request("commentThreads", params)
            items = data.get("items", [])

            for thread in items:
                top_comment = thread.get("snippet", {}).get("topLevelComment", {})
                if not top_comment:
                    continue

                top_id = top_comment.get("id")
                collected.append(self._normalize_comment(top_comment, video_id, None))
                if len(collected) >= limit:
                    return collected[:limit]

                if include_replies:
                    replies = thread.get("replies", {}).get("comments", [])
                    for reply in replies:
                        collected.append(self._normalize_comment(reply, video_id, top_id))
                        if len(collected) >= limit:
                            return collected[:limit]

                    reply_count = thread.get("snippet", {}).get("totalReplyCount", 0)
                    if reply_count and len(replies) < reply_count:
                        for reply in self._fetch_replies(top_id):
                            collected.append(self._normalize_comment(reply, video_id, top_id))
                            if len(collected) >= limit:
                                return collected[:limit]

            if progress_cb:
                try:
                    progress_cb(len(collected))
                except Exception:
                    pass

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return collected

    def _fetch_replies(self, parent_id: str) -> Iterator[Dict]:
        params = {
            "part": "snippet",
            "parentId": parent_id,
            "maxResults": 100,
            "textFormat": "plainText",
        }
        page_token = None
        while True:
            if page_token:
                params["pageToken"] = page_token
            elif "pageToken" in params:
                params.pop("pageToken")

            data = self._request("comments", params)
            items = data.get("items", [])
            for it in items:
                yield it

            page_token = data.get("nextPageToken")
            if not page_token:
                break
