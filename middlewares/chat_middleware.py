from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery
from typing import Callable, Awaitable, Dict, Any
from configs import config
from aiogram import types, Bot
from aiogram.types import Message


class ChatMiddleWare(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
            message: Message,
            data: dict[str, Any]
    ) -> Any:
        chat_id = message.chat.id
        print(chat_id)
        if chat_id == config.chat_id:
            await message.delete()
            await message.answer(config.chat_text)
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
        if chat_id < 0 or str(chat_id)[-1] == '-':
            return
        return await handler(message, data)



