from aiogram.types import PreCheckoutQuery
from aiogram.filters import Command
from aiogram import Router, F
from aiogram.types import Message, LabeledPrice
from sqlalchemy.ext.asyncio import AsyncSession
from shared.payment import Payment
from src.keyboards import Keyboard


router = Router()


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def success_payment_handler(message: Message):
    payment = message.successful_payment
    payment_amount = payment.total_amount
    payment_payload = payment.invoice_payload
    await message.answer(text="🥳Спасибо за вашу поддержку!🤗")


@router.message(Command("paysupport"))
async def pay_support_handler(message: Message):
    await message.answer('Возврат средства')


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
