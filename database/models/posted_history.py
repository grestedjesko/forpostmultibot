from sqlalchemy import (
    BigInteger, TIMESTAMP, func, JSON, Integer, VARCHAR, ForeignKeyConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base
import json


class PostedHistory(Base):
    __tablename__ = "posted_history"

    bot_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_text: Mapped[json] = mapped_column(JSON, nullable=False)
    message_photo: Mapped[json] = mapped_column(JSON, nullable=True)
    mention_link: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.current_timestamp()
    )
    packet_type: Mapped[int] = mapped_column(Integer, nullable=False)

    user = relationship("User", back_populates="posted_history")
    conversions = relationship("Conversion", back_populates="post", cascade="save-update, merge")
    prices = relationship("Prices", back_populates="posted_history", overlaps="posted_history, user")
    bot = relationship("ForpostBotList", back_populates="posted_history", overlaps="posted_history,prices,user")

    __table_args__ = (
        ForeignKeyConstraint(
            ['bot_id', 'user_id'],
            ['users.bot_id', 'users.telegram_user_id'],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ['bot_id', 'packet_type'],
            ['prices.bot_id', 'prices.id'],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ['bot_id'],
            ['forpost_bot_list.id'],
            ondelete="CASCADE"
        ),
    )
