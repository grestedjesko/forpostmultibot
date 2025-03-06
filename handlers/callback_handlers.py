from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from src.states import TopUpBalance
from src.keyboards import Keyboard
import config
from shared.pricelist import PriceList
from shared.user import BalanceManager

router = Router()


@router.callback_query(F.data == 'price')
async def get_price(call: CallbackQuery, session: AsyncSession):
    """Страница с информацией о стоимости публикации"""
    prices = await PriceList().get(session=session)

    # Берем первый пакет как основной
    price1 = f"{config.spec_emoji_1} <b>{prices[0].name}</b> — {prices[0].price} ₽"

    # Собираем остальные пакеты в price2
    price2 = "\n".join([f"{packet.name} - {packet.price} ₽" for packet in prices[1:]]) if len(prices) > 1 else ""

    # Подставляем значения в шаблон
    text = config.price_text % (price1, price2)

    keyboard = Keyboard.price_menu()
    await call.message.edit_text(text=text, reply_markup=keyboard, parse_mode='html')


@router.callback_query(F.data == 'balance')
async def get_balance(call: CallbackQuery, session: AsyncSession):
    """Страница с информацией о балансе"""
    balance = await BalanceManager().get_balance(user_id=call.from_user.id, session=session)

    text = f"""Ваш баланс: {balance} ₽"""

    keyboard = Keyboard.balance_menu()
    await call.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.in_(['buy_packet', 'buypacket']))
async def get_packet_menu(call: CallbackQuery, session: AsyncSession):
    """Страница с выбором пакета для покупки"""
    pricelist = await PriceList().get(session=session)

    await call.message.edit_text(config.packet_text, reply_markup=Keyboard.get_packets_keyboard(packets_list=pricelist))


@router.callback_query(F.data.in_({
    'upbalance', 'upbalance_cas', 'upbalance_sber', 'upbalance_yoo', 'upbalance_lot'}))
async def update_balance(call: CallbackQuery, state: FSMContext):
    """Страница пополнения баланса"""
    await call.message.delete()
    await call.message.answer(
        "<b>Напишите сумму пополнения числом </b> (Пример: 500)",
        reply_markup=Keyboard.cancel_menu(),
        parse_mode='html'
    )
    await state.set_state(TopUpBalance.amount)

@router.callback_query(F.data == 'back')
async def back_menu(call: CallbackQuery):
    """Выход в главное меню"""
    hello_message = (config.main_menu_text % call.from_user.first_name)
    await call.message.edit_text(hello_message, reply_markup=Keyboard.first_keyboard())


@router.callback_query(F.data == 'x')
async def recomended_designer_callback(callback_query: CallbackQuery):
    await callback_query.answer(
        text="🏅 Этот дизайнер - проверен администрацией и рекомендован к работе.",
        show_alert=True
    )


@router.callback_query(F.data == 'getprize')
async def get_lotery_prize(callback_query: CallbackQuery):
    pass