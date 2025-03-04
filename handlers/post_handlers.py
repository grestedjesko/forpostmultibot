from aiogram import F
from aiogram.types import CallbackQuery
from aiogram import Router
from aiogram.types import Message, InputMediaPhoto, InputMediaVideo
from aiogram.fsm.context import FSMContext
from src.keyboards import Keyboard
from sqlalchemy.ext.asyncio import AsyncSession
import re
from shared.user import PacketManager
from shared.post import AutoPost
from shared.post import Post

from src.states import AutoPostStates
from src.states import PostStates
from .callback_handlers import back_menu

router = Router()

TIME_PATTERN = re.compile(r'\d{1,2}[:.]\d{2}(?:\s*,\s*\d{1,2}[:.]\d{2})*')

def validate_time_format(time_text: str) -> bool:
    """Проверяет, соответствует ли строка формату времени HH:MM или HH.MM"""
    return bool(TIME_PATTERN.match(time_text))

async def send_time_error(message, error_text, time_count):
    error_text += await get_time_message(time_count=time_count)
    await message.answer(text=error_text, parse_mode='html')

async def get_messge_id_list(sended_message):
    bot_msg_id_list = []
    if isinstance(sended_message, list):
        for msg in sended_message:
            bot_msg_id_list.append(msg.message_id)
    else:
        bot_msg_id_list = [sended_message.message_id]
    return bot_msg_id_list

async def get_media_from_album(album, caption):
    media_group = []
    file_ids = []
    for msg in album:
        if msg.photo:
            file_id = msg.photo[-1].file_id
            if len(media_group) == 0:
                media_group.append(InputMediaPhoto(media=file_id, caption=caption))
            else:
                media_group.append(InputMediaPhoto(media=file_id))
            file_ids.append(file_id)
        elif msg.video:
            file_id = msg.video.file_id
            if len(media_group) == 0:
                media_group.append(InputMediaVideo(media=file_id, caption=caption))
            else:
                media_group.append(InputMediaVideo(media=file_id))
            file_ids.append(file_id)
        if len(media_group) >= 5:
            break
    return [media_group, file_ids]

async def get_time_message(time_count: int):
    times = ['08:00', '09:30', '10:05', '11:20', '12:42', '13:00', '14:30', '15:10', '16:20', '17:40',
             '18:30', '19:05', '20:17', '21:33', '22:40', '23:02']
    times_string = ''
    for i in range(time_count):
        times_string += times[i]
        if i != time_count - 1:
            times_string += ', '

    text = f"""<b>Введите время по мск через запятую
для {time_count} публикаций </b>

<code>Например: {times_string}</code>"""
    return text


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

    if caption and len(caption) > 450:
        await message.answer('Ошибка. Максимальная длина текста объявления - 450 символов')
        return

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

    bot_msg_id_list = await get_messge_id_list(sended_message)
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
    if caption and len(caption) > 450:
        await message.answer('Ошибка. Максимальная длина текста объявления - 450 символов')
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

    if len(times) < time_count:
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

    bot_msg_id_list = await get_messge_id_list(sended_message)
    await auto_post.add_bot_message_id(bot_message_id_list=bot_msg_id_list, session=session)

    await message.answer(
        f'Проверьте ваше объявление ⬆️\n\n Время публикации {timestr}\n\n Если все верно - нажмите кнопку "Включить публикацию".',
        reply_markup=Keyboard.start_auto_posting(post_id=post_id)
    )

    await state.clear()


@router.callback_query(F.data == 'create')
async def create_post_callback_handler(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Реакция на переход к размещению объявления"""
    has_active_packet = await PacketManager.has_active_packet(user_id=call.from_user.id, session=session)
    has_active_packet = True  # remove
    if has_active_packet:
        await call.message.edit_text("Выберите тип объявления:", reply_markup=Keyboard.post_packet_menu())
    else:
        await call.message.delete()
        await call.message.answer("📄 Введите текст объявления (Можно прикрепить одно фото)",
                                        reply_markup=Keyboard.cancel_menu())
        await state.set_state(PostStates.text)


@router.callback_query(F.data == 'create_hand')
async def create_hand_post(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("📄 Введите текст объявления (Можно прикрепить одно фото)",
                                    reply_markup=Keyboard.cancel_menu())
    await state.set_state(PostStates.text)


@router.callback_query(F.data == 'create_auto')
async def create_auto_post(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("📄 Введите текст объявления (Можно прикрепить одно фото)",
                                    reply_markup=Keyboard.cancel_menu())
    await state.set_state(AutoPostStates.text)


@router.callback_query(F.data.split('=')[0] == 'cancel_autopost_id')
async def delete_auto_post(call: CallbackQuery, session: AsyncSession):
    post_id = int(call.data.split('=')[1])
    auto_post = await AutoPost.from_db(auto_post_id=post_id, session=session)
    await auto_post.delete(session=session)

    for bot_message_id in auto_post.bot_message_id_list:
        try:
            await call.bot.delete_message(call.message.chat.id, bot_message_id)
        except:
            print('not deleted')

    await back_menu(call=call)


@router.callback_query(F.data.split('=')[0] == 'edit_autopost_id')
async def edit_auto_post(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    post_id = int(call.data.split('=')[1])
    auto_post = await AutoPost.from_db(auto_post_id=post_id, session=session)
    await auto_post.delete(session=session)

    for bot_message_id in auto_post.bot_message_id_list:
        try:
            await call.bot.delete_message(call.message.chat.id, bot_message_id)
        except:
            print('not deleted')

    if state:
        await state.clear()

    await create_auto_post(call=call, state=state)


@router.callback_query(F.data.split('=')[0] == 'start_autopost_id')
async def start_auto_post(call: CallbackQuery, session: AsyncSession):
    post_id = int(call.data.split('=')[1])
    auto_post = await AutoPost.from_db(auto_post_id=post_id, session=session)
    await auto_post.activate(session=session)

    for bot_message_id in auto_post.bot_message_id_list:
        try:
            await call.bot.delete_message(call.message.chat.id, bot_message_id)
        except:
            print('not deleted')

    await call.message.edit_text('Автопубликация включена')


@router.callback_query((F.data.split('=')[0] == 'post_onetime_id') | (
F.data.in_({'send_text_1', 'send_photo_1', 'send_handtext', 'send_handtext_photo'})))
async def send_post(call: CallbackQuery, session: AsyncSession):
    bot = call.bot
    post_id = int(call.data.split('=')[1])
    post = await Post.from_db(post_id=post_id, session=session)
    sended = await post.send(bot=bot, session=session)
    if sended:
        for bot_message_id in post.bot_message_id_list:
            await call.bot.delete_message(call.message.chat.id, bot_message_id)
        await call.message.delete()
    else:
        await call.answer('Недостаточно средств', show_alert=True)


@router.callback_query(F.data.split('=')[0] == 'edit_post_id')
async def edit_post(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    post_id = int(call.data.split('=')[1])
    post = await Post.from_db(post_id=post_id, session=session)
    await post.delete(session=session)

    for bot_message_id in post.bot_message_id_list:
        await call.bot.delete_message(call.message.chat.id, bot_message_id)

    await create_post_callback_handler(call=call, state=state)


@router.callback_query(F.data.split('=')[0] == 'cancel_post_id')
async def cancel_post(call: CallbackQuery, session: AsyncSession):
    post_id = int(call.data.split('=')[1])
    post = await Post.from_db(post_id=post_id, session=session)
    await post.delete(session=session)

    for bot_message_id in post.bot_message_id_list:
        await call.bot.delete_message(call.message.chat.id, bot_message_id)
    await back_menu(call=call)
