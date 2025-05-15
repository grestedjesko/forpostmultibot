import datetime
from typing import List, Optional
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import InputMediaPhoto
from aiogram import Bot
from configs import config
from src.keyboards import Keyboard
from database.models import User, PostedHistory, CreatedPosts, AutoPosts, UserPackets
from database.models.schedule import Schedule
from shared.user import BalanceManager, UserManager
from shared.user_packet import PacketManager
from shared.pricelist import PriceList
from shared.post.short_link import ShortLink
from shared.funnel_actions import FunnelActions
from database.models.funnel_user_actions import FunnelUserActionsType
from zoneinfo import ZoneInfo
from shared.bot_config import BotConfig


class BasePost:
    def __init__(self, text: str,
                 author_id: int,
                 author_username: str,
                 bot_config: BotConfig,
                 images: Optional[List[str]] = None,
                 bot_message_id_list: Optional[List[int]] = None,
                 mention_link: Optional[str] = None,
                 posted_id: Optional[int] = None):
        self.text = text
        self.images = images
        self.author_id = author_id
        self.author_username = author_username
        self.bot_config = bot_config
        self.bot_message_id_list = bot_message_id_list
        self.mention_link = mention_link or self._generate_mention_link()
        self.posted_id = posted_id

    def _generate_mention_link(self):
        return f"https://t.me/{self.author_username}" if self.author_username else f"tg://user?id={self.author_id}"

    async def send(self, bot: Bot, session: AsyncSession):
        self.posted_id = await self.new_post(session=session)

        mention_link = await ShortLink.shorten_links([self.mention_link], self.posted_id, bot.id)
        text = await ShortLink.find_and_shorten_links(self.text, self.posted_id, bot.id)
        print(mention_link, text)
        if mention_link:
            mention_link = mention_link.get(self.mention_link)
            self.mention_link = mention_link
        if text:
            self.text = text

        recommended = await UserManager.check_recommended_status(user_id=self.author_id, session=session)
        recommended = int(recommended)
        message_id = await self.post_to_chat(bot=bot, recommended=recommended)
        if isinstance(message_id, list):
            message_id = message_id[0]
        else:
            message_id = message_id.message_id
        await self.set_post_sended(message_id, session)

    async def post_to_chat(self, bot: Bot, recommended: int):
        me = await bot.get_me()
        bot_url = f"https://t.me/{me.username}?start=fromchat"
        keyboard = Keyboard.chat_post_menu(self.mention_link, recommended, bot_url)
        if self.images:
            if len(self.images) == 1:
                return await bot.send_photo(chat_id=self.bot_config.chat_id, photo=self.images[0], caption=self.text,
                                            reply_markup=keyboard, parse_mode='html')
            media_group = [
                InputMediaPhoto(media=file_id, caption=self.text if i == 0 else "", parse_mode='html')
                for i, file_id in enumerate(self.images)
            ]
            return await bot.send_media_group(chat_id=self.bot_config.chat_id, media=media_group)
        return await bot.send_message(chat_id=self.bot_config.chat_id,
                                      text=self.text,
                                      reply_markup=keyboard,
                                      parse_mode='html',
                                      disable_web_page_preview=True)

    async def new_post(self, session: AsyncSession):
        bot_id = session.info['bot_id']
        result = await session.execute(sa.select(sa.func.max(PostedHistory.id)).where(PostedHistory.bot_id == bot_id))
        max_id = result.scalar() or 0
        new_id = max_id + 1

        stmt = sa.insert(PostedHistory).values(
            bot_id=self.bot_config.bot_id,
            id=new_id,
            user_id=self.author_id,
            message_text=self.text,
            message_photo=self.images,
            mention_link=self.mention_link,
            packet_type=1,
        ).returning(PostedHistory.id)
        res = await session.execute(stmt)
        await session.commit()
        return res.scalar()

    async def set_post_sended(self,  message_id: int, session: AsyncSession):
        stmt = (sa.update(PostedHistory)
                .values(message_id=message_id, mention_link=self.mention_link)
                .where(PostedHistory.id == self.posted_id, PostedHistory.bot_id == self.bot_config.bot_id))
        await session.execute(stmt)
        await session.commit()

    async def delete(self, session: AsyncSession):
        pass  # Переопределяется в подклассах


class Post(BasePost):
    def __init__(self, post_id: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.post_id = post_id

    @classmethod
    async def from_db(cls, post_id: int, session: AsyncSession, bot_config: BotConfig):
        stmt = sa.select(CreatedPosts, User.username).join(User, CreatedPosts.user_id == User.telegram_user_id).where(
            CreatedPosts.id == post_id)
        result = await session.execute(stmt)
        row = result.first()
        if row:
            created_post, username = row
            return cls(post_id=created_post.id,
                       text=created_post.text,
                       author_id=created_post.user_id,
                       author_username=username,
                       images=created_post.images_links,
                       mention_link=created_post.mention_link,
                       bot_message_id_list=created_post.bot_message_id_list,
                       bot_config=bot_config)
        return None

    async def create(self, session: AsyncSession):
        stmt = sa.insert(CreatedPosts).values(
            bot_id=self.bot_config.bot_id,
            user_id=self.author_id,
            text=self.text,
            images_links=self.images,
            mention_link=self.mention_link
        ).returning(CreatedPosts.id)
        result = await session.execute(stmt)
        self.post_id = result.scalar_one_or_none()
        await session.commit()
        return self.post_id

    async def post(self, session: AsyncSession, bot: Bot, logger):
        active_packet = await PacketManager.has_active_packet(user_id=self.author_id, session=session)
        today_limit = 0
        price = 0
        if active_packet:
            today_limit = await PacketManager.get_today_limit(user_id=self.author_id, session=session)

        if today_limit <= 0:
            price = (await PriceList.get_onetime_price(session=session))[0].price
            current_balance = await BalanceManager.get_balance(user_id=self.author_id, session=session)
            if current_balance < price:
                return False

        try:
            await self.send(bot=bot, session=session)
            await self.delete(session=session)
        except Exception as e:
            print(f"Ошибка при публикации: {e}")
            return False

        if today_limit > 0:
            await PacketManager.deduct_today_limit(user_id=self.author_id, session=session)
        else:
            await BalanceManager.deduct(user_id=self.author_id,
                                        amount=price,
                                        session=session,
                                        logger=logger)
            await FunnelActions.save(user_id=self.author_id, action=FunnelUserActionsType.POSTED, session=session)
        return True

    async def delete(self, session: AsyncSession):
        await session.execute(sa.delete(CreatedPosts).where(CreatedPosts.id == self.post_id))
        await session.commit()

    async def add_bot_message_id(self, bot_message_id_list: list, session: AsyncSession):
        """Добавление ID сообщений бота в базу"""
        stmt = (
            sa.update(CreatedPosts)
            .where(CreatedPosts.id == self.post_id)
            .values(bot_message_id_list=bot_message_id_list)
        )
        await session.execute(stmt)
        await session.commit()


class AutoPost(BasePost):
    def __init__(self, auto_post_id: Optional[int] = None, times: Optional[List[datetime.time]] = None, **kwargs):
        super().__init__(**kwargs)
        self.auto_post_id = auto_post_id
        self.times = times

    @classmethod
    async def from_db(cls, auto_post_id: int, session: AsyncSession, bot_config: BotConfig):
        bot_id = session.info["bot_id"]
        stmt = (
            sa.select(AutoPosts, User.username)
            .join(User, sa.and_(
                AutoPosts.user_id == User.telegram_user_id,
                AutoPosts.bot_id == User.bot_id  # соединение по bot_id
            ))
            .where(
                AutoPosts.id == auto_post_id,
                AutoPosts.bot_id == bot_id
            )
        )

        result = await session.execute(stmt)
        row = result.first()
        if row:
            auto_post, username = row
            return cls(auto_post_id=auto_post.id,
                       text=auto_post.text,
                       images=auto_post.images_links,
                       times=auto_post.times,
                       author_id=auto_post.user_id,
                       author_username=username,
                       bot_message_id_list=auto_post.bot_message_id_list,
                       mention_link=auto_post.mention_link,
                       bot_config=bot_config)
        return None

    async def create(self, session: AsyncSession):
        bot_id = session.info["bot_id"]
        stmt = sa.insert(AutoPosts).values(
            bot_id=bot_id,
            user_id=self.author_id,
            text=self.text,
            images_links=self.images,
            mention_link=self.mention_link,
            times=self.times,
            activated=0
        ).returning(AutoPosts.id)
        result = await session.execute(stmt)
        self.auto_post_id = result.scalar_one_or_none()
        await session.commit()
        return self.auto_post_id

    async def activate(self, session: AsyncSession):
        """Активация автопоста"""
        bot_id = session.info["bot_id"]
        await self.delete_active(session)
        await session.execute(
            sa.update(AutoPosts).values(activated=1).where(AutoPosts.id == self.auto_post_id, AutoPosts.bot_id == bot_id)
        )

        for time in self.times:
            time_parsed = datetime.datetime.strptime(time.strip(), "%H:%M").time()  # Преобразуем в объект time
            current_time = datetime.datetime.now().time()  # Берем только текущее время без даты
            print(current_time)
            completed = 0
            if time_parsed <= current_time:
                completed = 1
            sche_post = Schedule(
                bot_id=self.bot_config.bot_id,
                user_id=self.author_id,
                scheduled_post_id=self.auto_post_id,
                time=time_parsed,
                completed=completed
            )
            session.add(sche_post)
        await session.commit()

    async def post(self, bot: Bot, session: AsyncSession):
        print('postim')
        today_limit = await PacketManager.get_today_limit(user_id=self.author_id, session=session)
        if int(today_limit) <= 0:
            return
        await PacketManager.deduct_today_limit(user_id=self.author_id, session=session)
        await self.send(bot=bot, session=session)
        return True

    async def delete(self, session: AsyncSession):
        bot_id = session.info["bot_id"]
        await session.execute(sa.delete(AutoPosts).where(AutoPosts.id == self.auto_post_id, AutoPosts.bot_id == bot_id))
        await session.commit()

    async def delete_active(self, session: AsyncSession):
        """Удаление активных автопостов пользователя"""
        await session.execute(
            sa.delete(AutoPosts).where(AutoPosts.user_id == self.author_id,
                                       AutoPosts.activated == 1,
                                       AutoPosts.bot_id == session.info['bot_id'])
        )
        await session.commit()

    async def add_bot_message_id(self, bot_message_id_list: list, session: AsyncSession):
        bot_id = session.info["bot_id"]
        stmt = sa.update(AutoPosts).where(AutoPosts.id == self.auto_post_id, AutoPosts.bot_id==bot_id).values(
            bot_message_id_list=bot_message_id_list)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def get_auto_post(user_id: int, session: AsyncSession):
        bot_id = session.info["bot_id"]
        stmt = sa.select(AutoPosts).where(AutoPosts.user_id == user_id, AutoPosts.activated == 1, AutoPosts.bot_id == bot_id)
        result = await session.execute(stmt)
        r = result.scalar()
        return r

    async def update_time(self, times: list, session: AsyncSession):
        bot_id = session.info["bot_id"]
        stmt = sa.update(AutoPosts).values(times=times).where(AutoPosts.id == self.auto_post_id)
        stmt2 = sa.delete(Schedule).where(Schedule.scheduled_post_id == self.auto_post_id)
        await session.execute(stmt)
        await session.execute(stmt2)

        for time in times:
            time_parsed = datetime.datetime.strptime(time.strip(), "%H:%M").time()  # Преобразуем в объект time
            current_time = datetime.datetime.now().time()  # Берем только текущее время без даты
            print(current_time)

            completed = 0

            if time_parsed <= current_time:
                completed = 1

            stmt = sa.insert(Schedule).values(
                bot_id=bot_id,
                user_id=self.author_id,
                scheduled_post_id=self.auto_post_id,
                time=time_parsed,
                completed=completed
            )

            await session.execute(stmt)
        await session.commit()

    async def new_post(self, session: AsyncSession):
        bot_id = session.info["bot_id"]
        stmt = sa.select(UserPackets.type).where(UserPackets.user_id == self.author_id)
        typeid = (await session.execute(stmt)).scalar()

        result = await session.execute(
            sa.select(sa.func.max(PostedHistory.id)).where(PostedHistory.bot_id == bot_id))
        max_id = result.scalar() or 0
        new_id = max_id + 1

        stmt = sa.insert(PostedHistory).values(
            bot_id=bot_id,
            id=new_id,
            user_id=self.author_id,
            message_text=self.text,
            message_photo=self.images,
            mention_link=self.mention_link,
            packet_type=typeid,
        ).returning(PostedHistory.id)
        res = await session.execute(stmt)
        await session.commit()
        return res.scalar()