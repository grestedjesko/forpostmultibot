from aiogram import Router, F, Bot
from aiogram.types import PreCheckoutQuery
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

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