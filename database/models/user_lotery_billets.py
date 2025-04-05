from sqlalchemy import ForeignKey, TIMESTAMP, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
from database.base import Base


class UserLoteryBillets(Base):
    __tablename__ = "user_lotery_billets"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_user_id"), primary_key=True, unique=True)
    billets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used_billets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    user = relationship("User", back_populates="billets")