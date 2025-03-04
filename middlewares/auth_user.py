from aiogram import types
from aiogram import BaseMiddleware
from shared.user import UserManager
from sqlalchemy.ext.asyncio import AsyncSession


class RegistrationMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def __call__(self, handler, event, data):
        session = data.get("session")

        if event.message:
            user = event.message.from_user
            registered = await self.process_registration(user=user, update=event.message, session=session)
            if registered:
                return
        elif event.callback_query:
            user = event.callback_query.from_user
            registered = await self.process_registration(user=user, update=event.callback_query, session=session)
            if registered:
                return
        return await handler(event, data)

    async def process_registration(self, user: types.User, session: AsyncSession,  update: types.Message | types.CallbackQuery):
        user_in_base = await UserManager.authenticate(user=user, session=session)
        if user_in_base:
            return False  # Пользователь уже зарегистрирован, продолжаем выполнение обработчиков

        await UserManager.register(user=user, session=session)

        await update.answer(
            "Добро пожаловать! Вы успешно зарегистрированы.\nЗдесь вы можете начать работу с нашим сервисом."
        )
        return True
