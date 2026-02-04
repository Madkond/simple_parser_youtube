from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.inline import start_keyboard

router = Router()


@router.message(Command("start", "help"))
async def start(message: Message) -> None:
    text = (
        "Привет.\n"
        "Отправь ссылку на YouTube-видео — соберу комментарии и верну файл."
    )
    await message.answer(text, reply_markup=start_keyboard())


@router.callback_query(F.data == "help:example")
async def example(callback: CallbackQuery) -> None:
    await callback.message.answer("Пример ссылки:\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ")
    await callback.answer()


@router.callback_query(F.data == "help:how")
async def how(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Как это работает:\n"
        "1) Ты отправляешь ссылку\n"
        "2) Выбираешь параметры\n"
        "3) Бот собирает комментарии и присылает файл"
    )
    await callback.answer()
