from sqlalchemy import BigInteger, Integer, ForeignKeyConstraint, Date, TIMESTAMP, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base


class UserActivity(Base):
    __tablename__ = 'user_activity'

    bot_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    date: Mapped[datetime] = mapped_column(Date, primary_key=True)
    count_activities: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_activity_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        # Связь на пользователя
        ForeignKeyConstraint(
            ['bot_id', 'user_id'],
            ['users.bot_id', 'users.telegram_user_id'],
            ondelete="CASCADE"
        ),
        # Связь на бота
        ForeignKeyConstraint(
            ['bot_id'],
            ['forpost_bot_list.id'],
            ondelete="CASCADE"
        ),
    )

    user = relationship("User", back_populates="user_activity")
    bot = relationship("ForpostBotList", back_populates="user_activity", overlaps="user, user_activity")
