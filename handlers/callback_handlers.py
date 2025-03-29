from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from src.states import TopUpBalance
from src.keyboards import Keyboard
import config
from shared.pricelist import PriceList
from shared.user import BalanceManager, PacketManager, UserManager
from datetime import datetime
from .command_handlers import get_menu_text

router = Router()


@router.callback_query(F.data == 'price')
async def get_price(call: CallbackQuery, session: AsyncSession):
    """Страница с информацией о стоимости публикации"""
    prices = await PriceList.get(session=session)

    # Берем первый пакет как основной
    price1 = f"{config.spec_emoji_1} <b>{prices[0].name}</b> — {prices[0].price} ₽"
    # Собираем остальные пакеты в price2
    price2 = "\n".join([f"{packet.name} - {packet.price} ₽" for packet in prices[1:]]) if len(prices) > 1 else ""

    text = config.price_text % (price1, price2)

    keyboard = Keyboard.price_menu()
    await call.message.edit_text(text=text, reply_markup=keyboard, parse_mode='html')


@router.callback_query(F.data == 'balance')
async def get_balance(call: CallbackQuery, session: AsyncSession):
    """Страница с информацией о балансе"""
    balance = await BalanceManager.get_balance(user_id=call.from_user.id, session=session)
    packet = await PacketManager.get_user_packet(user_id=call.from_user.id, session=session)

    if not packet:
        keyboard = Keyboard.price_menu()

        price = await PriceList.get_onetime_price(session=session)
        price = price[0].price
        text = config.balance_text % (str(balance), f"{balance//price} размещений")
        await call.message.edit_text(text=text, reply_markup=keyboard, parse_mode='html')
        return

    packet, packet_name, count_per_day = packet[0], packet[1], packet[2]
    packet_ending = datetime.strftime(packet.ending_at, '%d.%m.%Y')
    if packet.activated_at < datetime.now():
        keyboard = Keyboard.prolong_packet_menu()
        text = config.balance_active_packet_text % (str(balance), packet_name, count_per_day, packet_ending)
        await call.message.edit_text(text=text, reply_markup=keyboard, parse_mode='html')
        return
    elif packet.activated_at >= datetime.now():
        keyboard = Keyboard.activate_packet_menu(packet.id)
        activated_date = datetime.strftime(packet.activated_at, '%d.%m.%Y')
        text = config.balance_inactive_packet_text % (str(balance), packet_name, activated_date, packet_ending)
        await call.message.edit_text(text=text, reply_markup=keyboard, parse_mode='html')
        return


@router.callback_query(F.data.in_(['buy_packet', 'buypacket']))
async def get_packet_menu(call: CallbackQuery, session: AsyncSession):
    """Страница с выбором пакета для покупки"""
    pricelist = await PriceList.get(session=session)

    await call.message.edit_text(config.packet_text, reply_markup=Keyboard.get_packets_keyboard(packets_list=pricelist), parse_mode='html')

@router.callback_query(F.data.startswith("activate_packet_id"))
async def activate_packet_handler(call: CallbackQuery, session: AsyncSession):
    """Активация пакета"""
    packet_id = int(call.data.replace('activate_packet_id=', ''))

    result =  await PacketManager.activate_packet(packet_id=packet_id, session=session)
    print(result)
    if not result:
        await call.message.edit_text(text=config.error_activation_packet,
                                     reply_markup=Keyboard.support_keyboard(), parse_mode='html')
        return

    packet_name = result.get('name')
    packet_ending_date = result.get('ending_at')
    packet_ending_date = datetime.strftime(packet_ending_date, '%d.%m.%Y')
    text = config.success_activated_packet % (packet_name, packet_ending_date)

    await call.message.edit_text(text=text, reply_markup=Keyboard.create_auto(), parse_mode='html')


@router.callback_query(F.data.in_({
    'upbalance', 'upbalance_cas', 'upbalance_sber', 'upbalance_yoo', 'upbalance_lot'}))
async def update_balance(call: CallbackQuery, state: FSMContext, logger):
    """Страница пополнения баланса"""
    await call.message.delete()
    await call.message.answer(
        "<b>Напишите сумму пополнения числом </b> (Пример: 500)",
        reply_markup=Keyboard.cancel_menu(),
        parse_mode='html'
    )
    await state.set_state(TopUpBalance.amount)

    logger.info(f'Вошел в состояние TopUpBalance:amount',
                extra={'user_id': call.from_user.id,
                       'username': call.from_user.username,
                       'action': 'state_info'})


@router.callback_query(F.data == 'back')
async def back_menu(call: CallbackQuery, session: AsyncSession):
    """Выход в главное меню"""
    menu_text = await get_menu_text(user_id=call.from_user.id, session=session)
    text = (menu_text % call.from_user.first_name)
    await call.message.edit_text(text, reply_markup=Keyboard.first_keyboard())


@router.callback_query(F.data == 'x')
async def recomended_designer_callback(callback_query: CallbackQuery):
    await callback_query.answer(
        text="🏅 Этот дизайнер - проверен администрацией и рекомендован к работе.",
        show_alert=True
    )
    logger.info(f'Открыл плашку рекомендации',
                extra={'user_id': call.from_user.id,
                       'username': call.from_user.username,
                       'action': 'post_conversion'})


@router.callback_query(F.data == 'getprize')
async def get_lotery_prize(callback_query: CallbackQuery):
    pass