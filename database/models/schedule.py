from sqlalchemy import BigInteger, Boolean, TIMESTAMP, Integer, ForeignKeyConstraint, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base
import uuid


class Schedule(Base):
    __tablename__ = "schedule"

    id: Mapped[str] = mapped_column(Integer, autoincrement=True, primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    scheduled_post_id: Mapped[int] = mapped_column(Integer, nullable=False)

    time: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False)

    user = relationship("User", back_populates="schedule")
    post = relationship("AutoPosts", back_populates="schedule")
    bot = relationship("ForpostBotList", back_populates="schedule", overlaps="schedule, user")

    __table_args__ = (
        ForeignKeyConstraint(
            ['bot_id', 'user_id'],
            ['users.bot_id', 'users.telegram_user_id'],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ['scheduled_post_id'],
            ['auto_posts.id'],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ['bot_id'],
            ['forpost_bot_list.id'],
            ondelete="CASCADE"
        ),
    )
