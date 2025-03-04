import config
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, LabeledPrice
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from shared.payment import Payment
from src.keyboards import Keyboard
from config import merchant_id, api_key
from shared.pricelist import PriceList
from src.states import TopUpBalance
from aiogram.types import PreCheckoutQuery


router = Router()


@router.callback_query(F.data.startswith('buy_packet_id='))
async def select_packet(call: CallbackQuery, session: AsyncSession):
    """Выбор пакета для покупки"""
    packet_id = int(call.data.split('=')[1])
    title, amount = await PriceList().get_packet_price_by_id(packet_id=packet_id, session=session)

    payment = Payment(user_id=call.from_user.id, amount=amount)
    payment_url = await payment.create(packet_type=packet_id, merchant_id=merchant_id, api_key=api_key, session=session)

    text = config.payment_packet_text % (title, amount)
    payment_message = await call.message.edit_text(text=text, reply_markup=Keyboard.payment_keyboard(payment_url, payment_id=payment.id))

    await payment.save_message_id(message_id=payment_message.message_id, session=session)


async def pay_stars(payment_id: int, message: Message, session: AsyncSession):
    print(payment_id)
    payment = await Payment.from_db(id=payment_id, session=session)
    c = float(1.25)
    stars_amount = int(float(payment.amount) * c)

    prices = [LabeledPrice(label="Пополнение", amount=stars_amount)]
    await message.answer_invoice(
        title="Пополнение баланса",
        description=f"Пополнить баланс на {payment.amount}₽",
        prices=prices,
        provider_token="",
        payload=f"balance_up_{payment_id}",
        currency="XTR",
        reply_markup=Keyboard.stars_payment_keyboard(),
    )


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
    payment_message = await message.answer(text=text, reply_markup=Keyboard.payment_keyboard(payment_url, payment.id))

    await payment.save_message_id(message_id=payment_message.message_id, session=session)


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def success_payment_handler(message: Message):
    payment = message.successful_payment
    payment_amount = payment.total_amount
    payment_payload = payment.invoice_payload
    print(payment_payload)
    await message.answer(text="🥳Спасибо за вашу поддержку!🤗")


@router.message(Command("paysupport"))
async def pay_support_handler(message: Message):
    await message.answer('Возврат средства')