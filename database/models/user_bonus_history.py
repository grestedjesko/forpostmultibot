from sqlalchemy import (
    BigInteger, String, DECIMAL, ForeignKey, VARCHAR, TIMESTAMP, func, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base
from enum import Enum as PyEnum


class UserBonusHistory(Base):
    __tablename__ = "user_bonus_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger,
                                         ForeignKey("users.telegram_user_id", ondelete="CASCADE"),
                                         nullable=False)
    packet_type: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    amount: Mapped[int] = mapped_column(Integer, nullable=True)
    giver: Mapped[str] = mapped_column(VARCHAR(30), nullable=False)
    given_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    user = relationship("User", back_populates="bonus_history")