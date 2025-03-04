from sqlalchemy import (
    BigInteger, String, ForeignKey, Text, TIMESTAMP, func, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base
import json


class PostedHistory(Base):
    __tablename__ = "posted_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger,
                                         ForeignKey("users.telegram_user_id",
                                                    ondelete="CASCADE"),
                                         nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    message_photo: Mapped[json] = mapped_column(JSON, nullable=True)
    link: Mapped[str] = mapped_column(String(255), nullable=False)
    hash_link: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP,
                                                 nullable=False,
                                                 server_default=func.current_timestamp())

    user = relationship("User", back_populates="posted_history")
    conversions = relationship("Conversion", back_populates="post", cascade="save-update, merge")




