from aiogram import Router, F
from aiogram import types, Bot
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from .command_handlers import start_menu
from shared.bot_config import BotConfig
from configs import config


async def answer_chat(message: types.Message, bot: Bot, logger):
    await message.delete()
    await message.answer(config.chat_text)
    user = message.from_user
    await bot.restrict_chat_member(chat_id=message.chat.id,
                                   user_id=message.from_user.id,
                                   permissions=types.ChatPermissions(False))
    logger.info("Отправил запрещенное сообщение в чате",
                extra={'user_id': message.from_user.id,
                       'username': message.from_user.username,
                       'action': 'chat_message_sended'})


async def cancel_state(message: types.Message, state: FSMContext, session: AsyncSession, bot_config: BotConfig, logger):
    state_text = await state.get_state()
    await state.clear()
    s = await message.answer('Отменено', reply_markup=types.ReplyKeyboardRemove())
    await s.delete()
    await start_menu(message=message, session=session, logger=logger, bot_config=bot_config)

    logger.info('Нажал кнопку "Отмена"',
                extra={'user_id': message.from_user.id,
                       'username': message.from_user.username,
                       'action': 'button_info'})
    logger.info(f'Вышел из состояния {state_text}',
                extra={'user_id': message.from_user.id,
                       'username': message.from_user.username,
                       'action': 'state_info'})


def create_message_router():
    message_router = Router()
    message_router.message.register(answer_chat, F.chat.id == config.chat_id)
    message_router.message.register(cancel_state, F.text == '❌ Отмена')

    return message_router
