from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.filters import Command
from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession
from shared.admin import AdminManager
from shared.user import BalanceManager
from shared.user_packet import PacketManager
from shared.bonus.bonus_giver import BonusGiver
from datetime import datetime
from configs import config
from src.keyboards import Keyboard
import requests
from shared.notify_manager import NotifyManager
import os

admin_router = Router()


@admin_router.message(Command('getuser'))
async def admin_get_user(message: types.Message, session: AsyncSession, logger):
    if not message.from_user.id in config.admin_ids:
        return

    user_id = message.text.replace('/getuser ', '')
    if not user_id:
        await message.answer("Вы не ввели user_id")
        return

    if user_id.isdigit():
        user_data = await AdminManager.get_user_info(user_id=user_id, session=session)
    else:
        user_data = await AdminManager.get_user_info(username=user_id, session=session)

    if not user_data:
        await message.answer("Пользователь не найден")
        return

    user_id = user_data[0]
    first_name = user_data[1]
    username = user_data[2]
    balance = user_data[3]
    upbal_sum = user_data[4]
    posted_count = user_data[5]

    text = f"""👤 UserID: {user_id}

Имя: {first_name}
Ссылка: @{username} 

Баланс: {balance}"""

    packet = await PacketManager.get_user_packet(user_id=user_id, session=session)
    if packet:
        packet, packet_name = packet[0], packet[1]

        if packet.activated_at < datetime.now():
            packet_status = '✅ Пакет активен'
        else:
            packet_status = '✖️ Пакет не активирован'

        packet_text = f"""🛍 <b>Пакет: {packet_name}</b>
Статус: {packet_status}
Дата активации: {datetime.strftime(packet.activated_at, '%d.%m.%Y %H:%M')}
Заканчивается: {datetime.strftime(packet.ending_at, '%d.%m.%Y')}
Куплен за: {packet.price}

📝<b>Лимиты</b>
Постов сегодня: {packet.today_posts}
Постов использовано: {packet.used_posts}
Осталось постов: {packet.all_posts}"""

        text += '\n'*2
        text += packet_text

    text+= '\n'*2

    text += f"""📊<b>Статистика</b>
Пополнено на: {upbal_sum}
Получено бонуса: 0.0
Размещено обьявлений: {posted_count}"""


    await message.answer(text, parse_mode='html')

    logger.info(f"Запрошена информация о пользователе {user_id}", extra={"user_id": message.from_user.id,
                                                                         "username": message.from_user.username,
                                                                         "action": "admin_getuser"})


@admin_router.message(Command('sendid'))
async def admin_send_message_to_user(message: types.Message, bot: Bot, logger):
    if not message.from_user.id in config.admin_ids:
        return

    res = message.text.replace('/sendid ', '')
    res = res.split(' ', 1)
    user_id = res[0]
    text = res[1]

    if not user_id:
        await message.answer("Вы не ввели user_id")
        return

    if message.from_user.username:
        admin_link = f'https://t.me/{message.from_user.username}'
    else:
        admin_link = f"tg://user?id={message.from_user.id}"
    try:
        msg = await bot.send_message(chat_id=user_id, text=text, reply_markup=Keyboard.admin_keyboard(admin_link=admin_link))
    except:
        await message.answer(text=f'Ошибка отправки {user_id}')
        return
    await message.answer(text=f"Сообщение {user_id} отправлено", reply_markup=Keyboard.delete_message_keyboard(chat_id=int(user_id), message_id=msg.message_id))

    logger.info(f"Отправил пользователю {user_id} сообщение с текстом «{text}»",
                extra={"user_id": message.from_user.id,
                       "username": message.from_user.username,
                       "action": "admin_sendid"})


@admin_router.callback_query(F.data.contains('admin_delete_direct_chat'))
async def admin_delete_direct_chat(call: CallbackQuery, bot: Bot, logger):
    res = call.data.replace('admin_delete_direct_chat=', '')
    chat_id, message_id = res.split('+message=', 2)

    try:
        await bot.delete_message(chat_id=chat_id, message_id=int(message_id))

        await call.message.edit_text(f'Сообщение {chat_id} {message_id} удалено')

        logger.info(f"Удалил сообщение для {chat_id} n {message_id}",
                    extra={"user_id": call.from_user.id,
                           "username": call.from_user.username,
                           "action": "admin_sendid_delete"})

    except Exception as e:
        logger.info(f"Ошибка удаления сообщения админа: {e}",
                    extra={"user_id": call.from_user.id,
                           "username": call.from_user.username,
                           "action": "error"})


@admin_router.message(Command('upbal'))
async def admin_topup_user_balance(message: types.Message, session: AsyncSession, logger):
    res = message.text.replace('/upbal ', '')
    bonus = False
    if 'bonus' in res:
        bonus = True
        res = res.replace('bonus', '')

    if not res:
        await message.answer('user_id amount')
        return

    res = res.split(' ', 1)
    user_id, amount = int(res[0]), int(res[1])

    try:
        if bonus:
            await BonusGiver(giver='admin').give_balance_bonus(user_id=user_id, amount=amount, session=session)
        else:
            await BalanceManager.deposit(amount=amount,
                                         user_id=user_id,
                                         session=session)
            await AdminManager.save_payment(user_id=user_id, amount=amount, packet_type=1, session=session)

        balance = await BalanceManager.get_balance(user_id=user_id, session=session)
        await message.answer(f"Баланс {user_id} пополнен на {amount}₽. Текущий баланс {balance}₽")
        await message.bot.send_message(chat_id=user_id, text=f'💰 Ваш баланс пополнен на {amount}₽')

        logger.info(f"Пополнил баланс {user_id} на {amount}",
                    extra={"user_id": message.from_user.id,
                           "username": message.from_user.username,
                           "action": "admin_upbal"})
    except Exception as e:
        logger.info(f"Ошибка пополнения баланса админом {e}",
                    extra={"user_id": message.from_user.id,
                           "username": message.from_user.username,
                           "action": "error"})


@admin_router.message(Command('givepacket'))
async def admin_give_user_packet(message: types.Message, session: AsyncSession, bot: Bot, logger):
    res = message.text.replace('/givepacket ', '')
    if not res:
        await message.answer('user_id packet_id price')
        return

    bonus = False
    if 'bonus' in res:
        bonus = True
        res = res.replace('bonus', '')

    res = res.split(' ', 2)
    user_id, packet_id, price = int(res[0]), int(res[1]), int(res[2])

    try:
        if bonus:
            await BonusGiver(giver='bonus').give_packet_bonus(user_id=user_id, packet_id=packet_id, session=session)
        else:
            assigned_packet = await PacketManager.assign_packet(user_id=user_id,
                                                                packet_type=packet_id,
                                                                price=price,
                                                                session=session)

            await AdminManager.save_payment(user_id=user_id, amount=price, packet_type=packet_id, session=session)

        await NotifyManager(bot=bot).send_packet_assigned(user_id=user_id, assigned_packet=assigned_packet)

        await message.answer(f"Пакет {packet_id} успешно выдан {user_id}")

        logger.info(f"Выдал пакет id={packet_id} -> {user_id}",
                    extra={"user_id": message.from_user.id,
                           "username": message.from_user.username,
                           "action": "admin_givepacket"})

    except Exception as e:
        print(e)
        await message.answer(f"Ошибка выдачи пакета")
        logger.info(f"Ошибка выдачи пакета id={packet_id} -> {user_id}: {e}",
                    extra={"user_id": message.from_user.id,
                           "username": message.from_user.username,
                           "action": "error"})


@admin_router.message(Command('addpacket'))
async def admin_add_packet_days(message: types.Message, session: AsyncSession, bot: Bot, logger):
    res = message.text.replace('/addpacket ', '')
    res = res.split(' ', 1)
    if not res:
        await message.answer('user_id post_count')
        return
    user_id, additional_posts = list(map(int, res))
    try:
        user_packet = await PacketManager.get_user_packet(user_id=int(user_id), session=session)
        user_packet, limit_per_day = user_packet[0], user_packet[2]
        await PacketManager.extend_packet(user_packet=user_packet, additional_posts=additional_posts, new_limit_per_day=limit_per_day)
        await session.commit()
        ending_date = datetime.strftime(user_packet.ending_at, '%d.%m.%Y')
        await message.answer(f"Пакет {user_id} продлен до {ending_date}")
        await bot.send_message(user_id, f"Ваш пакет продлен до {ending_date}")
        logger.info(f"Продлил пакет на {additional_posts} до {ending_date} -> {user_id}",
                    extra={"user_id": message.from_user.id,
                           "username": message.from_user.username,
                           "action": "admin_givepacket"})

    except Exception as e:
        logger.info(f"Ошибка продления пакета на {additional_posts}шт -> {user_id}: {e}",
                    extra={"user_id": message.from_user.id,
                           "username": message.from_user.username,
                           "action": "error"})
        await message.answer(f"Ошибка продления пакета")


@admin_router.message(Command('poststats'))
async def admin_get_post_stats(message: types.Message, session: AsyncSession, bot:Bot, logger):
    post = message.text.replace('/poststats ', '')
    if post.isdigit():
        post_id = int(post)
        result = await get_post_stats(post_id=post_id)
    else:
        result = await get_post_stats(short_link=post)

    result = result[0]
    text = f"""Post_id: {result.get('post_id')}
Short_link: {result.get('short_link')}
Original_url: {result.get('original_url')}

Посещений: {result.get('visits')}"""

    await message.answer(text, disable_web_page_preview=True)

    logger.info(f"Запросил статистику поста {result.get('post_id')}",
                extra={"user_id": message.from_user.id,
                       "username": message.from_user.username,
                       "action": "admin_poststats"})


@admin_router.message(Command("log"))
async def get_log_lines(message: types.Message):
    try:
        # Извлекаем количество строк из команды
        parts = message.text.strip().split()
        num_lines = int(parts[1]) if len(parts) > 1 else 10  # по умолчанию 10

        log_path = os.path.join(os.getcwd(), "user_actions.log")

        if not os.path.exists(log_path):
            await message.answer("Файл логов не найден.")
            return

        # Читаем последние строки файла
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_lines = lines[-num_lines:]

        text = "".join(last_lines).strip()
        if not text:
            text = "Лог пуст."
        elif len(text) > 4000:
            text = "Слишком много данных для вывода. Запросите меньше строк."

        await message.answer(f"📄 Последние {num_lines} строк(и) лога:\n\n{text}")

    except ValueError:
        await message.answer("Неверный формат команды. Используйте: /log <количество_строк>")
    except Exception as e:
        await message.answer(f"Ошибка при получении логов: {e}")


async def get_post_stats(post_id=None, short_link=None):
    params = {}
    if post_id:
        params["post_id"] = post_id
    if short_link:
        params["short_link"] = short_link

    response = requests.get(f"{'http://s.forpost.me'}/stats", params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка: {response.status_code}, {response.json()}")
