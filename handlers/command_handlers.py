from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.filters import Command
from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from database.models import User
from shared.user import UserManager
from src.keyboards import Keyboard
from config import main_menu_text

command_router = Router()


@command_router.message(Command('start'))
async def start_menu(message: types.Message, session: AsyncSession):
    hello_message = (main_menu_text % message.from_user.first_name)

    await message.answer(hello_message, reply_markup=Keyboard.first_keyboard())

    user = UserManager()
    await user.update_activity(user_id=message.from_user.id, session=session)


@command_router.message(Command('support'))
async def support(message: types.Message):
    #await bot.send_message(message.from_user.id,f"Напишите администратору {support_tg}, с удовольствием поможем вам.")
    pass