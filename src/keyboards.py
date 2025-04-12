from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from configs.config import post_emoji_1, support_link
from configs import config


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
    def price_menu():
        keyboard = [
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="upbalance")],
            [InlineKeyboardButton(text="🛍 Купить пакет", callback_data="buy_packet")],
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
    def post_onetime_from_balance(post_id):
        keyboard = [
            [InlineKeyboardButton(text="💬 Опубликовать", callback_data=f'post_onetime_balance_id={post_id}')],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f'cancel_post_id={post_id}')]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


    @staticmethod
    def payment_keyboard(link):
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="💳 Оплатить", url=link))
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def payment_yookassa_keyboard(link, payment_id):
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="💳 Оплатить", url=link))
        builder.add(InlineKeyboardButton(text='✅ Перевод выполнен', callback_data='check_yookassa_id='+str(payment_id)))
        builder.add(InlineKeyboardButton(text="🔙 В главное меню", callback_data='back'))
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def start_auto_posting(post_id):
        keyboard = [
            [InlineKeyboardButton(text="⚡️ Включить автопубликацию", callback_data=f'start_autopost_id={post_id}')],
            [InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit_autopost_id={post_id}")],
            [InlineKeyboardButton(text="❌ В главное меню", callback_data=f"cancel_autopost_id={post_id}")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def cancel_auto_posting(post_id):
        keyboard = [
            [InlineKeyboardButton(text="📝 Создать заново", callback_data=f"recreate_auto")],
            [InlineKeyboardButton(text="⏰️ Изменить время", callback_data=f"change_time_autopost_id={post_id}")],
            [InlineKeyboardButton(text="❌ Отключить публикацию", callback_data=f"cancel_autopost_id={post_id}")],
            [InlineKeyboardButton(text="🗂 В главное меню", callback_data="back")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


    @staticmethod
    def get_packets_keyboard(packets_list: list):
        builder = InlineKeyboardBuilder()
        for packet in packets_list:
            if packet.id == 1:
                continue
            short_name = packet.short_name
            price = f"{packet.price}₽"
            if packet.discount:
                price += f' (-{packet.discount}%)'
            if not short_name:
                short_name = packet.name
            text = short_name + " — " + price
            builder.add(InlineKeyboardButton(text=text, callback_data=f"buy_packet_id={packet.id}"))

        builder.add(InlineKeyboardButton(text='Назад', callback_data='price'))
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def stars_payment_keyboard():
        builder = InlineKeyboardBuilder()
        builder.button(text=f"Оплатить", pay=True)

        return builder.as_markup()

    @staticmethod
    def buy_packet_keyboard():
        builder = InlineKeyboardBuilder()
        builder.button(text="🛍 Купить пакет", callback_data="buy_packet")
        return builder.as_markup()

    @staticmethod
    def connect_packet_keyboard():
        builder = InlineKeyboardBuilder()
        builder.button(text="🛍 Подключить пакет", callback_data="buy_packet")
        return builder.as_markup()

    @staticmethod
    def chat_post_menu(mention_link, reccomended):
        builder = InlineKeyboardBuilder()
        builder.button(text="💬 Написать автору", url=mention_link)
        if reccomended:
            builder.button(text="⭐️ Рекомендованный дизайнер", callback_data="x")
        builder.button(text="📝 Разместить объявление", url=config.bot_url)
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def main_menu():
        builder = InlineKeyboardBuilder()
        builder.button(text="В главное меню", callback_data="back")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def activate_packet(packet_id: int):
        builder = InlineKeyboardBuilder()
        builder.button(text="▶️ Активировать сейчас", callback_data=f"activate_packet_id={packet_id}")
        return builder.as_markup()

    @staticmethod
    def create_auto():
        builder = InlineKeyboardBuilder()

        builder.button(text="⚙ Настроить авторазмещение", callback_data="create_auto")
        builder.button(text="В главное меню", callback_data="back")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def support_keyboard():
        builder = InlineKeyboardBuilder()
        builder.button(text="Написать администратору", url=config.support_link)
        return builder.as_markup()



    @staticmethod
    def prolong_packet_menu(packet_id: int):
        keyboard = [
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="upbalance")],
            [InlineKeyboardButton(text="🛍 Продлить пакет", callback_data="buy_packet")],
            [InlineKeyboardButton(text="⏸️ Приостановить пакет", callback_data=f"pause_packet_id={packet_id}")],
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def activate_packet_menu(packet_id: int):
        keyboard = [
            [InlineKeyboardButton(text="▶️ Активировать пакет", callback_data=f"activate_packet_id={packet_id}")],
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="upbalance")],
            [InlineKeyboardButton(text="🛍 Продлить пакет", callback_data="buy_packet")],
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def success_paused_menu(packet_id: int):
        keyboard = [
            [InlineKeyboardButton(text="▶️ Активировать пакет", callback_data=f"activate_packet_id={packet_id}")],
            [InlineKeyboardButton(text="В главное меню", callback_data="back")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def admin_keyboard(admin_link: str):
        builder = InlineKeyboardBuilder()
        builder.button(text="💬 Сообщение от администратора", url=admin_link)
        return builder.as_markup()

    @staticmethod
    def delete_message_keyboard(chat_id: int, message_id:int):
        builder = InlineKeyboardBuilder()
        builder.button(text="Удалить сообщение", callback_data=f"admin_delete_direct_chat={chat_id}+message={message_id}")
        return builder.as_markup()

    @staticmethod
    def lotery_get_prize():
        builder = InlineKeyboardBuilder()
        builder.button(text="🎁 Получить приз", callback_data="lotery_get_prize")
        return builder.as_markup()