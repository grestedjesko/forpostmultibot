from quart import Quart, request, jsonify
import config
from shared.payment import Payment, PaymentValidator
from database.base import async_session_factory
from aiogram import Bot
from config import BOT_TOKEN

app = Quart(__name__)
bot = Bot(token=BOT_TOKEN)

@app.route('/pay_webhook', methods=['POST'])
async def receive_webhook():
    data = await request.get_json()
    received_signature = request.headers.get("sign")
    api_key = bytes(config.api_key, 'utf-8')

    if not (await PaymentValidator.is_valid_signature(api_key=api_key, data=data, received_signature=received_signature)):
        return jsonify('Forbidden'), 403

    payment_id = data.get('payment_id')
    amount = data.get('amount').get('value')

    async with async_session_factory() as session:
        payment = await Payment.from_db(gate_payment_id=payment_id, session=session)

        await Payment.process_payment(payment, float(amount), session=session, bot=bot)

    return jsonify('ok'), 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Указываем порт, например, 5001