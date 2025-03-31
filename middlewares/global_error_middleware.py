from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Awaitable, Dict, Any
import logging
import traceback

class GlobalErrorMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except Exception as e:
            user = getattr(event, "from_user", None)
            user_id = user.id if user else "Unknown"
            username = user.username if user else "Unknown"

            logger = data.get("user_logger")  # ✅ достаём логгер из data
            if logger:
                logger.exception(
                    f"Ошибка {type(e).__name__}: {e}",
                    extra={"user_id": user_id, "username": username, "action": "error"}
                )

            return None
