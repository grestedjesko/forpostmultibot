from aiogram.types import (
    CallbackQuery,
    Message,
)
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from configs import config
from src.keyboards import Keyboard
from shared.user_packet import PacketManager
import re
from handlers.callback_handlers import back_menu
from src.states import AutoPostStates
from shared.bot_config import BotConfig
import datetime
from shared.post.post import AutoPost
import shared.post.utils as post_utils
from aiogram.types import InputMediaPhoto


TIME_PATTERN = re.compile(r'\d{1,2}[:.]\d{2}(?:\s*,\s*\d{1,2}[:.]\d{2})*')


async def get_time_message(time_count: int) -> str:
    times = ['08:00', '09:30', '10:05', '11:20', '12:42', '13:00',
             '14:30', '15:10', '16:20', '17:40', '18:30', '19:05',
             '20:17', '21:33', '22:40', '23:02']

    times_string = ", ".join(times[:time_count])

    return (f"<b>Введите время по мск через запятую для {time_count} публикаций </b>\n\n"
            f"<code>Например: {times_string}</code>")


def validate_time_format(time_text: str) -> bool:
    """Возвращает True, если строка соответствует паттерну времени."""
    return bool(TIME_PATTERN.match(time_text))


async def send_time_error(message, error_text, time_count):
    error_text += await get_time_message(time_count=time_count)
    await message.answer(text=error_text, parse_mode='html')


async def get_auto_post_text(message: Message, album: list[Message] | None, caption: str | None, state: FSMContext, session: AsyncSession):
    if not await post_utils.check_caption_length(message, caption):
        return

    media_group, file_ids = await post_utils.get_media_from_album(album=album, caption=caption)
    time_count = await PacketManager.get_count_per_day(user_id=message.from_user.id, session=session)

    await state.update_data(text=caption,
                            images=file_ids,
                            media_group=media_group,
                            time_count=time_count)

    await state.set_state(AutoPostStates.time)
    text = await get_time_message(time_count)
    await message.answer(text, parse_mode='html')


async def create_auto_post_time(message: Message,
                                session: AsyncSession,
                                state: FSMContext,
                                bot_config: BotConfig):
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
        author_username=message.from_user.username,
        bot_config=bot_config
    )
    post_id = await auto_post.create(session=session)

    if media_group:
        sended_message = await message.answer_media_group(media_group)
    else:
        sended_message = await message.answer(text)

    bot_msg_id_list = await post_utils.get_message_id_list(sended_message)
    await auto_post.add_bot_message_id(bot_message_id_list=bot_msg_id_list, session=session)

    await message.answer(
        f'''Проверьте ваше объявление ⬆️\n\nВремя публикации {timestr}\n\n
Если все верно - нажмите кнопку "Включить публикацию".''',
        reply_markup=Keyboard.start_auto_posting(post_id=post_id)
    )

    await state.clear()


async def edit_time(message: Message,
                    session: AsyncSession,
                    state: FSMContext,
                    bot_config: BotConfig):
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

    auto_post = await AutoPost.from_db(auto_post_id=post_id, session=session, bot_config=bot_config)
    await auto_post.update_time(times=times, session=session)

    await message.answer(config.success_time_change_text, reply_markup=Keyboard.main_menu())


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
            if len(auto_post.images_links) == 1:
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


async def recreate_auto(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("📄 Введите текст объявления (Можно прикрепить одно фото)",
                              reply_markup=Keyboard.cancel_menu())
    await state.set_state(AutoPostStates.text)
    await call.answer()


async def change_time_auto_post(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    post_id = int(call.data.split('=')[1])
    await call.message.delete()

    time_count = await PacketManager.get_count_per_day(user_id=call.from_user.id, session=session)
    text = await get_time_message(time_count)
    await state.update_data(post_id=post_id, time_count=time_count)
    await call.message.answer(text, reply_markup=Keyboard.cancel_menu(), parse_mode='html')
    await state.set_state(AutoPostStates.new_time)
    await call.answer()


async def delete_auto_post(call: CallbackQuery, session: AsyncSession, bot_config: BotConfig):
    post_id = int(call.data.split('=')[1])
    auto_post = await AutoPost.from_db(auto_post_id=post_id, session=session, bot_config=bot_config)
    await auto_post.delete(session=session)
    for bot_message_id in auto_post.bot_message_id_list:
        try:
            await call.bot.delete_message(call.message.chat.id, bot_message_id)
        except Exception as e:
            print(e)
    await back_menu(call=call, session=session, bot_config=bot_config)
    await call.answer()


async def edit_auto_post(call: CallbackQuery, session: AsyncSession, state: FSMContext, bot_config: BotConfig):
    post_id = int(call.data.split('=')[1])
    auto_post = await AutoPost.from_db(auto_post_id=post_id, session=session, bot_config=bot_config)
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


async def start_auto_post(call: CallbackQuery, session: AsyncSession, bot_config: BotConfig):
    post_id = int(call.data.split('=')[1])
    auto_post = await AutoPost.from_db(auto_post_id=post_id, session=session, bot_config=bot_config)
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
