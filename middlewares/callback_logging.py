from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery
from typing import Callable, Awaitable, Dict, Any

class CallbackLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        user_id = user.id
        username = user.username or user.full_name
        callback_data = event.data

        logger = data.get("logger")
        if logger:
            logger.info(
                f"Нажал на кнопку: {callback_data}",
                extra={"user_id": user_id, "username": username, "action": "callback"}
            )
        return await handler(event, data)
