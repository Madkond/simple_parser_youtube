import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from app.bot.handlers import export, filters, parse_link, start
from app.config import Config
from app.logging import setup_logging
from app.storage.redis import get_redis_async, get_redis_sync


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    config = Config.from_env()

    fsm_url = config.redis_url.rsplit("/", 1)[0] + f"/{config.redis_fsm_db}"
    storage = RedisStorage.from_url(fsm_url)
    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)

    redis_async = get_redis_async(config.redis_url)
    redis_sync = get_redis_sync(config.redis_url)

    dp["redis"] = redis_async
    dp["redis_sync"] = redis_sync
    dp["config"] = config

    dp.include_router(start.router)
    dp.include_router(filters.router)
    dp.include_router(export.router)
    dp.include_router(parse_link.router)

    logger.info("Bot started")
    try:
        await dp.start_polling(bot)
    finally:
        await redis_async.aclose()
        await redis_async.connection_pool.disconnect()
        redis_sync.close()


if __name__ == "__main__":
    asyncio.run(main())
