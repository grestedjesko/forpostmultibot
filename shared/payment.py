from configs import config
from aiogram import Bot
from database.models.payment_history import PaymentHistory
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
import uuid
import json
from yookassa import Configuration, Payment as YooPayment
from shared.pricelist import PriceList
from shared.user import BalanceManager
from shared.user_packet import PacketManager
from src.keyboards import Keyboard
from typing import Dict
import hashlib
import hmac
import httpx
from shared.notify_manager import NotifyManager
from shared.bonus.global_deposit_bonus import DepositBonusManager
from configs.bonus_config import BonusConfig
from microservices.funnel_actions import FunnelActions
from database.models.funnel_user_actions import FunnelUserActionsType
from shared.bonus.promo_manager import PromoManager
from database.models.promotion import PromotionType
from shared.bonus.bonus_giver import BonusGiver
from datetime import datetime, timedelta


class Payment:
    def __init__(self, user_id: int,
                 amount: int,
                 id: int | None = None,
                 packet_type: int | None = None,
                 discount_promo_id: int | None = None,
                 gate_payment_id: int | None = None,
                 status: str | None = None):
        self.user_id = user_id
        self.amount = amount
        self.id = id
        self.merchant_id = None
        self.api_key = None
        self.packet_type = packet_type
        self.discount_promo_id = discount_promo_id
        self.gate_payment_id = gate_payment_id
        self.status = status

    @classmethod
    async def from_db(cls, session: AsyncSession, id: int | None = None, gate_payment_id: int | None = None):
        if id:
            stmt = sa.select(PaymentHistory.id,
                             PaymentHistory.user_id,
                             PaymentHistory.amount,
                             PaymentHistory.packet_type,
                             PaymentHistory.discount_promo_id,
                             PaymentHistory.gate_payment_id,
                             PaymentHistory.status).where(PaymentHistory.id == id)
        else:
            stmt = sa.select(PaymentHistory.id,
                             PaymentHistory.user_id,
                             PaymentHistory.amount,
                             PaymentHistory.packet_type,
                             PaymentHistory.discount_promo_id,
                             PaymentHistory.gate_payment_id,
                             PaymentHistory.status).where(PaymentHistory.gate_payment_id == gate_payment_id)

        result = await session.execute(stmt)
        result = result.first()
        return cls(id=result.id,
                   user_id=result.user_id,
                   amount=result.amount,
                   packet_type=result.packet_type,
                   discount_promo_id=result.discount_promo_id,
                   gate_payment_id=result.gate_payment_id,
                   status=result.status)

    async def create(self, merchant_id: int, api_key: str, session: AsyncSession, packet_type: int = 1):
        self.merchant_id = merchant_id
        self.api_key = api_key

        """Создание платежа"""
        query = sa.insert(PaymentHistory).values(
            user_id=self.user_id,
            amount=self.amount,
            packet_type=packet_type,
            discount_promo_id=self.discount_promo_id,
            status='created'
        ).returning(PaymentHistory.id)
        result = await session.execute(query)
        await session.commit()
        self.id = result.scalar_one_or_none()
        try:
            gate_payment_id, payment_link = await self.create_tgpayment()
            payment_type = 'tgpayment'
        except Exception as e:
            print(e)
            gate_payment_id, payment_link = await self.create_yookassa()
            payment_type = 'yookassa'

        query = sa.update(PaymentHistory).values(gate_payment_id=gate_payment_id).where(PaymentHistory.id == self.id)
        await session.execute(query)
        await session.commit()

        return [payment_link, payment_type]

    async def create_tgpayment(self):
        # Заголовки запроса
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",  # Замените на ваш API-ключ
            "X-Merchant-ID": f"{self.merchant_id}",
        }

        # Тело запроса
        data = {
            "amount": self.amount,
            "description": f"Пополнение баланса",
            "meta": {"user_id": "123"},
        }

        url = 'https://pay.forpost.me/api/'

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers)

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

    async def accept(self, session: AsyncSession):
        """Подтверждение платежа"""
        stmt = sa.update(PaymentHistory).values(status='succeeded').where(PaymentHistory.id == self.id)
        await session.execute(stmt)
        await session.commit()

    async def process_payment(self, amount: float, bot: Bot, session: AsyncSession, declare_link: str | None = None):
        """Обрабатывает успешный платеж"""
        if self.status == 'succeeded':
            return

        user_id, message_id = await self.get_message_id(session=session)
        await self._safe_delete_message(bot, user_id, message_id)

        if self.packet_type == 1:
            await self._handle_balance_topup(amount, user_id, bot, session, declare_link)
        else:
            await self._handle_packet_purchase(amount, user_id, bot, session, declare_link)

        await self.accept(session=session)

    async def _safe_delete_message(self, bot: Bot, user_id: int, message_id: int):
        try:
            await bot.delete_message(chat_id=user_id, message_id=message_id)
        except Exception as e:
            print(e)

    async def _handle_balance_topup(self, amount: float, user_id: int, bot: Bot, session: AsyncSession,
                                    declare_link: str | None):
        await BalanceManager.deposit(amount=amount, user_id=user_id, session=session)

        message_text = f'Успешное пополнение на {amount}₽'
        bonus_text = await self._apply_deposit_bonus(amount, user_id, session)
        if bonus_text:
            message_text += f". {bonus_text}"

        if declare_link:
            message_text += f' Ваш <a href="{declare_link}">чек</a>'

        await bot.send_message(chat_id=user_id, text=message_text, parse_mode='html', disable_web_page_preview=True)

        global_deposit_bonus = DepositBonusManager(config=BonusConfig, bot=bot)
        await global_deposit_bonus.check_and_give_bonus(user_id=user_id, deposit_amount=amount, session=session)

        await bot.send_message(chat_id=user_id, text=config.main_menu_text, reply_markup=Keyboard.first_keyboard())

        await Payment.offer_connect_packet(user_id=user_id, bot=bot, session=session)

        await FunnelActions.save(user_id=user_id, action=FunnelUserActionsType.DEPOSITED, details=amount,
                                 session=session)

    async def _apply_deposit_bonus(self, amount: float, user_id: int, session: AsyncSession) -> str | None:
        deposit_bonus = await PromoManager.get_deposit_bonus(user_id=user_id, session=session)
        if not deposit_bonus:
            return None

        if deposit_bonus.type == PromotionType.BALANCE_TOPUP_PERCENT:
            bonus_amount = int(amount * (deposit_bonus.value / 100))
        elif deposit_bonus.type == PromotionType.BALANCE_TOPUP_FIXED:
            bonus_amount = int(deposit_bonus.value)
        else:
            return None

        await BonusGiver(giver=deposit_bonus.source).give_balance_bonus(user_id=user_id, amount=bonus_amount,
                                                                        session=session)
        await PromoManager.set_promo_used(user_promo_id=deposit_bonus.id, session=session)

        return f"Начислен бонус {bonus_amount}₽"

    async def _handle_packet_purchase(self, amount: float, user_id: int, bot: Bot, session: AsyncSession,
                                      declare_link: str | None):
        if amount < self.amount:
            print('Сумма меньше требуемой')
            return

        if self.discount_promo_id:
            promo = await PromoManager.get_bonus_by_id(bonus_id=self.discount_promo_id, session=session)
            if not (promo.is_active and promo.ending_at >= (datetime.now() - timedelta(hours=1))):
                print('Бонус уже использован')
                return
            await PromoManager.set_promo_used(user_promo_id=promo.id, session=session)

        assigned_packet = await PacketManager.assign_packet(user_id=user_id, packet_type=self.packet_type, price=amount,
                                                            session=session)
        await NotifyManager(bot=bot).send_packet_assigned(user_id=user_id, assigned_packet=assigned_packet)

        if declare_link:
            await bot.send_message(chat_id=user_id, text=f'Ваш <a href="{declare_link}">чек</a>', parse_mode='html',
                                   disable_web_page_preview=True)

        if not self.discount_promo_id:
            bonus_placements = await PromoManager.get_packet_placement_bonus(user_id=user_id, session=session)
            if bonus_placements:
                value = bonus_placements.value
                await BonusGiver.give_placement_bonus(user_id=user_id, placement_count=value, session=session)
                await bot.send_message(chat_id=user_id, text=f"Вам выдано {value} бонусных размещений")
                await PromoManager.set_promo_used(user_promo_id=bonus_placements.id, session=session)

        await FunnelActions.save(user_id=user_id, action=FunnelUserActionsType.PACKET_PURCHASED,
                                 details=self.packet_type, session=session)


    @staticmethod
    async def offer_connect_packet(user_id: int, bot: Bot, session: AsyncSession):
        balance = await BalanceManager.get_balance(user_id=user_id, session=session)
        packet_price = await PriceList.get_packet_price_by_id(session=session, packet_id=2)
        packet_price = packet_price.price
        if int(balance) >= int(packet_price):
            await bot.send_message(chat_id=user_id,
                                   text=config.offer_buy_packet,
                                   reply_markup=Keyboard.connect_packet_keyboard())


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
