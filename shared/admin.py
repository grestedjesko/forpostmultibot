from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from database.models import User, PaymentHistory, PostedHistory, UserPackets


class AdminManager():
    @staticmethod
    async def get_user_info(session: AsyncSession, user_id: int | None = None, username: str | None = None):
        # Подзапрос для суммирования платежей
        payment_subq = (
            sa.select(sa.func.coalesce(sa.func.sum(PaymentHistory.amount), 0))
            .where(PaymentHistory.user_id == User.telegram_user_id)
            .scalar_subquery()
        )

        # Подзапрос для подсчёта постов
        posts_subq = (
            sa.select(sa.func.count(PostedHistory.id))
            .where(PostedHistory.user_id == User.telegram_user_id)
            .scalar_subquery()
        )

        # Основной запрос
        query = (
            sa.select(
                User.telegram_user_id,
                User.first_name,
                User.username,
                User.balance,
                payment_subq.label("total_paid"),
                posts_subq.label("posts_count"),
            )
        )

        # Фильтрация по user_id или username
        if user_id is not None:
            query = query.where(User.telegram_user_id == user_id)
        elif username is not None:
            query = query.where(User.username == username)

        result = await session.execute(query)
        user_data = result.fetchone()
        print('data:', user_data)
        return user_data

    @staticmethod
    async def save_payment(user_id: int, amount: int, packet_type: int, session: AsyncSession):
        payment = PaymentHistory(user_id=user_id,
                                 packet_type=packet_type,
                                 amount=amount,
                                 status='succeeded')
        session.add(payment)
        await session.commit()
