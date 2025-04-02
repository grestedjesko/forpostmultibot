from sqlalchemy import (
    BigInteger, String, ForeignKey, Text, Boolean, JSON, VARCHAR
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database.base import Base
import json


class AutoPosts(Base):
    __tablename__ = "auto_posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_user_id", ondelete="CASCADE"), nullable=False)
    text: Mapped[json] = mapped_column(JSON, nullable=False)
    images_links: Mapped[json] = mapped_column(JSON, nullable=True)
    times: Mapped[json] = mapped_column(JSON, nullable=True)
    mention_link: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    activated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=0)
    bot_message_id_list: Mapped[json] = mapped_column(JSON, nullable=True)

    user = relationship("User", back_populates="auto_posts")
    schedule = relationship("Schedule", back_populates="post", cascade="all, delete")