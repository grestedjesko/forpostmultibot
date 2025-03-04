from quart import Quart, request, jsonify
import json
import config
import hmac
import hashlib
from shared.payment import Payment
from shared.user import BalanceManager, PacketManager
from database.base import async_session_factory
from aiogram import Bot
from config import BOT_TOKEN
from src.keyboards import Keyboard

app = Quart(__name__)
bot = Bot(token=BOT_TOKEN)

@app.route('/pay_webhook', methods=['POST'])
async def receive_webhook():
    data = await request.get_json()
    received_signature = request.headers.get("sign")

    api_key = bytes(config.api_key, 'utf-8')

    expected_signature = generate_signature(api_key=api_key, data=data)
    if not hmac.compare_digest(received_signature, expected_signature):
        return jsonify('Forbidden'), 403

    id = data.get('payment_id')
    amount = data.get('amount').get('value')

    async with async_session_factory() as session:
        payment = await Payment.from_db(gate_payment_id=id, session=session)

    if data.get('paid') is True:
        user_id, message_id = await payment.get_message_id(session=session)
        await bot.delete_message(chat_id=user_id, message_id=message_id)
        if payment.packet_type == 1:
            await BalanceManager.deposit(amount=float(amount), user_id=user_id, session=session)
            await bot.send_message(chat_id=user_id, text=f'Успешно пополнено на {amount} рублей.')
        else:
            result = await PacketManager.assign_packet(user_id=user_id, packet_type=payment.packet_type, price=amount, session=session)
            txt = ''
            if result == 'Пакет продлен':
                txt = 'Пакет успешно продлен'
            else:
                txt = 'Пакет успешно выдан'
            await bot.send_message(chat_id=user_id, text=txt)

        await bot.send_message(chat_id=user_id, text='Главное меню', reply_markup=Keyboard.first_keyboard())

    return jsonify('ok'), 200

def generate_signature(api_key: bytes, data: dict) -> str:
    data = json.dumps(data, sort_keys=True)
    return hmac.new(api_key, data.encode(), hashlib.sha256).hexdigest()

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Указываем порт, например, 5001