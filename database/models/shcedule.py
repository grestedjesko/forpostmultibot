from sqlalchemy import (
    BigInteger, Boolean, ForeignKey, TIMESTAMP, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base


class Schedule(Base):
    __tablename__ = "schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger,
                                         ForeignKey("users.telegram_user_id", ondelete="CASCADE"),
                                         nullable=False)
    scheduled_post_id: Mapped[int] = mapped_column(BigInteger,
                                                   ForeignKey("auto_posts.id", ondelete="CASCADE"),
                                                   nullable=False)
    time: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False)

    user = relationship("User", back_populates="schedule")
    post = relationship("AutoPosts", back_populates="schedule")