from sqlalchemy import (
    BigInteger, Integer, VARCHAR, ForeignKeyConstraint, BINARY
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base
from sqlalchemy.dialects.mysql import JSON
import json
import uuid


class CreatedPosts(Base):
    __tablename__ = "created_posts"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger,
                                         nullable=False)
    text: Mapped[json] = mapped_column(JSON, nullable=False)
    images_links: Mapped[json] = mapped_column(JSON, nullable=True)
    mention_link: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    bot_message_id_list: Mapped[json] = mapped_column(JSON, nullable=True)

    user = relationship("User", back_populates="created_posts")
    bot = relationship("ForpostBotList", back_populates="created_posts", overlaps="created_posts, user")

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

