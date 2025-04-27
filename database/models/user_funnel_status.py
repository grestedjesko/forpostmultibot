from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKeyConstraint, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database.base import Base
from zoneinfo import ZoneInfo


class UserFunnelStatus(Base):
    __tablename__ = 'user_funnels_status'

    id: Mapped[int] = mapped_column(Integer, primary_key=True,  autoincrement=True)
    bot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    funnel_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[str] = mapped_column(String(100), nullable=True)
    activated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(ZoneInfo("Europe/Moscow")))
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(ZoneInfo("Europe/Moscow")),
                                                   onupdate=datetime.now(ZoneInfo("Europe/Moscow")))
    ended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user = relationship("User", back_populates="funnels_status")
    scheduled_messages = relationship("FunnelScheduledMessage", back_populates="user_funnel")
    bot = relationship("ForpostBotList", back_populates="user_funnels_status", overlaps="funnels_status,user")

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

