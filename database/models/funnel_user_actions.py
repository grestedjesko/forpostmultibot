from sqlalchemy import ForeignKey, Integer, String, DateTime, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database.base import Base
from enum import Enum as PyEnum


class FunnelUserActionsType(str, PyEnum):
    REGISTERED = "REGISTERED"
    INITIATED_DEPOSIT = "INITIATED_DEPOSIT"
    DEPOSITED = "DEPOSITED"
    POSTED = "POSTED"
    INITIATED_PACKET_PURCHASE = "INITIATED_PACKET_PURCHASE"
    PACKET_PURCHASED = "PACKET_PURCHASED"
    PACKET_ENDED = "PACKET_ENDED"


class FunnelUserAction(Base):
    __tablename__ = 'funnel_user_actions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_user_id"), nullable=False)
    action: Mapped[str] = mapped_column(Enum(FunnelUserActionsType), nullable=False)
    details: Mapped[str] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    used: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="funnel_actions")


class FunnelScheduledMessage(Base):
    __tablename__ = 'funnel_scheduled_messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    funnel_base_id: Mapped[str] = mapped_column(ForeignKey("user_funnels_status.id"), nullable=False)
    message_id: Mapped[str] = mapped_column(String(100), nullable=False)
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    send_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    user_funnel = relationship("UserFunnelStatus", back_populates="scheduled_messages")


class UserFunnelStatus(Base):
    __tablename__ = 'user_funnels_status'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_user_id"), nullable=False)
    funnel_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[str] = mapped_column(String(100), nullable=True)
    activated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user = relationship("User", back_populates="funnels_status")
    scheduled_messages = relationship("FunnelScheduledMessage", back_populates="user_funnel")

