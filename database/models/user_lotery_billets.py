from sqlalchemy import ForeignKeyConstraint, Integer, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base


class UserLoteryBillets(Base):
    __tablename__ = "user_lotery_billets"

    bot_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    billets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used_billets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="billets")
    bot = relationship("ForpostBotList", back_populates="user_lotery_billets", overlaps="billets,user")

    __table_args__ = (
        # Связь на пользователя
        ForeignKeyConstraint(
            ["bot_id", "user_id"],
            ["users.bot_id", "users.telegram_user_id"],
            ondelete="CASCADE"
        ),
        # Связь на таблицу ботов
        ForeignKeyConstraint(
            ["bot_id"],
            ["forpost_bot_list.id"],
            ondelete="CASCADE"
        ),
    )
