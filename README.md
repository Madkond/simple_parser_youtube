# YouTube Comments Parser Bot

## What it does
- Accepts a YouTube link in Telegram
- Fetches comments via YouTube Data API v3
- Filters/sorts/limits
- Exports to CSV or XLSX and sends the file back

## Quick start (Docker)
1. Copy `.env.example` to `.env` and fill `BOT_TOKEN` and `YT_API_KEY`.
2. Build and run:

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Running locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export BOT_TOKEN=...
export YT_API_KEY=...
export REDIS_URL=redis://localhost:6379/0

# Start redis separately
python -m app.bot.main
```

Start worker in another terminal:
```bash
python -m app.workers.worker
```

## Commands
- `/set_keywords word1, word2`
- `/set_sort none | length_desc | length_asc`
- `/set_limit 500`
- `/set_format csv | xlsx`
- `/run`

## Notes
- Rate limit: 1 job per minute by default.
- Caching: comments are cached for 12 hours to save quota.
