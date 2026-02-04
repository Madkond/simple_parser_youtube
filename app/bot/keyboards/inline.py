from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def start_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="📎 Пример ссылки", callback_data="help:example")],
        [InlineKeyboardButton(text="Как работает бот", callback_data="help:how")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def link_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="Настройки", callback_data="menu:settings")],
        [InlineKeyboardButton(text="Быстрый экспорт", callback_data="run:quick")],
        [InlineKeyboardButton(text="↩️ Другая ссылка", callback_data="link:reset")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def settings_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="Формат", callback_data="menu:format")],
        [InlineKeyboardButton(text="Лимит", callback_data="menu:limit")],
        [InlineKeyboardButton(text="Сортировка", callback_data="menu:sort")],
        [InlineKeyboardButton(text="Ключевые слова", callback_data="menu:keywords")],
        [InlineKeyboardButton(text="Replies", callback_data="menu:replies")],
        [InlineKeyboardButton(text="Поля", callback_data="menu:fields")],
        [InlineKeyboardButton(text="✅ Собрать файл", callback_data="run:start")],
        [InlineKeyboardButton(text="Сброс", callback_data="settings:reset")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="menu:back")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="menu:cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def format_keyboard(current: str) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text=("✅ CSV" if current == "csv" else "CSV"), callback_data="fmt:csv")],
        [InlineKeyboardButton(text=("✅ XLSX" if current == "xlsx" else "XLSX"), callback_data="fmt:xlsx")],
        [InlineKeyboardButton(text=("✅ JSON" if current == "json" else "JSON"), callback_data="fmt:json")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="menu:settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def limit_keyboard(current: int) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text=("✅ 200" if current == 200 else "200"), callback_data="limit:200")],
        [InlineKeyboardButton(text=("✅ 500" if current == 500 else "500"), callback_data="limit:500")],
        [InlineKeyboardButton(text=("✅ 1000" if current == 1000 else "1000"), callback_data="limit:1000")],
        [InlineKeyboardButton(text=("✅ 2000" if current == 2000 else "2000"), callback_data="limit:2000")],
        [InlineKeyboardButton(text="Ввести число", callback_data="limit:input")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="menu:settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def sort_keyboard(current: str) -> InlineKeyboardMarkup:
    items = [
        ("none", "Без сортировки"),
        ("length_desc", "По длине (убывание)"),
        ("length_asc", "По длине (возрастание)"),
        ("likes_desc", "По лайкам (убывание)"),
        ("date_new", "По дате (новые)"),
        ("date_old", "По дате (старые)"),
    ]
    kb = []
    for key, label in items:
        text = ("✅ " + label) if current == key else label
        kb.append([InlineKeyboardButton(text=text, callback_data=f"sort:{key}")])
    kb.append([InlineKeyboardButton(text="↩️ Назад", callback_data="menu:settings")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def keywords_keyboard(mode: str, case_sensitive: bool, has_keywords: bool) -> InlineKeyboardMarkup:
    mode_label = "все" if mode == "all" else "любое"
    case_label = "учитывать" if case_sensitive else "игнорировать"
    kb = [
        [InlineKeyboardButton(text="Ввести слова", callback_data="kw:input")],
        [InlineKeyboardButton(text=f"Режим: {mode_label}", callback_data="kw:mode")],
        [InlineKeyboardButton(text=f"Регистр: {case_label}", callback_data="kw:case")],
        [InlineKeyboardButton(text=("Очистить" if has_keywords else "Очистить"), callback_data="kw:clear")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="menu:settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def replies_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text=("✅ Включить" if enabled else "Включить"), callback_data="replies:on")],
        [InlineKeyboardButton(text=("✅ Выключить" if not enabled else "Выключить"), callback_data="replies:off")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="menu:settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def fields_keyboard(fields: list) -> InlineKeyboardMarkup:
    items = [
        ("author", "Автор"),
        ("published_at", "Дата"),
        ("like_count", "Лайки"),
        ("text", "Текст"),
        ("reply_count", "Reply count"),
        ("comment_id", "Comment ID"),
        ("parent_id", "Parent ID"),
    ]
    kb = []
    for key, label in items:
        checked = "✅ " if key in fields else ""
        kb.append([InlineKeyboardButton(text=f"{checked}{label}", callback_data=f"fields:toggle:{key}")])
    kb.append([InlineKeyboardButton(text="↩️ Назад", callback_data="menu:settings")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def job_keyboard(job_id: str) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="Обновить", callback_data=f"job:refresh:{job_id}"),
            InlineKeyboardButton(text="⛔ Остановить", callback_data=f"job:cancel:{job_id}"),
        ],
        [InlineKeyboardButton(text="↩️ В настройки", callback_data="menu:settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def result_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="🔁 Повторить", callback_data="menu:settings")],
        [InlineKeyboardButton(text="📎 Новая ссылка", callback_data="link:reset")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
