from sqlalchemy import BigInteger, Integer, ForeignKey, Date, TIMESTAMP, func, PrimaryKeyConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base


class UserActivity(Base):
    __tablename__ = 'user_activity'

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_user_id", ondelete="CASCADE"),
                                         nullable=False)
    date: Mapped[int] = mapped_column(Date, nullable=False)
    count_activities: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_activity_time: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="user_activity")

    __table_args__ = (
        PrimaryKeyConstraint("user_id", "date"),  # Указываем составной первичный ключ
    )
