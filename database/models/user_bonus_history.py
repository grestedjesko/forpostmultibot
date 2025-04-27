from sqlalchemy import (
    BigInteger, VARCHAR, TIMESTAMP, func, Integer, ForeignKeyConstraint, String
)
import uuid
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base


class UserBonusHistory(Base):
    __tablename__ = "user_bonus_history"

    id: Mapped[str] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    packet_type: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    amount: Mapped[int] = mapped_column(Integer, nullable=True)
    giver: Mapped[str] = mapped_column(VARCHAR(30), nullable=False)
    given_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    user = relationship("User", back_populates="bonus_history")
    bot = relationship("ForpostBotList", back_populates="user_bonus_history", overlaps="bonus_history,user")

    __table_args__ = (
        # Связь с users
        ForeignKeyConstraint(
            ["bot_id", "user_id"],
            ["users.bot_id", "users.telegram_user_id"],
            ondelete="CASCADE"
        ),
        # Связь с forpost_bot_list
        ForeignKeyConstraint(
            ["bot_id"],
            ["forpost_bot_list.id"],
            ondelete="CASCADE"
        ),
    )
