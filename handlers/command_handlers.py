from aiogram import Router
from aiogram.filters import Command
from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession
from shared.user import UserManager
from src.keyboards import Keyboard
from .topup_handlers import pay_stars
import config

command_router = Router()


async def get_menu_text(user_id: int, session: AsyncSession):

    has_balance, has_active_packet = await UserManager.get_posting_ability(user_id=user_id, session=session)
    if has_balance or has_active_packet:
        menu_text = config.main_menu_text
    else:
        menu_text = config.main_menu_first_text
    return menu_text


@command_router.message(Command('start'))
async def start_menu(message: types.Message, session: AsyncSession):
    if message.text.replace('/start ', '').split('=')[0] == 'pay_stars_id':
        payment_id = int(message.text.replace('/start ','').split('=')[1])
        await pay_stars(payment_id=payment_id, message=message, session=session)
        return

    menu_text = await get_menu_text(user_id=message.from_user.id, session=session)
    text = (menu_text % message.from_user.first_name)

    await message.answer(text, reply_markup=Keyboard.first_keyboard())

    await UserManager.update_activity(user_id=message.from_user.id, session=session)


@command_router.message(Command('support'))
async def support(message: types.Message):
    #await bot.send_message(message.from_user.id,f"Напишите администратору {support_tg}, с удовольствием поможем вам.")
    pass