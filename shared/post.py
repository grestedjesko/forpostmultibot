import datetime
from typing import List, Optional
from database.models.created_posts import CreatedPosts
from database.models.auto_posts import AutoPosts
from database.models.users import User
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.posted_history import PostedHistory
from database.models.shcedule import Schedule
import config
from aiogram.types import InputMediaPhoto
from aiogram import Bot
from shared.user import BalanceManager
from shared.pricelist import PriceList

class Post:
    def __init__(self,
                 text: str,
                 author_id: int,
                 author_username: str,
                 images: list | None = None,
                 bot_message_id_list: list | None = None,
                 post_id: int | None = None):
        """Инициализация поста"""
        self.text = text
        self.images = images
        self.author_id = author_id
        self.bot_message_id_list = bot_message_id_list
        self.post_id = post_id
        self.author_username = author_username

    @classmethod
    async def from_db(cls, post_id: int, session: AsyncSession):
        """Создание объекта Post из базы данных"""
        stmt = (
            sa.select(CreatedPosts, User.username)
            .join(User, CreatedPosts.user_id == User.telegram_user_id)
            .where(CreatedPosts.id == post_id)
        )
        result = await session.execute(stmt)
        row = result.first()
        if row:
            created_post, username = row
            return cls(
                post_id=created_post.id,
                text=created_post.text,
                author_id=created_post.user_id,
                author_username=username,
                images=created_post.images_links,
                bot_message_id_list=created_post.bot_message_id_list
            )
        return None

    async def create(self, session: AsyncSession):
        """Создание поста"""
        stmt = (
            sa.insert(CreatedPosts)
            .values(
                user_id=self.author_id,
                text=self.text.encode('utf-8'),
                images_links=self.images
            )
            .returning(CreatedPosts.id)
        )
        result = await session.execute(stmt)
        self.post_id = result.scalar_one_or_none()
        await session.commit()
        return self.post_id

    async def delete(self, session: AsyncSession):
        """Удаление поста из базы данных"""
        await session.execute(
            sa.delete(CreatedPosts).where(CreatedPosts.id == self.post_id)
        )
        await session.commit()

    async def send(self, bot: Bot, session: AsyncSession):
        """Отправка поста в чат"""
        price = (await PriceList().get_onetime_price(session=session))[0].price
        success = await BalanceManager.deduct(self.author_id, price, session)

        if success:
            message_id = await self.post_to_chat(bot)
            if isinstance(message_id, list):
                message_id = message_id[0]
            else:
                message_id = message_id.message_id

            await self.set_post_sended(
                message_id=message_id, link="t.me/username", hash_link="sellect.ru/sss", session=session
            )
            return True
        return False

    async def post_to_chat(self, bot: Bot):
        """Публикация поста в чат"""
        if self.images:
            media_group = [
                InputMediaPhoto(media=file_id, caption=self.text if i == 0 else "")
                for i, file_id in enumerate(self.images)
            ]
            return await bot.send_media_group(chat_id=config.chat_id, media=media_group)

        if self.text:
            return await bot.send_message(chat_id=config.chat_id, text=self.text)

        raise ValueError("Нет данных для отправки: ни текста, ни медиа.")

    async def set_post_sended(self, message_id: int, link: str, hash_link: str, session: AsyncSession):
        """Сохранение информации о размещенном посте"""
        stmt = sa.insert(PostedHistory).values(
            user_id=self.author_id,
            message_id=message_id,
            message_text=self.text,
            message_photo=self.images,
            link=link,
            hash_link=hash_link
        )
        await session.execute(stmt)
        await self.delete(session)

    async def add_bot_message_id(self, bot_message_id_list: list, session: AsyncSession):
        """Добавление ID сообщений бота в базу"""
        stmt = (
            sa.update(CreatedPosts)
            .where(CreatedPosts.id == self.post_id)
            .values(bot_message_id_list=bot_message_id_list)
        )
        await session.execute(stmt)
        await session.commit()


class AutoPost:
    def __init__(self,
                 text: str,
                 author_id: int,
                 author_username: str,
                 times: list[datetime.time]|None = None,
                 images: list | None = None,
                 bot_message_id_list: list | None = None,
                 auto_post_id: int | None = None):
        self.text = text
        self.images = images
        self.times = times
        self.author_id = author_id
        self.bot_message_id_list = bot_message_id_list
        self.auto_post_id = auto_post_id
        self.author_username = author_username

    @classmethod
    async def from_db(cls, auto_post_id: int, session: AsyncSession):
        """Создание объекта AutoPost из базы данных"""
        stmt = (
            sa.select(AutoPosts, User.username)
            .join(User, AutoPosts.user_id == User.telegram_user_id)
            .where(AutoPosts.id == auto_post_id)
        )
        result = await session.execute(stmt)
        row = result.first()

        if row:
            auto_post, username = row
            return cls(
                auto_post_id=auto_post.id,
                text=auto_post.text,
                images=auto_post.images_links,
                times=auto_post.times,
                author_id=auto_post.user_id,
                author_username=username,
                bot_message_id_list=auto_post.bot_message_id_list,
            )
        return None

    async def create(self, session: AsyncSession):
        """Создание автопоста в базе данных"""
        stmt = (
            sa.insert(AutoPosts)
            .values(
                user_id=self.author_id,
                text=self.text.encode("utf-8"),
                images_links=self.images,
                times=self.times,
                activated=0
            )
            .returning(AutoPosts.id)
        )

        result = await session.execute(stmt)
        self.auto_post_id = result.scalar_one_or_none()
        await session.commit()
        return self.auto_post_id

    async def delete(self, session: AsyncSession):
        """Удаление автопоста"""
        await session.execute(
            sa.delete(AutoPosts).where(AutoPosts.id == self.auto_post_id)
        )
        await session.commit()

    async def delete_active(self, session: AsyncSession):
        """Удаление активных автопостов пользователя"""
        await session.execute(
            sa.delete(AutoPosts).where(AutoPosts.user_id == self.author_id, AutoPosts.activated == 1)
        )
        await session.commit()

    async def activate(self, session: AsyncSession):
        """Активация автопоста"""
        await self.delete_active(session)
        await session.execute(
            sa.update(AutoPosts).values(activated=1).where(AutoPosts.id == self.auto_post_id)
        )

        for time in self.times:
            time_parsed = datetime.datetime.strptime(time.strip(), "%H:%M")
            completed = 0
            if time_parsed <= datetime.datetime.now():
                completed = 1

            stmt = sa.insert(Schedule).values(
                user_id=self.author_id,
                scheduled_post_id=self.auto_post_id,
                time=time_parsed,
                completed=completed
            )
            await session.execute(stmt)
        await session.commit()

    async def add_bot_message_id(self, bot_message_id_list: list, session: AsyncSession):
        stmt = sa.update(AutoPosts).where(AutoPosts.id == self.auto_post_id).values(
            bot_message_id_list=bot_message_id_list)
        await session.execute(stmt)
        await session.commit()

    async def post_to_chat(self, bot: Bot):
        """Публикация поста в чат"""
        if self.images:
            media_group = [
                InputMediaPhoto(media=file_id, caption=self.text if i == 0 else "")
                for i, file_id in enumerate(self.images)
            ]
            return await bot.send_media_group(chat_id=config.chat_id, media=media_group)

        if self.text:
            return await bot.send_message(chat_id=config.chat_id, text=self.text)

        raise ValueError("Нет данных для отправки: ни текста, ни медиа.")