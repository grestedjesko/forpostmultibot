import config
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from shared.payment import Payment
from src.keyboards import Keyboard
from config import merchant_id, api_key
from shared.pricelist import PriceList
from src.states import TopUpBalance

router = Router()


@router.callback_query(F.data.startswith('buy_packet_id='))
async def select_packet(call: CallbackQuery, session: AsyncSession):
    """Выбор пакета для покупки"""
    packet_id = int(call.data.split('=')[1])
    title, amount = await PriceList().get_packet_price_by_id(packet_id=packet_id, session=session)

    payment = Payment(user_id=call.from_user.id, amount=amount)
    payment_url = await payment.create(packet_type=packet_id, merchant_id=merchant_id, api_key=api_key, session=session)

    text = config.payment_packet_text % (title, amount)
    payment_message = await call.message.edit_text(text=text, reply_markup=Keyboard.payment_keyboard(payment_url))

    await payment.save_message_id(message_id=payment_message.message_id, session=session)


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


@router.callback_query(F.data.contains("create_payment_balance"))
async def create_payment_balance(callback_query: CallbackQuery):
    """Создание платежной ссылки для пополнения баланса"""
    pass


@router.callback_query(F.data.contains("create_payment_packet"))
async def create_payment_packet(callback_query: CallbackQuery):
    """Создание платежной ссылки для покупки пакета"""
    pass


@router.message(TopUpBalance.amount)
async def process_amount(message: Message, session: AsyncSession, state: FSMContext):
    """Обрабатываем введенную сумму"""
    if not message.text.isdigit():
        await message.answer("Введите корректное число.")
        return

    amount = int(message.text)
    await state.clear()

    payment = Payment(user_id=message.from_user.id, amount=amount)
    payment_url = await payment.create(merchant_id=merchant_id, api_key=api_key, session=session)

    text = config.payment_text % amount
    payment_message = await message.answer(text=text, reply_markup=Keyboard.payment_keyboard(payment_url))

    await payment.save_message_id(message_id=payment_message.message_id, session=session)