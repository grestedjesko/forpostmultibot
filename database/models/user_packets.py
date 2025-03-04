from sqlalchemy import BigInteger, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base


class UserPackets(Base):
    __tablename__ = "user_packets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_user_id", ondelete="CASCADE"), nullable=False)
    type: Mapped[int] = mapped_column(Integer, ForeignKey("packets.id", ondelete="CASCADE"), nullable=False)
    activated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ending_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    today_posts: Mapped[int] = mapped_column(Integer, nullable=False)
    used_posts: Mapped[int] = mapped_column(Integer, nullable=False)
    all_posts: Mapped[int] = mapped_column(Integer, nullable=False)

    user = relationship("User", back_populates="user_packets")
    packets = relationship("Packets", back_populates="user_packets")

    def __repr__(self):
        return f"<UserPacket(id={self.id}, user_id={self.user_id})>"
