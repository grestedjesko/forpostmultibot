from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
import config
from shared.payment import Payment, PaymentValidator
from database.base import async_session_factory
from aiogram import Bot
from config import BOT_TOKEN

app = FastAPI()
bot = Bot(token=BOT_TOKEN)

@app.post("/pay_webhook")
async def receive_webhook(
    request: Request,
    sign: str = Header(None)  # получаем заголовок "sign"
):
    try:
        data = await request.json()
        api_key = bytes(config.api_key, "utf-8")
        if not await PaymentValidator.is_valid_signature(api_key=api_key, data=data, received_signature=sign):
            raise HTTPException(status_code=403, detail="Forbidden")

        transaction_id = data.get("id")
        amount = data.get("amount")
        declare_link = data.get('declare_link', None)
        async with async_session_factory() as session:
            payment = await Payment.from_db(gate_payment_id=transaction_id, session=session)
            await Payment.process_payment(payment, float(amount), session=session, bot=bot, declare_link=declare_link)
        return {"status": "ok"}
    except Exception as e:
        print("Webhook error:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
