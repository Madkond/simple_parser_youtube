from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.handlers.utils import format_settings, get_user_settings, set_user_settings
from app.bot.keyboards.inline import (
    fields_keyboard,
    format_keyboard,
    keywords_keyboard,
    limit_keyboard,
    replies_keyboard,
    settings_keyboard,
    sort_keyboard,
    link_keyboard,
    start_keyboard,
)
from app.bot.states import KeywordInput, LimitInput

router = Router()


@router.callback_query(F.data == "menu:settings")
async def menu_settings(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    text = "Настройки выгрузки\n\n" + format_settings(settings)
    await callback.message.edit_text(text, reply_markup=settings_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:back")
async def menu_back(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    video_id = settings.get("video_id")
    if video_id:
        text = f"✅ Видео распознано\nID: `{video_id}`\n\nНастроить выгрузку?"
        await callback.message.edit_text(text, reply_markup=link_keyboard())
    else:
        await callback.message.edit_text(
            "Привет.\nОтправь ссылку на YouTube-видео — соберу комментарии и верну файл.",
            reply_markup=start_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "menu:cancel")
async def menu_cancel(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    settings["video_id"] = None
    await set_user_settings(redis, callback.from_user.id, settings)
    await callback.message.edit_text(
        "Отправь новую ссылку на YouTube-видео.",
        reply_markup=start_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "link:reset")
async def link_reset(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    settings["video_id"] = None
    await set_user_settings(redis, callback.from_user.id, settings)
    await callback.message.edit_text(
        "Отправь новую ссылку на YouTube-видео.",
        reply_markup=start_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:format")
async def menu_format(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    text = f"Формат файла\nТекущий: {settings.get('format', 'csv').upper()}"
    await callback.message.edit_text(text, reply_markup=format_keyboard(settings.get("format", "csv")))
    await callback.answer()


@router.callback_query(F.data.startswith("fmt:"))
async def set_format(callback: CallbackQuery, redis) -> None:
    fmt = callback.data.split(":", 1)[1]
    settings = await get_user_settings(redis, callback.from_user.id)
    settings["format"] = fmt
    await set_user_settings(redis, callback.from_user.id, settings)
    text = f"Формат файла\nТекущий: {fmt.upper()}"
    await callback.message.edit_text(text, reply_markup=format_keyboard(fmt))
    await callback.answer("Формат обновлен")


@router.callback_query(F.data == "menu:limit")
async def menu_limit(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    text = f"Сколько комментариев собрать?\nТекущий лимит: {settings.get('limit', 500)}"
    await callback.message.edit_text(text, reply_markup=limit_keyboard(int(settings.get("limit", 500))))
    await callback.answer()


@router.callback_query(F.data.startswith("limit:"))
async def set_limit(callback: CallbackQuery, state: FSMContext, redis) -> None:
    action = callback.data.split(":", 1)[1]
    if action == "input":
        await state.set_state(LimitInput.waiting_limit)
        await callback.message.answer("Введи число (например 750)")
        await callback.answer()
        return
    limit = int(action)
    settings = await get_user_settings(redis, callback.from_user.id)
    settings["limit"] = limit
    await set_user_settings(redis, callback.from_user.id, settings)
    text = f"Сколько комментариев собрать?\nТекущий лимит: {limit}"
    await callback.message.edit_text(text, reply_markup=limit_keyboard(limit))
    await callback.answer("Лимит обновлен")


@router.message(LimitInput.waiting_limit)
async def limit_input(message: Message, state: FSMContext, redis) -> None:
    try:
        limit = int((message.text or "").strip())
    except ValueError:
        await message.answer("Нужно число. Например 750.")
        return
    settings = await get_user_settings(redis, message.from_user.id)
    settings["limit"] = limit
    await set_user_settings(redis, message.from_user.id, settings)
    await state.clear()
    await message.answer("Лимит обновлен.", reply_markup=settings_keyboard())


@router.callback_query(F.data == "menu:sort")
async def menu_sort(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    text = "Сортировка комментариев\nТекущая: " + settings.get("sort", "none")
    await callback.message.edit_text(text, reply_markup=sort_keyboard(settings.get("sort", "none")))
    await callback.answer()


@router.callback_query(F.data.startswith("sort:"))
async def set_sort(callback: CallbackQuery, redis) -> None:
    sort = callback.data.split(":", 1)[1]
    settings = await get_user_settings(redis, callback.from_user.id)
    settings["sort"] = sort
    await set_user_settings(redis, callback.from_user.id, settings)
    text = "Сортировка комментариев\nТекущая: " + sort
    await callback.message.edit_text(text, reply_markup=sort_keyboard(sort))
    await callback.answer("Сортировка обновлена")


@router.callback_query(F.data == "menu:keywords")
async def menu_keywords(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    text = (
        "Фильтр по ключевым словам\n"
        f"Сейчас: {', '.join(settings.get('keywords', [])) or 'нет'}\n"
        f"Режим: {'все' if settings.get('keywords_mode')=='all' else 'любое'}\n"
        f"Регистр: {'учитывать' if settings.get('keywords_case_sensitive') else 'игнорировать'}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=keywords_keyboard(
            settings.get("keywords_mode", "any"),
            bool(settings.get("keywords_case_sensitive", False)),
            bool(settings.get("keywords")),
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "kw:input")
async def enter_keywords(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(KeywordInput.waiting_keywords)
    await callback.message.answer("Введи слова через запятую\nПример: курс, скидка, промокод")
    await callback.answer()


@router.callback_query(F.data == "kw:mode")
async def toggle_kw_mode(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    settings["keywords_mode"] = "all" if settings.get("keywords_mode") == "any" else "any"
    await set_user_settings(redis, callback.from_user.id, settings)
    await menu_keywords(callback, redis)


@router.callback_query(F.data == "kw:case")
async def toggle_kw_case(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    settings["keywords_case_sensitive"] = not bool(settings.get("keywords_case_sensitive", False))
    await set_user_settings(redis, callback.from_user.id, settings)
    await menu_keywords(callback, redis)


@router.callback_query(F.data == "kw:clear")
async def clear_kw(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    settings["keywords"] = []
    await set_user_settings(redis, callback.from_user.id, settings)
    await menu_keywords(callback, redis)


@router.message(KeywordInput.waiting_keywords)
async def keywords_input(message: Message, state: FSMContext, redis) -> None:
    text = message.text or ""
    settings = await get_user_settings(redis, message.from_user.id)
    settings["keywords"] = [t.strip() for t in text.split(",") if t.strip()]
    await set_user_settings(redis, message.from_user.id, settings)
    await state.clear()
    await message.answer("Ключевые слова обновлены.", reply_markup=settings_keyboard())


@router.callback_query(F.data == "menu:replies")
async def menu_replies(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    text = f"Собирать ответы на комментарии?\nСейчас: {'да' if settings.get('include_replies') else 'нет'}"
    await callback.message.edit_text(text, reply_markup=replies_keyboard(bool(settings.get("include_replies"))))
    await callback.answer()


@router.callback_query(F.data.startswith("replies:"))
async def set_replies(callback: CallbackQuery, redis) -> None:
    value = callback.data.split(":", 1)[1] == "on"
    settings = await get_user_settings(redis, callback.from_user.id)
    settings["include_replies"] = value
    await set_user_settings(redis, callback.from_user.id, settings)
    await menu_replies(callback, redis)


@router.callback_query(F.data == "menu:fields")
async def menu_fields(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    text = "Какие поля включить в файл?"
    await callback.message.edit_text(text, reply_markup=fields_keyboard(settings.get("fields", [])))
    await callback.answer()


@router.callback_query(F.data.startswith("fields:toggle:"))
async def toggle_field(callback: CallbackQuery, redis) -> None:
    key = callback.data.split(":", 2)[2]
    settings = await get_user_settings(redis, callback.from_user.id)
    fields = set(settings.get("fields", []))
    if key in fields:
        fields.remove(key)
    else:
        fields.add(key)
    settings["fields"] = list(fields)
    await set_user_settings(redis, callback.from_user.id, settings)
    await menu_fields(callback, redis)


@router.callback_query(F.data == "settings:reset")
async def reset_settings(callback: CallbackQuery, redis) -> None:
    settings = await get_user_settings(redis, callback.from_user.id)
    settings.update(
        {
            "format": "csv",
            "sort": "none",
            "keywords": [],
            "keywords_mode": "any",
            "keywords_case_sensitive": False,
            "min_len": None,
            "limit": 500,
            "include_replies": False,
            "fields": ["author", "published_at", "like_count", "text"],
        }
    )
    await set_user_settings(redis, callback.from_user.id, settings)
    await menu_settings(callback, redis)
