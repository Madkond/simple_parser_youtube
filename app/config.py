import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=_ROOT / ".env")


@dataclass(frozen=True)
class Config:
    bot_token: str
    yt_api_key: str
    redis_url: str
    redis_fsm_db: int
    export_dir: str
    rate_limit_seconds: int
    default_limit: int

    @classmethod
    def from_env(cls) -> "Config":
        bot_token = os.getenv("BOT_TOKEN", "").strip()
        yt_api_key = os.getenv("YT_API_KEY", "").strip()
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0").strip()
        redis_fsm_db = int(os.getenv("REDIS_FSM_DB", "1"))
        export_dir = os.getenv("EXPORT_DIR", str(_ROOT / "exports")).strip()
        rate_limit_seconds = int(os.getenv("RATE_LIMIT_SECONDS", "120"))
        default_limit = int(os.getenv("DEFAULT_LIMIT", "200"))

        if not bot_token:
            raise RuntimeError("BOT_TOKEN is required")
        if not yt_api_key:
            raise RuntimeError("YT_API_KEY is required")

        return cls(
            bot_token=bot_token,
            yt_api_key=yt_api_key,
            redis_url=redis_url,
            redis_fsm_db=redis_fsm_db,
            export_dir=export_dir,
            rate_limit_seconds=rate_limit_seconds,
            default_limit=default_limit,
        )
