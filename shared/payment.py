import config
from aiogram import Bot
from database.models.payment_history import PaymentHistory
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
import requests
import uuid
import json
from yookassa import Configuration, Payment as YooPayment

from shared.pricelist import PriceList
from shared.user import BalanceManager, PacketManager
from src.keyboards import Keyboard
from datetime import datetime
from typing import Dict
import hashlib
import hmac


class Payment:
    def __init__(self, user_id: int, amount: int, id: int | None = None, packet_type: int | None = None, gate_payment_id: int | None = None):
        self.user_id = user_id
        self.amount = amount
        self.id = id
        self.merchant_id = None
        self.api_key = None
        self.packet_type = packet_type
        self.gate_payment_id = gate_payment_id

    @classmethod
    async def from_db(cls, session: AsyncSession, id: int | None = None, gate_payment_id: int | None = None):
        if id:
            stmt = sa.select(PaymentHistory.id, PaymentHistory.user_id, PaymentHistory.amount, PaymentHistory.packet_type, PaymentHistory.gate_payment_id).where(PaymentHistory.id==id)
        else:
            stmt = sa.select(PaymentHistory.id, PaymentHistory.user_id, PaymentHistory.amount, PaymentHistory.packet_type, PaymentHistory.gate_payment_id).where(PaymentHistory.gate_payment_id == gate_payment_id)

        result = await session.execute(stmt)
        result = result.first()
        return cls(id=result.id,
                   user_id=result.user_id,
                   amount=result.amount,
                   packet_type=result.packet_type,
                   gate_payment_id=result.gate_payment_id)

    async def create(self, merchant_id: int, api_key: str, session: AsyncSession, packet_type: int = 1):
        self.merchant_id = merchant_id
        self.api_key = api_key

        """Создание платежа"""
        query = sa.insert(PaymentHistory).values(
            user_id=self.user_id,
            amount=self.amount,
            packet_type=packet_type,
            status='created'
        ).returning(PaymentHistory.id)
        result = await session.execute(query)
        await session.commit()
        self.id = result.scalar_one_or_none()

        try:
            gate_payment_id, payment_link = await self.create_tgpayment()
            type = 'tgpayment'
        except Exception as e:
            gate_payment_id, payment_link = await self.create_yookassa()
            type = 'yookassa'

        query = sa.update(PaymentHistory).values(gate_payment_id=gate_payment_id).where(PaymentHistory.id == self.id)
        await session.execute(query)
        await session.commit()

        return [payment_link, type]

    async def create_tgpayment(self):
        # Заголовки запроса
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"  # Замените на ваш API-ключ
        }

        # Тело запроса
        data = {
            "merchant_id": str(self.merchant_id),  # Замените на ваш merchant_id
            "amount": self.amount
        }

        url = 'http://127.0.0.1:5000/payapi'
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            payment_id = response.json().get('payment_id')
            payment_link = response.json().get('payment_link')
            return [payment_id, payment_link]
        raise ValueError

    async def create_yookassa(self):
        Configuration.account_id = config.yoo_account_id
        Configuration.secret_key = config.yoo_account_key

        amount = self.amount*1.05
        payment = YooPayment.create({
            "amount": {"value": f"{amount}", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": config.bot_url},
            "capture": True, "description": f"Покупка пакета размещений"}, uuid.uuid4())

        payment_data = json.loads(payment.json())
        payment_id = payment_data['id']
        payment_link = (payment_data['confirmation'])['confirmation_url']

        return [payment_id, payment_link]

    async def check_yookassa(self, amount: float, bot: Bot, session: AsyncSession):
        """Проверка платежа"""
        amount = int(amount * 0.9525)
        await self.process_payment(amount=amount, bot=bot, session=session)

    async def save_message_id(self, message_id: int, session: AsyncSession):
        stmt = sa.update(PaymentHistory).values(payment_message_id=message_id).where(PaymentHistory.id == self.id)
        await session.execute(stmt)
        await session.commit()

    async def get_message_id(self, session: AsyncSession):
        stmt = sa.select(PaymentHistory.user_id, PaymentHistory.payment_message_id).where(PaymentHistory.id == self.id)
        r = await session.execute(stmt)
        return r.first()

    async def accept(self):
        """Подтверждение платежа"""

    async def process_payment(self, amount: float, bot: Bot, session: AsyncSession):
        """Обрабатывает успешный платеж"""
        user_id, message_id = await self.get_message_id(session=session)

        # Удаляем сообщение о неоплаченном платеже
        await bot.delete_message(chat_id=user_id, message_id=message_id)

        if self.packet_type == 1:
            # Пополнение баланса
            await BalanceManager.deposit(amount=float(amount), user_id=user_id, session=session)
            await bot.send_message(chat_id=user_id, text=f'Успешно пополнено на {amount} рублей.')
            await self.offer_connect_packet(user_id=user_id,
                                            bot=bot,
                                            session=session)
        else:
            if amount < self.amount:
                print('Сумма меньше требуемой')
                return

            # Выдача пакета
            result = await PacketManager.assign_packet(
                user_id=user_id,
                packet_type=self.packet_type,
                price=amount,
                session=session,
                bot=bot
            )

    async def offer_connect_packet(self, user_id: int, bot: Bot, session: AsyncSession):
        balance = await BalanceManager.get_balance(user_id=user_id, session=session)
        packet_price = await PriceList.get_packet_price_by_id(session=session, packet_id=2)
        packet_price = packet_price[1]
        if int(balance) >= int(packet_price):
            await bot.send_message(chat_id=user_id, text=config.offer_buy_packet, reply_markup=Keyboard.connect_packet_keyboard())


class PaymentValidator:
    """Класс для валидации платежа"""

    @staticmethod
    async def is_valid_signature(api_key: bytes, data: Dict, received_signature: str) -> bool:
        """Проверяет подпись платежа"""
        expected_signature = await PaymentValidator.generate_signature(api_key=api_key, data=data)
        return hmac.compare_digest(received_signature, expected_signature)

    @staticmethod
    async def generate_signature(api_key: bytes, data: dict) -> str:
        data = json.dumps(data, sort_keys=True)
        return hmac.new(api_key, data.encode(), hashlib.sha256).hexdigest()


class Invoice:
    def __init__(self, payment):
        pass

    async def create_invoice(self):
        """Создание чека"""
        pass
