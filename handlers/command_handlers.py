from aiogram import Router
from aiogram.filters import Command
from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession
from shared.user import UserManager
from src.keyboards import Keyboard
from .stars_handler import pay_stars
from configs import config


async def get_menu_text(user_id: int, session: AsyncSession):
    has_balance, has_active_packet = await UserManager.get_posting_ability(user_id=user_id, session=session)
    if has_balance or has_active_packet:
        menu_text = config.main_menu_text_hi
    else:
        menu_text = config.main_menu_first_text
    return menu_text


async def start_menu(message: types.Message, session: AsyncSession, bot_config, logger):
    print('bot config')
    print(bot_config)
    if message.text.replace('/start ', '').split('=')[0] == 'pay_stars_id':
        payment_id = int(message.text.replace('/start ','').split('=')[1])
        await pay_stars(payment_id=payment_id, message=message, session=session)
        return

    menu_text = await get_menu_text(user_id=message.from_user.id, session=session)
    text = (menu_text % message.from_user.first_name)
    await message.answer(text, reply_markup=Keyboard.first_keyboard())

    await UserManager.update_activity(user_id=message.from_user.id, session=session)
    logger.info("Вызвал главное меню", extra={'user_id': message.from_user.id, 'username': message.from_user.username, 'action': 'get_main_menu'})


async def support(message: types.Message):
    await message.answer(f"Напишите администратору {config.support_link}, с удовольствием поможем вам.")


async def lotery(message: types.Message):
    await message.answer('Получить приз?', reply_markup=Keyboard.lotery_get_prize())


def create_command_router():
    command_router = Router()
    command_router.message.register(start_menu, Command('start'))
    command_router.message.register(support, Command('support'))
    command_router.message.register(lotery, Command('lotery'))
    return command_router
