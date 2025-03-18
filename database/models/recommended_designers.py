from sqlalchemy import (
    BigInteger, ForeignKey, Integer, DateTime
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base


class RecommendedDesigners(Base):
    __tablename__ = "recommended_designers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger,
                                         ForeignKey("users.telegram_user_id", ondelete="CASCADE"),
                                         nullable=False)
    ending_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user = relationship("User", back_populates="recommended_designers")