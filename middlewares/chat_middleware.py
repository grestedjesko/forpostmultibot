from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery
from typing import Callable, Awaitable, Dict, Any
from configs import config
from aiogram import types, Bot


class ChatMiddleWare(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        chat_id = event.chat.id
        if chat_id == config.chat_id:
            if event.message:
                message = event.message
            else:
                return

            await message.delete()
            await message.answer(config.chat_text)
            user = message.from_user
            bot = data.get('bot')
            await bot.restrict_chat_member(chat_id=message.chat.id,
                                           user_id=message.from_user.id,
                                           permissions=types.ChatPermissions(False))

            logger = data.get("user_logger")  # ✅ достаём логгер из data
            if logger:
                logger.info("Отправил запрещенное сообщение в чате",
                            extra={'user_id': message.from_user.id,
                                   'username': message.from_user.username,
                                   'action': 'chat_message_sended'})
        return await handler(event, data)



