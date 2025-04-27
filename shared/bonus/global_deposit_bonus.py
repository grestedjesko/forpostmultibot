from configs.bonus_config import BonusConfig
from aiogram import  Bot
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from shared.bonus.lotery import Lotery
from database.models import UserLoteryBillets
from shared.bonus.bonus_giver import BonusGiver
from shared.bonus.lotery import Lotery
from src.keyboards import Keyboard


class DepositBonusManager:
    def __init__(self, config, bot):
        self.config = config
        self.bot = bot

    @classmethod
    def create(cls, config: BonusConfig, bot: Bot):
        if config.active:
            return cls(config=config, bot=bot)
        return None

    async def send_offer(self, user_id: int):
        try:
            if self.config.bonus_image:
                await self.bot.send_photo(chat_id=user_id, photo=self.config.bonus_image, caption=self.config.bonus_text, parse_mode='html')
            else:
                await self.bot.send_message(chat_id=user_id, text=self.config.bonus_text, parse_mode='html')
        except Exception as e:
            print(e)

    async def check_and_give_bonus(self, user_id: int, deposit_amount: int, session: AsyncSession):
        if deposit_amount < self.config.minimal_sum:
            return

        count = (deposit_amount // self.config.minimal_sum)
        if self.config.max_count != 0:
            if count >= self.config.max_count:
                count = self.config.max_count
        if self.config.bonus_type == "lotery":
            billets = count * self.config.bonus_sum
            await self._apply_bonus(user_id=user_id, bonus_type="lotery", value=billets, session=session)
        elif self.config.bonus_type == "deposit":
            bonus_amount = count * self.config.bonus_sum
            await self._apply_bonus(user_id=user_id, bonus_type="balance", value=bonus_amount, session=session)

    async def _apply_bonus(self, user_id: int, bonus_type: str, value: int, session: AsyncSession):
        if bonus_type == "balance":
            await BonusGiver(giver='bonus').give_balance_bonus(user_id=user_id, amount=value, session=session)
            message = f"🎁 Вам начислено {value}₽ бонуса на баланс!"
            await self.bot.send_message(user_id, message)
        elif bonus_type == "lotery":
            await Lotery.give_billets(user_id=user_id, count=value, session=session)
            message = f"🎟 Вам начислено {value} лотерейных билетов! Чтобы получить приз, нажмите кнопку ниже"
            await self.bot.send_message(user_id, message, reply_markup=Keyboard.lotery_get_prize())
