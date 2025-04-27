from sqlalchemy import (
    BigInteger, Boolean, JSON, VARCHAR, Integer, BINARY
)
import uuid
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database.base import Base
import json
from sqlalchemy import ForeignKeyConstraint

class AutoPosts(Base):
    __tablename__ = "auto_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    text: Mapped[json] = mapped_column(JSON, nullable=False)
    images_links: Mapped[json] = mapped_column(JSON, nullable=True)
    times: Mapped[json] = mapped_column(JSON, nullable=True)
    mention_link: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    activated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=0)
    bot_message_id_list: Mapped[json] = mapped_column(JSON, nullable=True)

    user = relationship("User", back_populates="auto_posts")
    schedule = relationship("Schedule", back_populates="post", cascade="all, delete", overlaps="schedule, user")
    bot = relationship("ForpostBotList", back_populates="auto_posts", overlaps="auto_posts,user")

    __table_args__ = (
        # Связь на пользователя
        ForeignKeyConstraint(
            ['bot_id', 'user_id'],
            ['users.bot_id', 'users.telegram_user_id'],
            ondelete="CASCADE"
        ),
        # Связь на бота
        ForeignKeyConstraint(
            ['bot_id'],
            ['forpost_bot_list.id'],
            ondelete="CASCADE"
        ),
    )
