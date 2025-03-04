from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import post_emoji_1, support_link

class Keyboard:
    @staticmethod
    def first_keyboard() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="🔖 Тарифы", callback_data="price"),
             InlineKeyboardButton(text="💸 Пополнить баланс", callback_data="upbalance")],
            [InlineKeyboardButton(text=f"{post_emoji_1} Разместить объявление", callback_data="create")],
            [InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
             InlineKeyboardButton(text="Тех. поддержка", url=support_link)]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def balance_menu():
        keyboard = [
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="upbalance")],
            [InlineKeyboardButton(text='Назад', callback_data="back")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def price_menu():
        keyboard = [
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="upbalance")],
            [InlineKeyboardButton(text="🛍 Купить пакет", callback_data="buypacket")],
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def post_packet_menu():
        keyboard = [
            [InlineKeyboardButton(text='⌨ Ручная публикация', callback_data='create_hand')],
            [InlineKeyboardButton(text='⚙ Авторазмещение', callback_data='create_auto')],
            [InlineKeyboardButton(text='Назад', callback_data='back')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def cancel_menu():
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='❌ Отмена')]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

    @staticmethod
    def post_onetime_menu(post_id):
        keyboard = [
            [InlineKeyboardButton(text="💬 Опубликовать", callback_data=f'post_onetime_id={post_id}')],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f'cancel_post_id={post_id}'),
             InlineKeyboardButton(text="✏️ Редактировать", callback_data=f'edit_post_id={post_id}')],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def payment_keyboard(link):
        keyboard = [
            [InlineKeyboardButton(text="💳 Оплатить", url=link)],
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data='back')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def start_auto_posting(post_id):
        keyboard = [
            [InlineKeyboardButton(text="⚡️ Включить автопубликацию", callback_data=f'start_autopost_id={post_id}')],
            [InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit_autopost_id={post_id}")],
            [InlineKeyboardButton(text="❌ В главное меню", callback_data=f"cancel_autopost_id={post_id}")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_packets_keyboard(packets_list: list):
        builder = InlineKeyboardBuilder()
        for packet in packets_list:
            if packet.id == 1:
                continue

            button_title = packet.button_title
            if not button_title:
                button_title = packet.name
            builder.add(InlineKeyboardButton(text=button_title, callback_data=f"buy_packet_id={packet.id}"))

        builder.add(InlineKeyboardButton(text='Назад', callback_data='price'))
        builder.adjust(1)
        return builder.as_markup()