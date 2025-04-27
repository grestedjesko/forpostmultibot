from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from src.states import TopUpBalance
from src.keyboards import Keyboard
from configs import config
from shared.pricelist import PriceList
from shared.user import BalanceManager
from shared.user_packet import PacketManager
from datetime import datetime
from .command_handlers import get_menu_text
from shared.bonus.global_deposit_bonus import DepositBonusManager
from configs.bonus_config import BonusConfig
from shared.bonus.lotery import Lotery
from shared.bonus.promo_manager import PromoManager
from zoneinfo import ZoneInfo


async def get_price(call: CallbackQuery, session: AsyncSession):
    """Страница с информацией о стоимости публикации"""
    packet_bonus = await PromoManager.get_packet_bonus(user_id=call.from_user.id,
                                                       session=session)
    placement_bonus = None
    if not packet_bonus:
        placement_bonus = await PromoManager.get_packet_placement_bonus(user_id=call.from_user.id,
                                                                        session=session)
    deposit_bonus = await PromoManager.get_deposit_bonus(user_id=call.from_user.id,
                                                         session=session)
    # выдача скидки (фикса или рубли)
    prices = await PriceList.get(session=session, packet_promotion=packet_bonus)
    price1 = f"{config.spec_emoji_1} <b>{prices[0].name}</b> — {prices[0].price} ₽"
    price2 = ""
    for packet in prices[1:]:
        if packet.discount:
            price2 += f"{packet.name} - {packet.price}₽ ({packet.discount})"
        else:
            price2 += f"{packet.name} - {packet.price}₽"
        price2 += '\n'
    text = config.price_text % (price1, price2)
    # учесть бонус в клавиатуре
    keyboard = Keyboard.price_menu(packet_bonus=packet_bonus,
                                   placement_bonus=placement_bonus,
                                   deposit_bonus=deposit_bonus)
    await call.message.edit_text(text=text, reply_markup=keyboard, parse_mode='html')
    await call.answer()


async def get_balance(call: CallbackQuery, session: AsyncSession):
    print('get_balance')
    """Страница с информацией о балансе"""
    balance = await BalanceManager.get_balance(user_id=call.from_user.id, session=session)
    packet = await PacketManager.get_user_packet(user_id=call.from_user.id, session=session)
    if not packet:
        packet_bonus = await PromoManager.get_packet_bonus(user_id=call.from_user.id,
                                                           session=session)
        placement_bonus = None
        if not packet_bonus:
            placement_bonus = await PromoManager.get_packet_bonus(user_id=call.from_user.id,
                                                                  session=session)
        deposit_bonus = await PromoManager.get_packet_bonus(user_id=call.from_user.id,
                                                            session=session)

        keyboard = Keyboard.price_menu(packet_bonus=packet_bonus,
                                       placement_bonus=placement_bonus,
                                       deposit_bonus=deposit_bonus)
        price = await PriceList.get_onetime_price(session=session)
        print(price)
        if price[0].price:
            text = config.balance_text % (str(balance), f"{balance // price} размещений")
        else:
            text = config.balance_noprice_text % (str(balance))

        await call.message.edit_text(text=text, reply_markup=keyboard, parse_mode='html')
        return
    packet, packet_name, count_per_day = packet[0], packet[1], packet[2]
    packet_ending = datetime.strftime(packet.ending_at, '%d.%m.%Y')
    if packet.activated_at < datetime.now(ZoneInfo("Europe/Moscow")):
        keyboard = Keyboard.prolong_packet_menu(packet_id=packet.id)
        text = config.balance_active_packet_text % (str(balance), packet_name, packet.today_posts, packet_ending)
        await call.message.edit_text(text=text, reply_markup=keyboard, parse_mode='html')
        return
    elif packet.activated_at >= datetime.now(ZoneInfo("Europe/Moscow")):
        keyboard = Keyboard.activate_packet_menu(packet_id=packet.id)
        activated_date = datetime.strftime(packet.activated_at, '%d.%m.%Y')
        text = config.balance_inactive_packet_text % (str(balance), packet_name, activated_date, packet_ending)
        await call.message.edit_text(text=text, reply_markup=keyboard, parse_mode='html')
        return
    await call.answer()


async def get_packet_menu(call: CallbackQuery, session: AsyncSession):
    """Страница с выбором пакета для покупки"""
    packet_promotion = await PromoManager.get_packet_bonus(user_id=call.from_user.id,
                                                           session=session)
    pricelist = await PriceList.get_packets_price(session=session, packet_promotion=packet_promotion)
    await call.message.edit_text(config.packet_text,
                                 reply_markup=Keyboard.get_packets_keyboard(packets_list=pricelist),
                                 parse_mode='html')
    await call.answer()


async def activate_packet_handler(call: CallbackQuery, session: AsyncSession):
    """Активация пакета"""
    packet_id = int(call.data.replace('activate_packet_id=', ''))
    result = await PacketManager.activate_packet(packet_id=packet_id, session=session)
    if not result:
        await call.message.edit_text(text=config.error_activation_packet,
                                     reply_markup=Keyboard.support_keyboard(), parse_mode='html')
        return
    packet_name = result.get('name')
    packet_ending_date = result.get('ending_at')
    packet_ending_date = datetime.strftime(packet_ending_date, '%d.%m.%Y')
    text = config.success_activated_packet % (packet_name, packet_ending_date)
    await call.message.edit_text(text=text, reply_markup=Keyboard.create_auto(), parse_mode='html')
    await call.answer()


async def pause_packet_handler(call: CallbackQuery, session: AsyncSession):
    """Активация пакета"""
    packet_id = int(call.data.replace('pause_packet_id=', ''))
    activated_date = await PacketManager.pause_packet(packet_id=packet_id, session=session)
    keyboard = Keyboard.success_paused_menu(packet_id=packet_id)
    text = config.success_paused_packet % activated_date
    await call.message.edit_text(text=text, reply_markup=keyboard, parse_mode='html')
    await call.answer()


async def update_balance(call: CallbackQuery, state: FSMContext, logger):
    """Страница пополнения баланса"""
    await call.message.delete()

    deposit_bonus = DepositBonusManager(config=BonusConfig, bot=call.bot)
    if deposit_bonus:
        await deposit_bonus.send_offer(user_id=call.from_user.id)

    await call.message.answer(
        "<b>Напишите сумму пополнения числом </b> (Пример: 500)",
        reply_markup=Keyboard.cancel_menu(),
        parse_mode='html'
    )
    await state.set_state(TopUpBalance.amount)
    await call.answer()
    logger.info(f'Вошел в состояние TopUpBalance:amount',
                extra={'user_id': call.from_user.id,
                       'username': call.from_user.username,
                       'action': 'state_info'})


async def recomended_designer_callback(call: CallbackQuery, logger):
    await call.answer(
        text="🏅 Этот дизайнер - проверен администрацией и рекомендован к работе.",
        show_alert=True
    )
    logger.info(f'Открыл плашку рекомендации',
                extra={'user_id': call.from_user.id,
                       'username': call.from_user.username,
                       'action': 'post_conversion'})
    await call.answer()


async def get_lotery_prize(call: CallbackQuery, bot: Bot, session: AsyncSession, logger):
    await call.message.delete()
    await Lotery(config=BonusConfig).get_prize(user=call.from_user, session=session, bot=bot, logger=logger)


async def back_menu(call: CallbackQuery, session: AsyncSession):
    """Выход в главное меню"""
    menu_text = await get_menu_text(user_id=call.from_user.id, session=session)
    text = (menu_text % call.from_user.first_name)
    await call.message.edit_text(text, reply_markup=Keyboard.first_keyboard())
    await call.answer()


def create_callback_router():
    router = Router()
    router.callback_query.register(get_price, F.data == "price")
    router.callback_query.register(get_balance, F.data == "balance")
    router.callback_query.register(get_packet_menu, F.data.in_(["buy_packet", "buypacket"]))
    router.callback_query.register(activate_packet_handler, F.data.startswith("activate_packet_id"))
    router.callback_query.register(pause_packet_handler, F.data.startswith("pause_packet_id"))
    router.callback_query.register(update_balance, F.data.in_({'upbalance', 'upbalance_cas', 'upbalance_sber',
                                                               'upbalance_yoo', 'upbalance_lot'}))
    router.callback_query.register(get_lotery_prize, F.data == 'lotery_get_prize')
    router.callback_query.register(recomended_designer_callback, F.data == 'x')

    router.callback_query.register(back_menu, F.data == "back")

    return router