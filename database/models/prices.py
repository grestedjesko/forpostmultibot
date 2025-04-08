from sqlalchemy import BigInteger, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base
from sqlalchemy.orm import relationship


class Prices(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    packets = relationship("Packets", back_populates="prices", cascade="save-update, merge")
    posted_history = relationship("PostedHistory", back_populates="prices")


class OneTimePacket:
    def __init__(self, id, name, price):
        self.id = id
        self.name = name
        self.price = price

    def __repr__(self):
        return f"<OneTimePacket(id={self.id}, name='{self.name}', price={self.price})>"
