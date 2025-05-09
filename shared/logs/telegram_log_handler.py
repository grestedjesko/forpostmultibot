import logging
import asyncio
from aiogram import Bot


class TelegramLogHandler(logging.Handler):
    def __init__(self, bot: Bot, chat_map: dict[str, int]):
        super().__init__()
        self.bot = bot
        self.chat_map = chat_map

    def emit(self, record: logging.LogRecord):
        try:
            action = getattr(record, "action", None)
            user_id = getattr(record, "user_id", "Unknown")
            username = getattr(record, "username", "—")
            message = record.getMessage()

            if not self.chat_map:
                return

            chat_id = self.chat_map.get(action)
            if not chat_id:
                return

            thread_id = None
            if ':' in chat_id:
                r = str(chat_id).split(':', 2)[0]
                chat_id, thread_id = r[0], r[1]

            # Форматируем сообщение для Telegram
            tg_text = f"{message}\n<b>{username}</b>(<code>{user_id}</code>)"

            if thread_id:
                asyncio.create_task(self.bot.send_message(
                    chat_id=chat_id,
                    message_thread_id=thread_id,
                    text=tg_text[:4000],
                    parse_mode="HTML"
                ))
            else:
                asyncio.create_task(self.bot.send_message(
                    chat_id=chat_id,
                    text=tg_text[:4000],
                    parse_mode="HTML"
                ))

        except Exception:
            self.handleError(record)
