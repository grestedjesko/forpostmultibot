import logging
import asyncio
from aiogram import Bot

class TelegramLogHandler(logging.Handler):
    def __init__(self, bot: Bot, chat_map: dict[str, int]):
        super().__init__()
        self.bot = bot
        self.chat_map = chat_map  # {'registration': chat_id, 'payment': chat_id, ...}

    def emit(self, record: logging.LogRecord):
        try:
            action = getattr(record, "action", None)
            user_id = getattr(record, "user_id", "Unknown")
            username = getattr(record, "username", "—")
            message = record.getMessage()

            chat_id = self.chat_map.get(action)
            if not chat_id:
                return

            # Форматируем сообщение для Telegram
            tg_text = f"👤 <b>{username}</b> (ID: <code>{user_id}</code>)\n📝 {message}"

            asyncio.create_task(self.bot.send_message(
                chat_id=chat_id,
                text=tg_text[:4000],
                parse_mode="HTML"
            ))

        except Exception:
            self.handleError(record)
