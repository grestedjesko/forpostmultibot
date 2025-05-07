from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from database.models import User, PaymentHistory, PostedHistory, UserPackets


class AdminManager():
    @staticmethod
    async def get_user_info(session: AsyncSession, user_id: int | None = None, username: str | None = None):
        bot_id = session.info["bot_id"]

        payment_subq = (
            sa.select(sa.func.coalesce(sa.func.sum(PaymentHistory.amount), 0))
            .where(
                sa.and_(
                    PaymentHistory.user_id == User.telegram_user_id,
                    PaymentHistory.bot_id == bot_id  # bot_id у платежей
                )
            )
            .scalar_subquery()
        )

        posts_subq = (
            sa.select(sa.func.count(PostedHistory.id))
            .where(
                sa.and_(
                    PostedHistory.user_id == User.telegram_user_id,
                    PostedHistory.bot_id == bot_id  # bot_id у постов
                )
            )
            .scalar_subquery()
        )

        query = (
            sa.select(
                User.telegram_user_id,
                User.first_name,
                User.username,
                User.balance,
                payment_subq.label("total_paid"),
                posts_subq.label("posts_count"),
            )
            .where(
                User.bot_id == bot_id  # bot_id у пользователя
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
        bot_id = session.info["bot_id"]

        result = await session.execute(sa.select(sa.func.max(PaymentHistory.id)).where(PaymentHistory.bot_id == bot_id))
        max_id = result.scalar() or 0
        new_id = max_id + 1

        payment = PaymentHistory(id=new_id,
                                 bot_id=bot_id,
                                 user_id=user_id,
                                 packet_type=packet_type,
                                 amount=amount,
                                 status='succeeded')
        session.add(payment)
        await session.commit()
