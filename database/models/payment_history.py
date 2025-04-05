from sqlalchemy import (
    BigInteger, String, DECIMAL, ForeignKey, TIMESTAMP, func, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base


class PaymentHistory(Base):
    __tablename__ = "payment_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger,
                                         ForeignKey("users.telegram_user_id", ondelete="CASCADE"),
                                         nullable=False)
    gate_payment_id: Mapped[str] = mapped_column(String(255), nullable=True)
    packet_type: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payment_message_id: Mapped[int] = mapped_column(Integer, nullable=True)
    amount: Mapped[float] = mapped_column(DECIMAL(8, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    user = relationship("User", back_populates="payment_history")