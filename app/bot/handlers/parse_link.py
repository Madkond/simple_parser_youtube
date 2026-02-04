from aiogram import Router
from aiogram.types import Message

from app.bot.handlers.utils import get_user_settings, set_user_settings
from app.bot.keyboards.inline import link_keyboard
from app.services.parsing import extract_video_id

router = Router()


@router.message()
async def parse_link(message: Message, redis) -> None:
    if not message.text:
        return

    video_id = extract_video_id(message.text)
    if not video_id:
        await message.answer("Не смог распознать ссылку. Пришли ссылку на видео YouTube.")
        return

    settings = await get_user_settings(redis, message.from_user.id)
    settings["video_id"] = video_id
    await set_user_settings(redis, message.from_user.id, settings)

    text = f"✅ Видео распознано\nID: `{video_id}`\n\nНастроить выгрузку?"
    await message.answer(text, reply_markup=link_keyboard())
