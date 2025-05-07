from aiogram.types import (
    InputMediaPhoto,
    InputMediaVideo,
    Message
)
from configs import config


async def check_caption_length(message: Message, caption: str | None) -> bool:
    if caption and len(caption) >= 500:
        await message.answer(f"Ошибка. Введите текст до 450 символов ({len(caption)})")
        return False
    return True


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

