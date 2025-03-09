from sqlalchemy import BigInteger, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base
from sqlalchemy.orm import relationship


class Packets(Base):
    __tablename__ = "packets"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("prices.id", ondelete="CASCADE"), primary_key=True)
    name: Mapped[str] = mapped_column(String(100, collation='utf8mb4_unicode_ci'), nullable=False)
    short_name: Mapped[str] = mapped_column(String(100, collation='utf8mb4_unicode_ci'), nullable=True)
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    count_per_day: Mapped[int] = mapped_column(Integer, nullable=False)

    prices = relationship("Prices", back_populates="packets", cascade="save-update, merge")
    user_packets = relationship("UserPackets", back_populates="packets", cascade="save-update, merge")

    def __repr__(self):
        return f"<Packet(id={self.id}, name='{self.name}', button_title='{self.short_name if self.short_name else self.name}', period={self.period}, count_per_day={self.count_per_day})>"