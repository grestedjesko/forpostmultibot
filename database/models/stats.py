from sqlalchemy import Integer, String, Date, Column
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base


class Stats(Base):
    __tablename__ = "stats"

    date: Mapped[Date] = mapped_column(Date, primary_key=True)  # Используем дату как PK
    posted_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    posted_old: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upbal_count_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upbal_count_old: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upbal_sum_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upbal_sum_old: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reg: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
