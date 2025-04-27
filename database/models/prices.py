from sqlalchemy import Integer, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base
from sqlalchemy.orm import relationship


class Prices(Base):
    __tablename__ = "prices"

    bot_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    packets = relationship("Packets", back_populates="prices", cascade="save-update, merge", overlaps="packets, bot, prices")
    posted_history = relationship("PostedHistory", back_populates="prices",  overlaps="posted_history, user, conversions, prices, bot")
    bot = relationship("ForpostBotList", back_populates="prices")

    __table_args__ = (
        ForeignKeyConstraint(
            ['bot_id'],
            ['forpost_bot_list.id'],
            ondelete="CASCADE"
        ),
    )


class OneTimePacket:
    def __init__(self, id, name, price):
        self.id = id
        self.name = name
        self.price = price

    def __repr__(self):
        return f"<OneTimePacket(id={self.id}, name='{self.name}', price={self.price})>"
