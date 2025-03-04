from aiogram.fsm.state import StatesGroup, State


class TopUpBalance(StatesGroup):
    amount = State()


class PostStates(StatesGroup):
    text = State()


class AutoPostStates(StatesGroup):
    text = State()
    images_links = State()
    time = State()
    file_ids = State()
    time_count = State()
    media_group = State()