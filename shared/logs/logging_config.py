import logging
from shared.logs.telegram_log_handler import TelegramLogHandler
from aiogram import Bot


def setup_logging(bot: Bot, chat_map: dict[str, int]):
    # Логгер
    logger = logging.getLogger("user_actions")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    # 📄 Файловый хендлер
    file_handler = logging.FileHandler(f"forpost_{bot.id}.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | USER_ID=%(user_id)s | USERNAME=%(username)s | ACTION=%(action)s | %(message)s"
    ))
    logger.addHandler(file_handler)

    # 📩 Telegram хендлер
    tg_handler = TelegramLogHandler(bot, chat_map)
    logger.addHandler(tg_handler)

    return logger