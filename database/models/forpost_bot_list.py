from database.base import Base
from sqlalchemy import BigInteger, TEXT
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
import json


class ForpostBotList(Base):
    __tablename__ = 'forpost_bot_list'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(Integer, nullable=False)
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    image_link: Mapped[str] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False)

    forpost_bot_configs = relationship("ForpostBotConfigs", back_populates="forpost_bot_list")
    forpost_bot_text_configs = relationship("ForpostBotTextConfigs", back_populates="forpost_bot_list")
    forpost_bot_bonus_configs = relationship("ForpostBotBonusConfigs", back_populates="forpost_bot_list")

    users = relationship('User', back_populates='bot')
    user_promotion = relationship('UserPromotion', back_populates='bot', overlaps="promotion, user_promotion") # promotion,promotion,user,user_promotion
    user_packets = relationship('UserPackets', back_populates='bot', overlaps="user, packets, user_packets")
    user_lotery_billets = relationship('UserLoteryBillets', back_populates='bot', overlaps="billets, user")
    user_bonus_history = relationship('UserBonusHistory', back_populates='bot', overlaps="bonus_history, user")
    user_activity = relationship('UserActivity', back_populates='bot', overlaps="user, user_activity")
    stats = relationship('Stats', back_populates='bot')
    schedule = relationship('Schedule', back_populates='bot', overlaps="schedule, user")
    recommended_designers = relationship('RecommendedDesigners', back_populates='bot', overlaps="recommended_designers, user")
    promotion = relationship('Promotion', back_populates='bot')
    prices = relationship('Prices', back_populates='bot')
    posted_history = relationship('PostedHistory', back_populates='bot', overlaps="posted_history,prices,user")
    payment_history = relationship('PaymentHistory', back_populates='bot', overlaps="payment_history, user")
    packets = relationship('Packets', back_populates='bot')

    funnel_user_actions = relationship('FunnelUserAction', back_populates='bot', overlaps="funnel_actions, user")
    funnel_scheduled_messages = relationship('FunnelScheduledMessage', back_populates='bot')
    user_funnels_status = relationship('UserFunnelStatus', back_populates='bot', overlaps="funnels_status, user")

    created_posts = relationship('CreatedPosts', back_populates='bot', overlaps="created_posts, user")
    conversions = relationship('Conversion', back_populates='bot', overlaps="conversions")
    auto_posts = relationship('AutoPosts', back_populates='bot', overlaps="auto_posts, user")
    archive_packets = relationship('ArchivePackets', back_populates='bot', overlaps="archive_packets, user")


class ForpostBotConfigs(Base):
    __tablename__ = 'forpost_bot_configs'

    bot_id: Mapped[int] = mapped_column(ForeignKey("forpost_bot_list.id"), primary_key=True)
    config_name: Mapped[str] = mapped_column(String(255), nullable=False, primary_key=True)
    config_value: Mapped[dict] = mapped_column(TEXT, nullable=False)

    forpost_bot_list = relationship("ForpostBotList", back_populates="forpost_bot_configs")


class ForpostBotTextConfigs(Base):
    __tablename__ = 'forpost_bot_text_configs'

    bot_id: Mapped[int] = mapped_column(ForeignKey("forpost_bot_list.id"), primary_key=True)
    text_id: Mapped[str] = mapped_column(String(255), nullable=False, primary_key=True)
    text: Mapped[dict] = mapped_column(TEXT, nullable=False)

    forpost_bot_list = relationship("ForpostBotList", back_populates="forpost_bot_text_configs")


class ForpostBotBonusConfigs(Base):
    __tablename__ = 'forpost_bot_bonus_configs'

    bot_id: Mapped[int] = mapped_column(ForeignKey("forpost_bot_list.id"), primary_key=True)
    config_name: Mapped[str] = mapped_column(String(255), nullable=False, primary_key=True)
    config_value: Mapped[dict] = mapped_column(TEXT, nullable=False)

    forpost_bot_list = relationship("ForpostBotList", back_populates="forpost_bot_bonus_configs")

