import asyncio
from typing import Callable, Any, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src.states import PostStates  # Импортируем состояние
from src.states import AutoPostStates


class AlbumMiddleware(BaseMiddleware):
    def __init__(self, latency: Union[int, float] = 1):
        self.latency = latency
        self.album_data: dict[str, list[Message]] = {}
        self.album_caption: dict[str, str] = {}

    async def __call__(
            self,
            handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
            message: Message,
            data: dict[str, Any]
    ) -> Any:
        state: FSMContext = data.get("state")  # Получаем состояние пользователя
        if not state:
            return await handler(message, data)

        current_state = await state.get_state()
        print(current_state)
        if current_state != PostStates.text and current_state != AutoPostStates.text:
            return await handler(message, data)

        if not message.media_group_id:
            data["album"] = [message] if message.photo else []
            data["caption"] = message.caption or message.text or ""
            return await handler(message, data)

        self.album_data.setdefault(message.media_group_id, []).append(message)

        if message.caption:
            self.album_caption[message.media_group_id] = message.caption

        await asyncio.sleep(self.latency)

        if message.media_group_id in self.album_data:
            data["album"] = self.album_data.pop(message.media_group_id)
            data["caption"] = self.album_caption.pop(message.media_group_id, "")
            print(data['album'])
            return await handler(message, data)