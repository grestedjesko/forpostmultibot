from aiogram.types import CallbackQuery
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from configs import config
from src.keyboards import Keyboard
from src.states import PostStates
import handlers.post.auto_post_handlers as auto_post_handlers
import handlers.post.onetime_post_handlers as onetime_post_handlers
from aiogram.filters import StateFilter
from src.states import AutoPostStates


def create_post_router():
    router = Router()
    router.message.register(onetime_post_handlers.create_post, StateFilter(PostStates.text))
    router.callback_query.register(onetime_post_handlers.create_hand_post, F.data == 'create_hand')
    router.callback_query.register(onetime_post_handlers.post_onetime_wrapper, F.data.startswith("post_onetime_id"))
    router.callback_query.register(onetime_post_handlers.post_onetime_balance_wrapper,
                                   F.data.startswith("post_onetime_balance_id"))
    router.callback_query.register(onetime_post_handlers.edit_post, F.data.startswith("edit_post_id"))
    router.callback_query.register(onetime_post_handlers.cancel_post, F.data.startswith("cancel_post_id"))

    router.message.register(auto_post_handlers.create_auto_post_time, StateFilter(AutoPostStates.time))
    router.message.register(auto_post_handlers.get_auto_post_text, StateFilter(AutoPostStates.text))
    router.message.register(auto_post_handlers.edit_time, StateFilter(AutoPostStates.new_time))
    router.callback_query.register(auto_post_handlers.create_auto_post, F.data == 'create_auto')
    router.callback_query.register(auto_post_handlers.recreate_auto, F.data == "recreate_auto")
    router.callback_query.register(auto_post_handlers.change_time_auto_post, F.data.startswith("change_time_autopost_id"))
    router.callback_query.register(auto_post_handlers.delete_auto_post, F.data.startswith("cancel_autopost_id"))
    router.callback_query.register(auto_post_handlers.edit_auto_post, F.data.startswith("edit_autopost_id"))
    router.callback_query.register(auto_post_handlers.start_auto_post, F.data.startswith("start_autopost_id"))

    return router
