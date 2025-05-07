from sqlalchemy import BigInteger, Integer, DateTime, ForeignKeyConstraint, String, TIMESTAMP
import uuid
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base


class UserPackets(Base):
    __tablename__ = "user_packets"

    id: Mapped[str] = mapped_column(Integer, autoincrement=True, primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # foreign
    type: Mapped[int] = mapped_column(Integer, nullable=False)  # foreign

    activated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    ending_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    today_posts: Mapped[int] = mapped_column(Integer, nullable=False)
    used_posts: Mapped[int] = mapped_column(Integer, nullable=False)
    all_posts: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        # связь с пользователями
        ForeignKeyConstraint(
            ["bot_id", "user_id"],
            ["users.bot_id", "users.telegram_user_id"],
            ondelete="CASCADE"
        ),
        # связь с пакетами
        ForeignKeyConstraint(
            ["bot_id", "type"],
            ["packets.bot_id", "packets.id"],
            ondelete="CASCADE"
        ),
        # связь с таблицей ботов
        ForeignKeyConstraint(
            ["bot_id"],
            ["forpost_bot_list.id"],
            ondelete="CASCADE"
        ),
    )

    user = relationship("User",
                        back_populates="user_packets", overlaps="")

    packets = relationship("Packets",
                           back_populates="user_packets", overlaps="user_packets, user")

    bot = relationship("ForpostBotList",
                       back_populates="user_packets", overlaps="user_packets, packets, user")

    def __repr__(self):
        return f"<UserPacket(bot_id={self.bot_id}, id={self.id}, user_id={self.user_id})>"
