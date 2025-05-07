from aiogram.types import (
    CallbackQuery,
    Message,
)
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from configs import config
from src.keyboards import Keyboard
from src.states import PostStates
from shared.pricelist import PriceList
from shared.user import BalanceManager
from shared.user_packet import PacketManager
from shared.post.post import Post
from aiogram.types import ReplyKeyboardRemove

from handlers.callback_handlers import back_menu
from shared.bot_config import BotConfig
from aiogram.types import InputMediaPhoto
import shared.post.utils as post_utils
from handlers.callback_handlers import create_post_callback_handler


async def create_post(message: Message, session: AsyncSession, album: list[Message] | None, caption: str | None, state: FSMContext, bot_config: BotConfig):
    """Получаем текст и фото для поста"""
    await state.clear()

    if not await post_utils.check_caption_length(message, caption):
        return

    msg = await message.answer(text='ㅤ', reply_markup=ReplyKeyboardRemove())
    await msg.delete()

    media_group, file_ids = await post_utils.get_media_from_album(album=album, caption=caption)
    if media_group:
        post = Post(
            bot_config=bot_config,
            text=caption,
            author_id=message.from_user.id,
            author_username=message.from_user.username,
            images=file_ids
        )

        post_id = await post.create(session=session)
        sended_message = await message.answer_media_group(media_group)
    else:
        post = Post(
            bot_config=bot_config,
            text=message.text,
            author_id=message.from_user.id,
            author_username=message.from_user.username,
            images=[]  # Нет фото
        )
        post_id = await post.create(session=session)
        sended_message = await message.answer(caption)

    bot_msg_id_list = await post_utils.get_message_id_list(sended_message)
    await post.add_bot_message_id(bot_message_id_list=bot_msg_id_list, session=session)

    await message.answer(
        "Проверьте ваше объявление. Если все верно - нажмите кнопку опубликовать, и объявление попадет в чат.",
        reply_markup=Keyboard.post_onetime_menu(post_id=post_id)
    )


async def create_hand_post(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("📄 Введите текст объявления (Можно прикрепить одно фото)",
                              reply_markup=Keyboard.cancel_menu())
    await state.set_state(PostStates.text)
    await call.answer()


async def post_onetime_wrapper(call: CallbackQuery, session: AsyncSession, bot_config: BotConfig):
    post_id = int(call.data.split('=')[1])
    await handle_post_onetime(call=call, post_id=post_id, session=session, bot_config=bot_config, use_balance=False)


async def post_onetime_balance_wrapper(call: CallbackQuery, session: AsyncSession, bot_config: BotConfig):
    post_id = int(call.data.split('=')[1])
    await handle_post_onetime(call=call, post_id=post_id, session=session, bot_config=bot_config, use_balance=True)


async def handle_post_onetime(call: CallbackQuery, post_id: int, session: AsyncSession, bot_config: BotConfig, use_balance: bool = False):
    user_id = call.from_user.id
    use_balance = use_balance

    if not use_balance and await PacketManager.has_active_packet(user_id=user_id, session=session):
        today_limit = await PacketManager.get_today_limit(user_id=user_id, session=session)
        if today_limit <= 0:
            await call.message.edit_text(config.limit_exceeded_text, reply_markup=Keyboard.post_onetime_from_balance(post_id=post_id))
            return
    else:
        use_balance = True

    if use_balance:
        price = (await PriceList.get_onetime_price(session=session))[0].price
        balance = await BalanceManager.get_balance(user_id=user_id, session=session)
        if balance < price:
            await call.message.edit_text(config.low_balance_text, reply_markup=Keyboard.price_menu())
            return
    await post_onetime(call=call, post_id=post_id, session=session, bot_config=bot_config)
    await call.answer()


async def post_onetime(call: CallbackQuery, post_id: int, session: AsyncSession, bot_config: BotConfig):
    post = await Post.from_db(post_id=post_id, session=session, bot_config=bot_config)
    sended = await post.post(bot=call.bot, session=session)
    if sended:
        for bot_message_id in post.bot_message_id_list:
            await call.bot.delete_message(call.message.chat.id, bot_message_id)
        await call.message.edit_text(config.success_posted_text, reply_markup=Keyboard.main_menu())
    else:
        await call.message.edit_text(config.low_balance_text, reply_markup=Keyboard.price_menu())


async def edit_post(call: CallbackQuery, session: AsyncSession, state: FSMContext, bot_config: BotConfig):
    post_id = int(call.data.split('=')[1])
    post = await Post.from_db(post_id=post_id, session=session, bot_config=bot_config)
    await post.delete(session=session)
    for bot_message_id in post.bot_message_id_list:
        await call.bot.delete_message(call.message.chat.id, bot_message_id)
    await create_post_callback_handler(call=call, state=state, session=session)


async def cancel_post(call: CallbackQuery, session: AsyncSession, bot_config: BotConfig):
    post_id = int(call.data.split('=')[1])
    post = await Post.from_db(post_id=post_id, session=session, bot_config=bot_config)
    await post.delete(session=session)

    for bot_message_id in post.bot_message_id_list:
        await call.bot.delete_message(call.message.chat.id, bot_message_id)
    await back_menu(call=call, session=session, bot_config=bot_config)
    await call.answer()