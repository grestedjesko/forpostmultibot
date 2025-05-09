import sqlalchemy as sa
from database.models import ForpostBotConfigs, ForpostBotList
from sqlalchemy.ext.asyncio import AsyncSession
from crypto.encrypt_token import decrypt_token

class BotConfig:
    def __init__(self, bot_id, admin_ids, chat_id, pay_api_key, pay_merchant_id, support_tag, chat_map):
        self.bot_id = bot_id
        self.admin_ids = list(map(int, admin_ids.replace('[', '').replace(']', '').split(',')))
        self.chat_id = chat_id
        self.pay_api_key = pay_api_key
        self.pay_merchant_id = pay_merchant_id
        self.support_tag = support_tag
        self.support_link = f't.me/{support_tag}'
        self.chat_map = chat_map

    @classmethod
    async def load(cls, bot_id: int, session: AsyncSession):
        stmt = sa.select(ForpostBotConfigs.config_name, ForpostBotConfigs.config_value).where(
            ForpostBotConfigs.bot_id == bot_id)
        result = await session.execute(stmt)
        configs = dict(result.fetchall())
        chat_map = {"default": configs.get('log_chat_default'),
                    "bonus": configs.get('log_chat_bonus'),
                    "deposit": configs.get('log_chat_deposit'),
                    "management": configs.get('log_chat_management'),
                    "registration": configs.get('log_chat_regs'),
                    "report": configs.get('log_chat_reports'),
                    "sale_conversions": configs.get('log_chat_sale_conv')
                    }
        return cls(bot_id=bot_id,
                   admin_ids=configs.get('admin_ids'),
                   chat_id=configs.get('chat_id'),
                   pay_api_key=configs.get('pay_api_key'),
                   pay_merchant_id=configs.get('pay_merchant_id'),
                   support_tag=configs.get('support_tag'),
                   chat_map=chat_map)

    @staticmethod
    async def get_token_by_id(bot_id: int, session: AsyncSession):
        query = await session.execute(sa.select(ForpostBotList.token).where(ForpostBotList.id == bot_id))
        result = query.scalar_one_or_none()
        if result:
            result = decrypt_token(result)
        return result