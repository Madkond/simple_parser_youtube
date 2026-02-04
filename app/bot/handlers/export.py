import json
import time
from uuid import uuid4

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message
from rq import Queue

from app.bot.handlers.utils import get_last_job_ts, get_user_settings, set_last_job_ts, set_user_settings
from app.bot.keyboards.inline import job_keyboard, result_keyboard
from app.storage.cache_keys import job_cancel_key, job_progress_key, job_result_key, job_status_key

router = Router()


def _enqueue_job(redis_sync, settings: dict) -> str:
    q = Queue("default", connection=redis_sync)
    job_id = str(uuid4())
    q.enqueue("app.workers.tasks.fetch_and_export", job_id, settings)
    return job_id


def _get_job_status(redis_async, job_id: str):
    return redis_async.get(job_status_key(job_id))


def _get_job_progress(redis_async, job_id: str):
    return redis_async.get(job_progress_key(job_id))


def _get_job_result(redis_async, job_id: str):
    return redis_async.get(job_result_key(job_id))


def _progress_bar(current: int, total: int) -> str:
    total = max(total, 1)
    current = max(0, min(current, total))
    filled = int((current / total) * 10)
    return "[" + ("█" * filled) + ("░" * (10 - filled)) + f"] {int((current/total)*100)}%"


def _format_status(status: str, progress_raw: bytes | None) -> str:
    progress = ""
    if progress_raw:
        try:
            data = json.loads(progress_raw.decode("utf-8"))
            message = data.get("message", "")
            fetched = data.get("fetched", 0)
            limit = int(data.get("limit") or 0)
            bar = _progress_bar(fetched, limit) if limit else ""
            progress = f"\n{message} | fetched: {fetched}" + (f"\n{bar}" if bar else "")
        except Exception:
            pass
    return f"Статус: {status}{progress}"


async def _run_job(message, user_id: int, settings: dict, rate_limit_seconds: int, redis, redis_sync):
    last_ts = await get_last_job_ts(redis, user_id)
    now = time.time()
    if now - last_ts < rate_limit_seconds:
        await message.answer("Слишком часто. Подожди немного и попробуй снова.")
        return

    await set_last_job_ts(redis, user_id, now)
    job_id = _enqueue_job(redis_sync, settings)
    await redis.setex(job_status_key(job_id), 60 * 60 * 4, b"queued")
    await redis.setex(job_progress_key(job_id), 60 * 60 * 4, b"{\"message\": \"Queued\", \"fetched\": 0}")
    settings["last_job_id"] = job_id
    await set_user_settings(redis, user_id, settings)

    await message.answer(
        f"Задача поставлена в очередь. Job ID: {job_id}",
        reply_markup=job_keyboard(job_id),
    )


@router.callback_query(F.data == "run:quick")
async def run_quick(callback: CallbackQuery, redis, redis_sync, config) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    if not settings.get("video_id"):
        await callback.message.answer("Сначала пришли ссылку на видео.")
        await callback.answer()
        return
    rate_limit_seconds = config.rate_limit_seconds
    await _run_job(callback.message, callback.from_user.id, settings, rate_limit_seconds, redis, redis_sync)
    await callback.answer()


@router.callback_query(F.data == "run:start")
async def run_job_callback(callback: CallbackQuery, redis, redis_sync, config) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    if not settings.get("video_id"):
        await callback.message.answer("Сначала пришли ссылку на видео.")
        await callback.answer()
        return
    rate_limit_seconds = config.rate_limit_seconds
    await _run_job(callback.message, callback.from_user.id, settings, rate_limit_seconds, redis, redis_sync)
    await callback.answer()


@router.message(Command("run"))
async def run_job_cmd(message: Message, redis, redis_sync, config) -> None:
    settings = await get_user_settings(redis, message.from_user.id)
    if not settings.get("video_id"):
        await message.answer("Сначала пришли ссылку на видео.")
        return
    rate_limit_seconds = config.rate_limit_seconds
    await _run_job(message, message.from_user.id, settings, rate_limit_seconds, redis, redis_sync)


@router.callback_query(F.data.startswith("job:refresh:"))
async def refresh_status(callback: CallbackQuery, redis) -> None:
    job_id = callback.data.split(":", 2)[2]
    status_raw = await _get_job_status(redis, job_id)
    progress_raw = await _get_job_progress(redis, job_id)
    status = status_raw.decode("utf-8") if status_raw else "unknown"
    await callback.message.answer(_format_status(status, progress_raw))

    if status == "done":
        result_raw = await _get_job_result(redis, job_id)
        if result_raw:
            try:
                data = json.loads(result_raw.decode("utf-8"))
                file_path = data.get("file_path")
                if file_path:
                    doc = FSInputFile(file_path)
                    await callback.message.answer_document(
                        doc,
                        caption=f"✅ Готово\nСобрано: {data.get('count', 0)}\nФормат: {data.get('format', 'csv').upper()}",
                    )
                    await callback.message.answer("", reply_markup=result_keyboard())
            except Exception:
                pass

    await callback.answer()


@router.callback_query(F.data.startswith("job:cancel:"))
async def cancel_job(callback: CallbackQuery, redis) -> None:
    job_id = callback.data.split(":", 2)[2]
    await redis.setex(job_cancel_key(job_id), 60 * 60, b"1")
    await callback.message.answer("⛔ Задача остановлена")
    await callback.answer()


@router.callback_query(F.data.startswith("get_file:"))
async def get_file(callback: CallbackQuery, redis) -> None:
    job_id = callback.data.split(":", 1)[1]
    result_raw = await _get_job_result(redis, job_id)
    if not result_raw:
        await callback.message.answer("Файл пока не готов. Нажми 'Обновить'.")
        await callback.answer()
        return

    try:
        data = json.loads(result_raw.decode("utf-8"))
    except Exception:
        await callback.message.answer("Не удалось прочитать результат задачи.")
        await callback.answer()
        return

    file_path = data.get("file_path")
    if not file_path:
        await callback.message.answer("Файл не найден.")
        await callback.answer()
        return

    doc = FSInputFile(file_path)
    await callback.message.answer_document(doc, caption=f"✅ Готово\nСобрано: {data.get('count', 0)}\nФормат: {data.get('format', 'csv').upper()}")
    await callback.message.answer("", reply_markup=result_keyboard())
    await callback.answer()


@router.message(Command("status"))
async def status_cmd(message: Message, redis) -> None:
    settings = await get_user_settings(redis, message.from_user.id)
    job_id = settings.get("last_job_id")
    if not job_id:
        await message.answer("Нет активных задач. Сначала запусти /run.")
        return

    status_raw = await _get_job_status(redis, job_id)
    progress_raw = await _get_job_progress(redis, job_id)
    status = status_raw.decode("utf-8") if status_raw else "unknown"
    await message.answer(_format_status(status, progress_raw), reply_markup=job_keyboard(job_id))
