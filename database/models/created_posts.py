from sqlalchemy import (
    BigInteger, String, ForeignKey, Text, TIMESTAMP, func, Integer, VARCHAR
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base
from sqlalchemy.dialects.mysql import JSON
import json


class CreatedPosts(Base):
    __tablename__ = "created_posts"

    id: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger,
                                         ForeignKey("users.telegram_user_id",
                                                    ondelete="CASCADE"),
                                         nullable=False)
    text: Mapped[json] = mapped_column(JSON, nullable=False)
    images_links: Mapped[json] = mapped_column(JSON, nullable=True)
    mention_link: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    bot_message_id_list: Mapped[json] = mapped_column(JSON, nullable=True)

    user = relationship("User", back_populates="created_posts")

