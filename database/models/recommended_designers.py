from sqlalchemy import BigInteger, Integer, DateTime, ForeignKeyConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base


class RecommendedDesigners(Base):
    __tablename__ = "recommended_designers"

    bot_id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, primary_key=True)
    ending_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user = relationship("User", back_populates="recommended_designers")
    bot = relationship("ForpostBotList", back_populates="recommended_designers", overlaps="recommended_designers,user")

    __table_args__ = (
        ForeignKeyConstraint(
            ['bot_id', 'user_id'],
            ['users.bot_id', 'users.telegram_user_id'],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ['bot_id'],
            ['forpost_bot_list.id'],
            ondelete="CASCADE"
        ),
    )
