from database.models.payment_history import PaymentHistory
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
import requests


class Payment:
    def __init__(self, user_id: int, amount: int, id: int | None = None, packet_type: int | None = None):
        self.user_id = user_id
        self.amount = amount
        self.id = id
        self.merchant_id = None
        self.api_key = None
        self.packet_type = packet_type

    @classmethod
    async def from_db(cls, gate_payment_id: int, session: AsyncSession):
        stmt = sa.select(PaymentHistory.id, PaymentHistory.user_id, PaymentHistory.amount, PaymentHistory.packet_type).where(PaymentHistory.gate_payment_id == gate_payment_id)
        result = await session.execute(stmt)
        result = result.first()
        return cls(id=result.id, user_id=result.user_id, amount=result.amount, packet_type=result.packet_type)

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

        gate_payment_id, payment_link = await self.create_tgpayment()
        query = sa.update(PaymentHistory).values(gate_payment_id=gate_payment_id).where(PaymentHistory.id == self.id)
        await session.execute(query)
        await session.commit()

        return payment_link

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
            print("Успешный ответ:")
            payment_id = response.json().get('payment_id')
            print('получен id из transactions')
            print(payment_id)
            payment_link = response.json().get('payment_link')
        else:
            print(f"Ошибка: {response.status_code}")
            print(response.json())

        return (payment_id, payment_link)

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

    async def check(self):
        """Проверка платежа"""


class Invoice:
    def __init__(self, payment):
        pass

    async def create_invoice(self):
        """Создание чека"""
        pass
