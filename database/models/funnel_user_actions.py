from sqlalchemy import Integer, String, DateTime, Enum, Boolean, ForeignKeyConstraint, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database.base import Base
from enum import Enum as PyEnum
import uuid
from zoneinfo import ZoneInfo



class FunnelUserActionsType(str, PyEnum):
    REGISTERED = "REGISTERED"
    INITIATED_DEPOSIT = "INITIATED_DEPOSIT"
    DEPOSITED = "DEPOSITED"
    POSTED = "POSTED"
    INITIATED_PACKET_PURCHASE = "INITIATED_PACKET_PURCHASE"
    PACKET_PURCHASED = "PACKET_PURCHASED"
    PACKET_ENDED = "PACKET_ENDED"


class FunnelUserAction(Base):
    __tablename__ = 'funnel_user_actions'

    id: Mapped[str] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action: Mapped[str] = mapped_column(Enum(FunnelUserActionsType), nullable=False)
    details: Mapped[str] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(ZoneInfo("Europe/Moscow")))
    used: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="funnel_actions")
    bot = relationship("ForpostBotList", back_populates="funnel_user_actions", overlaps="funnel_actions, user")

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
