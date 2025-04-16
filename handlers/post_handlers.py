import re
import datetime
from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    Message,
    InputMediaPhoto,
    InputMediaVideo
)
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from configs import config
from src.keyboards import Keyboard
from src.states import AutoPostStates, PostStates
from shared.pricelist import PriceList
from shared.user import BalanceManager, UserManager
from shared.user_packet import PacketManager
from shared.post.post import AutoPost, Post
from aiogram.types import ReplyKeyboardRemove

from .callback_handlers import back_menu

router = Router()

TIME_PATTERN = re.compile(r'\d{1,2}[:.]\d{2}(?:\s*,\s*\d{1,2}[:.]\d{2})*')


async def check_caption_length(message: Message, caption: str | None) -> bool:
    if caption and len(caption) > 450:
        await message.answer("Ошибка. Введите текст до 450 символов")
        return False
    return True


def validate_time_format(time_text: str) -> bool:
    """Возвращает True, если строка соответствует паттерну времени."""
    return bool(TIME_PATTERN.match(time_text))


async def send_time_error(message, error_text, time_count):
    error_text += await get_time_message(time_count=time_count)
    await message.answer(text=error_text, parse_mode='html')


async def get_message_id_list(sended_message):
    bot_msg_id_list = []
    if isinstance(sended_message, list):
        for msg in sended_message:
            bot_msg_id_list.append(msg.message_id)
    else:
        bot_msg_id_list = [sended_message.message_id]
    return bot_msg_id_list


async def get_media_from_album(album, caption):
    media_group, file_ids = [], []

    for i, msg in enumerate(album[:config.max_image_count]):  # Ограничиваем до 5 файлов
        file_id = msg.photo[-1].file_id if msg.photo else msg.video.file_id
        file_ids.append(file_id)

        media = InputMediaPhoto(media=file_id, caption=caption) if msg.photo else InputMediaVideo(media=file_id,
                                                                                                  caption=caption)
        media_group.append(media if i == 0 else media.__class__(media=file_id))  # Только первый получает caption

    return media_group, file_ids


async def get_time_message(time_count: int) -> str:
    times = ['08:00', '09:30', '10:05', '11:20', '12:42', '13:00',
             '14:30', '15:10', '16:20', '17:40', '18:30', '19:05',
             '20:17', '21:33', '22:40', '23:02']

    times_string = ", ".join(times[:time_count])

    return (f"<b>Введите время по мск через запятую для {time_count} публикаций </b>\n\n"
            f"<code>Например: {times_string}</code>")


@router.message(PostStates.text)
async def create_post(
    message: Message,
    session: AsyncSession,
    album: list[Message] | None,
    caption: str | None,
    state: FSMContext
):
    """Получаем текст и фото для поста"""
    await state.clear()

    if not await check_caption_length(message, caption):
        return

    msg = await message.answer(text='ㅤ', reply_markup=ReplyKeyboardRemove())
    await msg.delete()

    media_group, file_ids = await get_media_from_album(album=album, caption=caption)
    if media_group:
        post = Post(
            text=caption,
            author_id=message.from_user.id,
            author_username=message.from_user.username,
            images=file_ids
        )

        post_id = await post.create(session=session)
        sended_message = await message.answer_media_group(media_group)
    else:
        post = Post(
            text=message.text,
            author_id=message.from_user.id,
            author_username=message.from_user.username,
            images=[]  # Нет фото
        )
        post_id = await post.create(session=session)
        sended_message = await message.answer(caption)

    bot_msg_id_list = await get_message_id_list(sended_message)
    await post.add_bot_message_id(bot_message_id_list=bot_msg_id_list, session=session)

    await message.answer(
        "Проверьте ваше объявление. Если все верно - нажмите кнопку опубликовать, и объявление попадет в чат.",
        reply_markup=Keyboard.post_onetime_menu(post_id=post_id)
    )


@router.message(AutoPostStates.text)
async def get_auto_post_text(
        message: Message,
        album: list[Message] | None,
        caption: str | None,
        state: FSMContext,
        session: AsyncSession
):
    if not await check_caption_length(message, caption):
        return

    media_group, file_ids = await get_media_from_album(album=album, caption=caption)
    time_count = await PacketManager.get_count_per_day(user_id=message.from_user.id, session=session)

    await state.update_data(text=caption,
                            images=file_ids,
                            media_group=media_group,
                            time_count=time_count)

    await state.set_state(AutoPostStates.time)
    text = await get_time_message(time_count)
    await message.answer(text, parse_mode='html')


@router.message(AutoPostStates.time)
async def create_auto_post(message: Message,
                           session: AsyncSession,
                           state: FSMContext):
    data = await state.get_data()
    text = data.get('text')
    file_ids = data.get('images')  # Исправлено: берём 'images', а не 'images_links'
    time_count = data.get('time_count')
    media_group = data.get('media_group')

    time_input = message.text.strip()
    if not validate_time_format(time_input):
        await send_time_error(message, "❌ Некорректный формат времени.\n\n", time_count)
        return

    times = [t.replace('.', ':') for t in time_input.split(',')]

    if len(times) != time_count:
        await send_time_error(message, f"❌ Ошибка. Введите {time_count} значений времени через запятую\n\n", time_count)
        return

    timestr = ', '.join(times)

    auto_post = AutoPost(
        text=text,
        images=file_ids,  # Исправлено: передаём file_ids, а не images_links
        times=times,
        author_id=message.from_user.id,
        author_username=message.from_user.username
    )
    post_id = await auto_post.create(session=session)

    if media_group:
        sended_message = await message.answer_media_group(media_group)
    else:
        sended_message = await message.answer(text)

    bot_msg_id_list = await get_message_id_list(sended_message)
    await auto_post.add_bot_message_id(bot_message_id_list=bot_msg_id_list, session=session)

    await message.answer(
        f'''Проверьте ваше объявление ⬆️\n\nВремя публикации {timestr}\n\n
Если все верно - нажмите кнопку "Включить публикацию".''',
        reply_markup=Keyboard.start_auto_posting(post_id=post_id)
    )

    await state.clear()


@router.message(AutoPostStates.new_time)
async def edit_time(message: Message,
                    session: AsyncSession,
                    state: FSMContext):
    data = await state.get_data()
    post_id = data.get('post_id')
    time_count = data.get('time_count')

    time_input = message.text.strip()

    if not validate_time_format(time_input):
        await send_time_error(message, "❌ Некорректный формат времени.\n\n", time_count)
        return

    times = [t.replace('.', ':') for t in time_input.split(',')]

    if len(times) != time_count:
        await send_time_error(message, f"❌ Ошибка. Введите {time_count} значений времени через запятую\n\n", time_count)
        return

    auto_post = await AutoPost.from_db(auto_post_id=post_id, session=session)
    await auto_post.update_time(times=times, session=session)

    await message.answer(config.success_time_change_text, reply_markup=Keyboard.main_menu())


@router.callback_query(F.data == 'create')
async def create_post_callback_handler(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Реакция на переход к размещению объявления"""
    has_balance, has_active_packet = await UserManager.get_posting_ability(
        user_id=call.from_user.id, session=session
    )
    if not has_balance and not has_active_packet:
        await call.message.edit_text(config.low_balance_text, reply_markup=Keyboard.price_menu())
        return

    if has_active_packet:
        await call.message.edit_text("Выберите тип объявления:", reply_markup=Keyboard.post_packet_menu())
        return
    await call.message.delete()
    await call.message.answer(
        "📄 Введите текст объявления (Можно прикрепить одно фото)",
        reply_markup=Keyboard.cancel_menu()
    )
    await state.set_state(PostStates.text)
    await call.answer()


@router.callback_query(F.data == 'create_hand')
async def create_hand_post(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("📄 Введите текст объявления (Можно прикрепить одно фото)",
                              reply_markup=Keyboard.cancel_menu())
    await state.set_state(PostStates.text)
    await call.answer()


@router.callback_query(F.data == 'create_auto')
async def create_auto_post(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    auto_post = await AutoPost.get_auto_post(user_id=call.from_user.id, session=session)
    if auto_post:
        await call.message.edit_text('У вас уже есть активная публикация')
        text = """Текст объявления:\n"""
        text += auto_post.text
        text += """\n\nВремя публикации:\n"""
        text += ", ".join(auto_post.times)

        keyboard = Keyboard.cancel_auto_posting(post_id=auto_post.id)
        if auto_post.images_links:
            if len(auto_post.images) == 1:
                await call.message.answer_photo(photo=auto_post.images_links[0],
                                                caption=text,
                                                reply_markup=keyboard,
                                                parse_mode='html')
            media_group = [
                InputMediaPhoto(media=file_id, caption=text if i == 0 else "", parse_mode='html')
                for i, file_id in enumerate(auto_post.images_links)
            ]
            await call.message.answer_media_group(media=media_group)

        await call.message.answer(text=text,
                                  reply_markup=keyboard,
                                  parse_mode='html',
                                  disable_web_page_preview=True)

    else:
        await call.message.delete()
        await call.message.answer("📄 Введите текст объявления (Можно прикрепить одно фото)",
                                  reply_markup=Keyboard.cancel_menu())
        await state.set_state(AutoPostStates.text)
    await call.answer()


@router.callback_query(F.data == "recreate_auto")
async def recreate_auto(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("📄 Введите текст объявления (Можно прикрепить одно фото)",
                              reply_markup=Keyboard.cancel_menu())
    await state.set_state(AutoPostStates.text)
    await call.answer()


@router.callback_query(F.data.startswith("change_time_autopost_id"))
async def change_time_auto_post(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    post_id = int(call.data.split('=')[1])
    await call.message.delete()

    time_count = await PacketManager.get_count_per_day(user_id=call.from_user.id, session=session)
    text = await get_time_message(time_count)
    await state.update_data(post_id=post_id, time_count=time_count)
    await call.message.answer(text, reply_markup=Keyboard.cancel_menu(), parse_mode='html')
    await state.set_state(AutoPostStates.new_time)
    await call.answer()


@router.callback_query(F.data.startswith("cancel_autopost_id"))
async def delete_auto_post(call: CallbackQuery, session: AsyncSession):
    post_id = int(call.data.split('=')[1])
    auto_post = await AutoPost.from_db(auto_post_id=post_id, session=session)
    await auto_post.delete(session=session)

    for bot_message_id in auto_post.bot_message_id_list:
        try:
            await call.bot.delete_message(call.message.chat.id, bot_message_id)
        except Exception as e:
            print(e)
    await back_menu(call=call, session=session)
    await call.answer()


@router.callback_query(F.data.startswith("edit_autopost_id"))
async def edit_auto_post(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    post_id = int(call.data.split('=')[1])
    auto_post = await AutoPost.from_db(auto_post_id=post_id, session=session)
    await auto_post.delete(session=session)

    for bot_message_id in auto_post.bot_message_id_list:
        try:
            await call.bot.delete_message(call.message.chat.id, bot_message_id)
        except Exception as e:
            print(e)
    if state:
        await state.clear()
    await create_auto_post(call=call, state=state, session=session)
    await call.answer()


@router.callback_query(F.data.startswith("start_autopost_id"))
async def start_auto_post(call: CallbackQuery, session: AsyncSession):
    post_id = int(call.data.split('=')[1])
    auto_post = await AutoPost.from_db(auto_post_id=post_id, session=session)
    await auto_post.activate(session=session)

    for bot_message_id in auto_post.bot_message_id_list:
        try:
            await call.bot.delete_message(call.message.chat.id, bot_message_id)
        except Exception as e:
            print(e)
    times = ','.join(auto_post.times)
    packet_ending_date = await PacketManager.get_packet_ending_date(user_id=call.from_user.id, session=session)
    packet_ending_date = datetime.datetime.strftime(packet_ending_date[0], "%d.%m.%Y")
    text = config.success_auto_posted_text % (times, packet_ending_date)
    await call.message.edit_text(text, reply_markup=Keyboard.main_menu())
    await call.answer()


@router.callback_query(F.data.startswith("post_onetime_id"))
async def post_onetime_wrapper(call: CallbackQuery, session: AsyncSession):
    post_id = int(call.data.split('=')[1])
    await handle_post_onetime(call=call, post_id=post_id, session=session, force_balance=False)


@router.callback_query(F.data.startswith("post_onetime_balance_id"))
async def post_onetime_balance_wrapper(call: CallbackQuery, session: AsyncSession):
    post_id = int(call.data.split('=')[1])
    await handle_post_onetime(call=call, post_id=post_id, session=session, force_balance=True)


async def handle_post_onetime(call: CallbackQuery, post_id: int, session: AsyncSession, force_balance: bool = False):
    user_id = call.from_user.id
    use_balance = force_balance

    if not force_balance and await PacketManager.has_active_packet(user_id=user_id, session=session):
        today_limit = await PacketManager.get_today_limit(user_id=user_id, session=session)
        if today_limit <= 0:
            await call.message.edit_text(
                config.limit_exceeded_text,
                reply_markup=Keyboard.post_onetime_from_balance(post_id=post_id)
            )
            return
        # Лимит есть — постим без использования баланса
    else:
        use_balance = True

    if use_balance:
        price = (await PriceList.get_onetime_price(session=session))[0].price
        balance = await BalanceManager.get_balance(user_id=user_id, session=session)
        if balance < price:
            await call.message.edit_text(config.low_balance_text, reply_markup=Keyboard.price_menu())
            return

    await post_onetime(call=call, post_id=post_id, session=session)
    await call.answer()


async def post_onetime(call: CallbackQuery, post_id: int, session: AsyncSession):
    post = await Post.from_db(post_id=post_id, session=session)
    print(post)
    sended = await post.post(bot=call.bot, session=session)
    print(sended)
    if sended:
        for bot_message_id in post.bot_message_id_list:
            await call.bot.delete_message(call.message.chat.id, bot_message_id)
        await call.message.edit_text(config.success_posted_text, reply_markup=Keyboard.main_menu())
    else:
        await call.message.edit_text(config.low_balance_text, reply_markup=Keyboard.price_menu())


@router.callback_query(F.data.startswith("edit_post_id"))
async def edit_post(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    post_id = int(call.data.split('=')[1])
    post = await Post.from_db(post_id=post_id, session=session)
    await post.delete(session=session)
    for bot_message_id in post.bot_message_id_list:
        await call.bot.delete_message(call.message.chat.id, bot_message_id)
    await create_post_callback_handler(call=call, state=state, session=session)


@router.callback_query(F.data.startswith("cancel_post_id"))
async def cancel_post(call: CallbackQuery, session: AsyncSession):
    post_id = int(call.data.split('=')[1])
    post = await Post.from_db(post_id=post_id, session=session)
    await post.delete(session=session)

    for bot_message_id in post.bot_message_id_list:
        await call.bot.delete_message(call.message.chat.id, bot_message_id)
    await back_menu(call=call, session=session)
    await call.answer()