from aiogram import  Bot
from datetime import datetime
from configs import config
from src.keyboards import Keyboard
from shared.user_packet import AssignedPacketInfo
from zoneinfo import ZoneInfo


class NotifyManager:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_packet_assigned(self, user_id: int, assigned_packet: AssignedPacketInfo):
        if assigned_packet.activated_at > datetime.now():
            txt = config.success_bought_packet % (assigned_packet.packet_name, assigned_packet.activated_at)
            keyboard = Keyboard.activate_packet_menu(packet_id=assigned_packet.user_packet_id)
        else:
            txt = config.success_prolonged_packet % (assigned_packet.packet_name, assigned_packet.ending_at)
            keyboard = Keyboard.create_auto()

        await self.bot.send_message(chat_id=user_id, text=txt, parse_mode='html', reply_markup=keyboard)
