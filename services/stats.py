import datetime

from sqlalchemy import select, func, and_, case

import config
from database.models import User, PaymentHistory, PostedHistory, Conversion
from datetime import date
from aiogram import Bot
from database.base import async_session_factory
import asyncio


async def send_stats(target_date: date, bot: Bot):
    recharge_query = select(
        func.count().label("recharge_count"),
        func.coalesce(func.sum(PaymentHistory.amount), 0).label("recharge_sum")
    ).where(
        PaymentHistory.packet_type == 1,
        func.date(PaymentHistory.created_at) == target_date
    )

    # Покупки пакетов (packet_type > 1)
    purchase_query = select(
        func.count(PaymentHistory.id),
        func.coalesce(func.sum(PaymentHistory.amount), 0)
    ).where(
        PaymentHistory.packet_type > 1,
        func.date(PaymentHistory.created_at) == target_date
    )

    # Регистрации
    registration_query = select(
        func.count().label("registration_count")
    ).where(
        func.date(User.created_at) == target_date
    )

    # Размещения
    posting_query = select(
        func.sum(
            case((PostedHistory.packet_type == 1, 1), else_=0)
        ).label("posting_count_balance"),
        func.sum(
            case((PostedHistory.packet_type > 1, 1), else_=0)
        ).label("posting_count_package")
    ).where(
        func.date(PostedHistory.created_at) == target_date
    )

    '''# Переходы
    click_query = select(
        func.count().label("click_count")
    ).where(
        Conversion.method == "GET",
        Conversion.url.like("https://s.forpost.me%"),
        func.date(Conversion.created_at) == target_date
    )'''

    async with async_session_factory() as session:
        recharge_result = (await session.execute(recharge_query)).one()
        purchase_result = (await session.execute(purchase_query)).one()
        registration_result = (await session.execute(registration_query)).scalar()
        posting_result = (await session.execute(posting_query)).one()

    txt = f"""Отчёт за {target_date}

Сумма доходов: {float(recharge_result[1]) + float(purchase_result[1])}
Пополнений: {float(recharge_result[1])} {recharge_result[0]}
Пакетов: {float(purchase_result[1])} {purchase_result[0]}

Новых регистраций: {registration_result}

Размещено поштучных: {posting_result[0]}
Размещено пакетом: {posting_result[1]}"""

    await bot.send_message(config.chat_map.get("report"), txt)

