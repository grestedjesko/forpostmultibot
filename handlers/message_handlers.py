from aiogram import Router, F
from aiogram import types, Bot
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from .command_handlers import start_menu
import config

CHAT_ID=123

message_router = Router()


@message_router.message(F.chat.id == CHAT_ID)
async def answer_chat(message: types.Message, bot: Bot):
    await message.delete()
    await message.answer(config.chat_text)
    user = message.from_user
    await bot.restrict_chat_member(chat_id=message.chat.id,
                                   user_id=message.from_user.id,
                                   permissions=types.ChatPermissions(False))

@message_router.message(F.text == '❌ Отмена')
async def cancel_state(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    s = await message.answer('Отменено', reply_markup=types.ReplyKeyboardRemove())
    await s.delete()
    await start_menu(message=message, session=session)