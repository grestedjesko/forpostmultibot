from sqlalchemy import BigInteger, String, DECIMAL, TIMESTAMP, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from database.base import Base


class User(Base):
    __tablename__ = "users"

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    balance: Mapped[float] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())
    utm: Mapped[str] = mapped_column(String(255), nullable=True)

    payment_history = relationship("PaymentHistory", back_populates="user", cascade="save-update, merge")
    posted_history = relationship("PostedHistory", back_populates="user", cascade="save-update, merge")
    user_packets = relationship("UserPackets", back_populates="user", cascade="save-update, merge")
    created_posts = relationship("CreatedPosts", back_populates="user", cascade="save-update, merge")
    auto_posts = relationship("AutoPosts", back_populates="user", cascade="save-update, merge")
    schedule = relationship("Schedule", back_populates="user", cascade="save-update, merge")
    user_activity = relationship("UserActivity", back_populates="user", cascade="save-update, merge")
    archive_packets = relationship("ArchivePackets", back_populates="user", cascade="save-update, merge")
    recommended_designers = relationship("RecommendedDesigners", back_populates="user", cascade="save-update, merge")
    bonus_history = relationship("UserBonusHistory", back_populates="user", cascade="save-update, merge")
    promotion = relationship("UserPromotion", back_populates="user")
    billets = relationship("UserLoteryBillets", back_populates="user")
    funnel_actions = relationship("FunnelUserAction", back_populates="user")
    funnels_status = relationship("UserFunnelStatus", back_populates="user")

    def __repr__(self):
        return f"<User(telegram_user_id={self.telegram_user_id}, name={self.first_name})>"
