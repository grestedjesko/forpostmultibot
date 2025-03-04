from sqlalchemy import (
    BigInteger, ForeignKey, TIMESTAMP, func, VARBINARY
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base


class Conversion(Base):
    __tablename__ = "conversions"

    post_id: Mapped[int] = mapped_column(BigInteger,
                                         ForeignKey("posted_history.id", ondelete="CASCADE"),
                                         primary_key=True)
    ip: Mapped[bytes] = mapped_column(VARBINARY(16), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    post = relationship("PostedHistory", back_populates="conversions")