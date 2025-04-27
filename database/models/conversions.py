from sqlalchemy import (
    TIMESTAMP, func, VARBINARY, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base
from sqlalchemy import ForeignKeyConstraint


class Conversion(Base):
    __tablename__ = "conversions"

    bot_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ip: Mapped[bytes] = mapped_column(VARBINARY(16), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    post = relationship("PostedHistory", back_populates="conversions", overlaps="posted_history, user, conversions, prices, bot")
    bot = relationship("ForpostBotList", back_populates="conversions", overlaps="conversions")

    __table_args__ = (
        ForeignKeyConstraint(
            ["bot_id", "post_id"],
            ["posted_history.bot_id", "posted_history.id"]
        ),
        ForeignKeyConstraint(
            ["bot_id"],
            ["forpost_bot_list.id"]
        ),
    )
