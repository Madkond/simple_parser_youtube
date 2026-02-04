from aiogram.fsm.state import State, StatesGroup


class KeywordInput(StatesGroup):
    waiting_keywords = State()


class LimitInput(StatesGroup):
    waiting_limit = State()
