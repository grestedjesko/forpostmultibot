from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKeyConstraint, TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database.base import Base
import uuid


class FunnelScheduledMessage(Base):
    __tablename__ = 'funnel_scheduled_messages'

    id: Mapped[str] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    funnel_base_id: Mapped[int] = mapped_column(Integer, nullable=False)
    message_id: Mapped[str] = mapped_column(String(100), nullable=False)
    text: Mapped[str] = mapped_column(TEXT(collation='utf8mb4_general_ci'), nullable=False)
    send_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    user_funnel = relationship("UserFunnelStatus", back_populates="scheduled_messages")
    bot = relationship("ForpostBotList", back_populates="funnel_scheduled_messages")

    __table_args__ = (
        # Связь на пользователя
        ForeignKeyConstraint(
            ['funnel_base_id'],
            ['user_funnels_status.id'],
            ondelete="CASCADE"
        ),
        # Связь на бота
        ForeignKeyConstraint(
            ['bot_id'],
            ['forpost_bot_list.id'],
            ondelete="CASCADE"
        ),
    )
