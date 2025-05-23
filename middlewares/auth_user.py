from aiogram import types
from aiogram import BaseMiddleware

from configs import config
from shared.user import UserManager
from sqlalchemy.ext.asyncio import AsyncSession
from src.keyboards import Keyboard
from shared.funnel_actions import FunnelActions
from database.models.funnel_user_actions import FunnelUserActionsType
from shared.bot_config import BotConfig


class RegistrationMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def __call__(self, handler, event, data):
        session = data.get("session")
        logger = data.get("logger")
        bot_config = data.get("bot_config")
        if event.message:
            if str(event.message.chat.id)[0] == '-':
                return
            user = event.message.from_user
            registered = await self.process_registration(user=user, update=event.message, session=session, bot_config=bot_config, logger=logger)
            if registered:
                return
        elif event.callback_query:
            user = event.callback_query.from_user
            registered = await self.process_registration(user=user, update=event.callback_query, session=session, bot_config=bot_config, logger=logger)
            if registered:
                return
        return await handler(event, data)

    async def process_registration(self, user: types.User, session: AsyncSession,  update: types.Message | types.CallbackQuery, bot_config: BotConfig, logger):
        user_in_base = await UserManager.authenticate(user=user, session=session)
        if user_in_base:
            return False  # Пользователь уже зарегистрирован, продолжаем выполнение обработчиков

        await UserManager.register(user=user, session=session)

        await update.answer(
            config.onboarding_text, parse_mode="html", reply_markup=Keyboard.first_keyboard(support_link=bot_config.support_link)
        )
        if logger:
            logger.info(
                "Новый пользователь",
                extra={"user_id": user.id, "username": user.username, "action": "registration"}
            )
        await FunnelActions.save(user_id=user.id, action=FunnelUserActionsType.REGISTERED, session=session)
        return True