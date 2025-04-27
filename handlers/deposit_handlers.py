from configs import config
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from shared.payment import Payment
from src.keyboards import Keyboard
from configs.config import merchant_id, api_key
from shared.pricelist import PriceList
from src.states import TopUpBalance
import json
from yookassa import Configuration, Payment as YooPayment
from shared.user import BalanceManager
from shared.user_packet import PacketManager
from shared.notify_manager import NotifyManager
from microservices.funnel_actions import FunnelActions
from database.models.funnel_user_actions import FunnelUserActionsType
from shared.bonus.promo_manager import PromoManager
from aiogram.filters import StateFilter
from shared.bot_config import BotConfig


async def select_packet(call: CallbackQuery, session: AsyncSession, bot: Bot):
    """Выбор пакета для покупки"""
    packet_id = int(call.data.split('=')[1])

    packet_promotion = await PromoManager.get_packet_bonus(user_id=call.from_user.id,  session=session)
    packet_price = await PriceList.get_packet_price_by_id(packet_id=packet_id,
                                                          session=session,
                                                          packet_promotion=packet_promotion)

    balance = await BalanceManager().get_balance(user_id=call.from_user.id, session=session)
    if balance >= packet_price.price:
        await call.message.delete()
        await BalanceManager.deduct(user_id=call.from_user.id,
                                    amount=packet_price.price,
                                    session=session)

        if packet_promotion and packet_id in packet_promotion.packet_ids:
            await PromoManager.set_promo_used(user_promo_id=packet_promotion.id, session=session)
            await call.message.answer(f'Использована скидка {packet_promotion.value}% до {packet_promotion.ending_at}')

        assigned_packet = await PacketManager.assign_packet(user_id=call.from_user.id,
                                                            packet_type=packet_id,
                                                            price=packet_price.price,
                                                            session=session)
        await NotifyManager(bot=bot).send_packet_assigned(user_id=call.from_user.id,
                                                          assigned_packet=assigned_packet)

        await call.answer()
        return

    user_promotion_id = None
    if packet_promotion and packet_id in packet_promotion.packet_ids:
        user_promotion_id = packet_promotion.id
    payment = Payment(user_id=call.from_user.id, amount=packet_price.price, discount_promo_id=user_promotion_id)
    payment_url, payment_type = await payment.create(packet_type=packet_id,
                                                     merchant_id=merchant_id,
                                                     api_key=api_key,
                                                     session=session)
    if payment_type == "tgpayment":
        keyboard = Keyboard.payment_keyboard(link=payment_url)
    else:
        keyboard = Keyboard.payment_yookassa_keyboard(link=payment_url, payment_id=payment.id)

    text = config.payment_packet_text % (packet_price.name, packet_price.price)
    payment_message = await call.message.edit_text(text=text,
                                                   reply_markup=keyboard,
                                                   parse_mode='html')

    await payment.save_message_id(message_id=payment_message.message_id, session=session)
    await call.answer()

    await FunnelActions.save(user_id=call.from_user.id,
                             action=FunnelUserActionsType.INITIATED_PACKET_PURCHASE,
                             details=packet_id,
                             session=session)


async def process_amount(message: Message, session: AsyncSession, state: FSMContext, bot_config: BotConfig, logger):
    """Обрабатываем введенную сумму"""
    if not message.text.isdigit():
        await message.answer("Введите корректное число.")
        logger.info(f"Ввел некорректную сумму {message.text}", extra={"user_id": message.from_user.id,
                                                                      "username": message.from_user.username,
                                                                      "action": "amount_error"})
        return

    amount = int(message.text)
    await state.clear()
    msg = await message.answer(text='ㅤ', reply_markup=ReplyKeyboardRemove())

    payment = Payment(user_id=message.from_user.id, amount=amount, bot_config=bot_config)
    payment_url, payment_type = await payment.create(session=session)
    text = config.payment_text % amount

    await msg.delete()

    if payment_type == "tgpayment":
        keyboard = Keyboard.payment_keyboard(link=payment_url)
    else:
        keyboard = Keyboard.payment_yookassa_keyboard(link=payment_url, payment_id=payment.id)

    payment_message = await message.answer(text=text, reply_markup=keyboard, parse_mode='html')

    await payment.save_message_id(message_id=payment_message.message_id, session=session)

    logger.info(f"Создан платеж {payment_type}", extra={"user_id": message.from_user.id,
                                                        "username": message.from_user.username,
                                                        "action": "payment_created"})

    await FunnelActions.save(user_id=message.from_user.id,
                             action=FunnelUserActionsType.INITIATED_DEPOSIT,
                             details=payment_url,
                             session=session)


async def check_yookassa(call: CallbackQuery, session: AsyncSession, bot: Bot, logger):
    Configuration.account_id = config.yoo_account_id
    Configuration.secret_key = config.yoo_account_key

    payment_id = int(call.data.split('=')[1])

    payment = await Payment.from_db(id=payment_id, session=session)
    gate_payment_id = payment.gate_payment_id

    payment_json = json.loads((YooPayment.find_one(gate_payment_id)).json())
    amount = float(payment_json.get('amount').get('value'))

    if payment_json.get('status') == 'succeeded':
        await payment.check_yookassa(amount=amount,
                                     bot=bot,
                                     session=session,
                                     logger=logger)
    await call.answer()


def create_deposit_router():
    router = Router()
    router.callback_query.register(select_packet, F.data.startswith('buy_packet_id='))
    router.message.register(process_amount, StateFilter(TopUpBalance.amount))
    router.callback_query.register(check_yookassa, F.data.split('=')[0] == 'check_yookassa_id')
    return router