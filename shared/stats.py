from sqlalchemy import select, func, case
from src.data_classes import BotWrapper
from configs import config
from database.models import User, PaymentHistory, PostedHistory
from datetime import date
from aiogram import Bot
from database.base import async_session_factory
import asyncpg
from datetime import datetime
from database.models.stats import Stats



async def send_stats(target_date: date, bot_wrapper: BotWrapper):
    recharge_query = select(
        func.count().label("recharge_count"),
        func.coalesce(func.sum(PaymentHistory.amount), 0).label("recharge_sum")
    ).where(
        PaymentHistory.packet_type == 1,
        func.date(PaymentHistory.created_at) == target_date,
        PaymentHistory.status == 'succeeded'
    )

    # Покупки пакетов (packet_type > 1)
    purchase_query = select(
        func.count(PaymentHistory.id),
        func.coalesce(func.sum(PaymentHistory.amount), 0)
    ).where(
        PaymentHistory.packet_type > 1,
        func.date(PaymentHistory.created_at) == target_date,
        PaymentHistory.status == 'succeeded'
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

    click_count = await get_click_count(bot_id=bot_wrapper.bot.id, target_date=datetime.now().date())

    async with async_session_factory() as session:
        recharge_result = (await session.execute(recharge_query)).one()
        purchase_result = (await session.execute(purchase_query)).one()
        registration_result = (await session.execute(registration_query)).scalar()
        posting_result = (await session.execute(posting_query)).one()

        """
        stats = Stats(bot_id=bot_wrapper.id,
                      date=datetime.now().date(),
                      posted_new=posted_new,
                      posted_old=posted_old,
                      upbal_count_new=upbal_count_new,
                      upbal_sum_new=upbal_sum_new,
                      reg=registration_result)

        """

    txt = f"""Отчёт за {target_date}

Сумма доходов: {float(recharge_result[1]) + float(purchase_result[1])}
Пополнений: {float(recharge_result[1])} {recharge_result[0]}
Пакетов: {float(purchase_result[1])} {purchase_result[0]}

Новых регистраций: {registration_result}

Размещено поштучных: {posting_result[0]}
Размещено пакетом: {posting_result[1]}

Кликов по объявлениям: {click_count}"""

    await bot.send_message(config.chat_map.get("report"), txt)




async def get_click_count(bot_id: int, target_date: date) -> int:
    conn = await asyncpg.connect(
        user='j98603797_tgsh',
        password='gjz6wmqsmfX',
        database='j98603797_tgshort',
        host='mysql.bc9753bc1538.hosting.myjino.ru',
        port=3306
    )

    row = await conn.fetchrow("""
        SELECT COUNT(*) AS click_count
        FROM visit_log
        WHERE bot_id=%s 
        AND DATE(timestamp) = %s
    """, (bot_id, target_date,))

    await conn.close()

    return row['click_count'] or 0