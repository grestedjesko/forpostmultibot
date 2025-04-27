from sqlalchemy import Integer, Date, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base


class Stats(Base):
    __tablename__ = "stats"

    bot_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, primary_key=True)

    posted_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    posted_old: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upbal_count_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upbal_count_old: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upbal_sum_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upbal_sum_old: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reg: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    bot = relationship("ForpostBotList", back_populates="stats")

    __table_args__ = (
        ForeignKeyConstraint(
            ['bot_id'],
            ['forpost_bot_list.id'],
            ondelete="CASCADE"
        ),
    )
