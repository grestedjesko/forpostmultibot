# main.py
from aiogram import Dispatcher
from aiogram.types import Update
from middlewares.database_middleware import DbSessionMiddleware
from middlewares.chat_middleware import ChatMiddleWare
from middlewares.callback_logging import CallbackLoggingMiddleware
from middlewares.auth_user import RegistrationMiddleware
from middlewares.album_middleware import AlbumMiddleware
from database.models import ForpostBotList
from middlewares.config_loader import ConfigLoaderMiddleware
from middlewares.get_logger_middleware import LoggerMiddleware
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from shared.payment import Payment, PaymentValidator
from database.base import async_session_factory
from aiogram import Bot
from shared.bot_config import BotConfig
from shared.logs.logging_config import setup_logging


from handlers import (message_handlers,
                      command_handlers,
                      callback_handlers,
                      admin_handlers,
                      deposit_handlers)
from handlers.post import post_handlers

app = FastAPI()
bots_pool = {}  # bot_id -> (Bot, Dispatcher)


async def load_bot_and_dispatcher(bot_id: int):
    async with async_session_factory() as session:
        bot_data = await session.get(ForpostBotList, bot_id)
        if not bot_data:
            raise HTTPException(status_code=404, detail="Bot not found")
        print(bot_data.token)
        bot = Bot(token=bot_data.token)
        dp = Dispatcher()

        # Подключение middleware с конфигами
        dp.update.middleware(DbSessionMiddleware())
        dp.update.middleware(ConfigLoaderMiddleware(bot_id=bot_id))
        dp.update.middleware(LoggerMiddleware())

        # Устанавливаем middleware
        #dp.update.middleware(GlobalErrorMiddleware())
        dp.message.middleware(ChatMiddleWare())
        dp.update.middleware(RegistrationMiddleware())
        dp.message.middleware(AlbumMiddleware())
        dp.callback_query.middleware(CallbackLoggingMiddleware())

        # Подключение роутеров
        dp.include_router(message_handlers.create_message_router())
        dp.include_router(command_handlers.create_command_router())
        dp.include_router(callback_handlers.create_callback_router())
        dp.include_router(deposit_handlers.create_deposit_router())
        dp.include_router(post_handlers.create_post_router())
        dp.include_router(admin_handlers.create_admin_router())

        bots_pool[bot_id] = (bot, dp)
        return bot, dp


@app.post("/webhook/{bot_id}")
async def webhook_handler(bot_id: int, request: Request):
    body = await request.body()
    update = Update.model_validate_json(body)
    if bot_id not in bots_pool:
        await load_bot_and_dispatcher(bot_id)
    bot, dp = bots_pool[bot_id]
    try:
        await dp.feed_update(bot, update)
    except Exception as e:
        print(e)
    return {"ok": True}


@app.post("/pay_webhook/{bot_id}")
async def receive_webhook(
    bot_id: int,
    request: Request,
    sign: str = Header(None)  # получаем заголовок "sign"
):
    async with async_session_factory() as session:
        session.info['bot_id'] = bot_id
        bot_token = await BotConfig.get_token_by_id(bot_id=bot_id, session=session)
        if not bot_token:
            return JSONResponse(status_code=500, content={"unknown"})
        bot_config = await BotConfig.load(bot_id=bot_id, session=session)

        try:
            data = await request.json()
            api_key = bytes(bot_config.pay_api_key, "utf-8")
            if not await PaymentValidator.is_valid_signature(api_key=api_key, data=data, received_signature=sign):
                raise HTTPException(status_code=403, detail="Forbidden")
            transaction_id = data.get("id")
            amount = data.get("amount")
            declare_link = data.get('declare_link', None)

            bot = Bot(bot_token)
            logger = setup_logging(bot=bot, chat_map=None, admin_id=bot_config.admin_ids[0])

            payment = await Payment.from_db(gate_payment_id=transaction_id, session=session, bot_config=bot_config)
            await Payment.process_payment(payment, float(amount), session=session, bot=bot, declare_link=declare_link, logger=logger)
            return {"status": "ok"}

        except Exception as e:
            print("Webhook error:", e)
            return JSONResponse(status_code=500, content={"error": str(e)})
