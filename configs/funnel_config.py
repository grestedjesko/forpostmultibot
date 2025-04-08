import configs.funnel_texts as texts
from datetime import timedelta
from database.models.funnel_user_actions import FunnelUserActionsType
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
manager_url = "https://t.me/re_tail"


class FunnelConfig:
    funnels = {
        "registration_flow":
        {
            "id": "registration_flow",
            "trigger": {"condition": FunnelUserActionsType.REGISTERED},
            "start_step": "post_motivation1",
            "messages": {
                "post_motivation1":
                {"step_id": "post_motivation1",
                 "delay": timedelta(minutes=1),
                 "text": texts.post_motivation1,
                 "next_step": "post_motivation2",
                 "keyboard": [[InlineKeyboardButton(text="📄 Попробовать разово", callback_data="upbalance")],
                              [InlineKeyboardButton(text="🛍 Купить пакет", callback_data="buy_packet")]]
                 },
                "post_motivation2":
                {"step_id": "post_motivation2",
                 "delay": timedelta(minutes=3),
                 "text": texts.post_motivation2,
                 "next_step": "post_motivation3",
                 "action": 7,
                 "keyboard": [[InlineKeyboardButton(text="🛍 Купить пакет (-15%)", callback_data="buy_packet")]]
                },
                "post_motivation3":
                {"step_id": "post_motivation3",
                 "delay": timedelta(minutes=4),
                 "text": texts.post_motivation3,
                 "next_step": "post_motivation4",
                 "keyboard": [[InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="upbalance")]],
                 },
                "post_motivation4":
                {"step_id": "post_motivation4",
                 "delay": timedelta(hours=5),
                 "text": texts.post_motivation4,
                 "next_step": "",
                 "keyboard": [[InlineKeyboardButton(text="💬 Получить доступ к чату", url=manager_url)]]}
            },
            "cancel_conditions": [FunnelUserActionsType.PACKET_PURCHASED, FunnelUserActionsType.DEPOSITED],
            "infinity": False
        },

        "payment_not_completed_flow":
            {
            "id": "payment_not_completed_flow",
            "trigger": {"condition": FunnelUserActionsType.INITIATED_DEPOSIT},
            "start_step": "payment_not_completed",
            "messages": {
                "payment_not_completed":
                {"step_id": "payment_not_completed",
                 "delay": timedelta(minutes=1),
                 "text": texts.not_upbaled,
                 "next_step": "",
                 "keyboard": [[InlineKeyboardButton(text="💳 Продолжить оплату", url="%s")],
                              [InlineKeyboardButton(text="💬 Написать в поддержку", url=manager_url)]],
                 },
            },
            "cancel_conditions": [FunnelUserActionsType.DEPOSITED],
            "infinity": True
            },

        "onetime_posted_flow":
        {
            "id": "onetime_posted_flow",
            "trigger": {"condition": FunnelUserActionsType.POSTED},
            "start_step": "onetime_posted_other_chats",
            "messages": {
                "onetime_posted_other_chats":
                    {"step_id": "onetime_posted_other_chats",
                     "delay": timedelta(minutes=30),
                     "text": texts,
                     "next_step": "offer_packet_after_post",
                     "keyboard": None,
                    },
                "offer_packet_after_post":
                    {"step_id": "offer_packet_after_post",
                     "delay": timedelta(hours=3),
                     "text": texts,
                     "next_step": "offer_packet_after_post",
                     "keyboard": [[InlineKeyboardButton(text="🛍 Купить пакет", callback_data="buy_packet")]]
                     },
                "offer_packet_after_post_sale":
                    {"step_id": "offer_packet_after_post_sale",
                     "delay": timedelta(hours=24),
                     "text": texts,
                     "next_step": "offer_packet_after_post",
                     "action": 8,
                     "keyboard": [[InlineKeyboardButton(text="🛍 Купить пакет (-20%)", callback_data="buy_packet")]]
                     },
            },
            "cancel_conditions": [FunnelUserActionsType.PACKET_PURCHASED],
            },

        "packet_not_completed_flow":
        {
            "id": "packet_not_completed_flow",
            "trigger": {"condition": FunnelUserActionsType.INITIATED_PACKET_PURCHASE},
            "start_step": "not_bought_packet",
            "messages": {
                "not_bought_packet":
                 {"step_id": "not_bought_packet",
                  "delay": timedelta(hours=1),
                  "text": texts.not_bought_packet,
                  "next_step": "",
                  "keyboard": [[InlineKeyboardButton(text="💳 Продолжить оплату", url="%s")],
                               [InlineKeyboardButton(text="💬 Написать в поддержку", url=manager_url)]],
                 },
            },
            "cancel_conditions": [FunnelUserActionsType.PACKET_PURCHASED],
            "infinity": True
        },
        "packet_week_flow":
        {
            "id": "packet_week_flow",
            "trigger": {"condition": FunnelUserActionsType.PACKET_PURCHASED, "details": "2,3"},
            "start_step": "offer_other_chats_packet_week",
            "messages": {
                "offer_other_chats_packet_week":
                {"step_id": "offer_other_chats_packet_week",
                 "delay": timedelta(hours=3),
                 "text": texts.offer_other_chats_packet_ned,
                 "next_step": "offer_packet_prolong_to_month",
                 "keyboard": [[InlineKeyboardButton(text="💬 Разместить в 3 чатах со скидкой", url=manager_url)]]
                 },
                "offer_packet_prolong_to_month":
                {"step_id": "offer_packet_prolong_to_month",
                 "delay": timedelta(days=4),
                 "text": texts.offer_packet_prolong_to_month,
                 "next_step": "",
                 "action": 13,
                 "keyboard": [[InlineKeyboardButton(text="🛍 Продлить пакет (+ статус)", callback_data="prolong_packet")]],
                 },
        },
            "cancel_conditions": [],
            "infinity": False
        },

        "packet_month_flow":
        {
            "id": "packet_month_flow",
            "trigger": {"condition": FunnelUserActionsType.PACKET_PURCHASED, "details": "4,5"},
            "start_step": "offer_other_chats_packet_week",
            "messages": {
                "offer_other_chats_packet_week":
                {"step_id": "offer_other_chats_packet_week",
                 "delay": timedelta(days=7),
                 "text": texts.offer_other_chats_packet_ned,
                 "next_step": "",
                 "keyboard": [[InlineKeyboardButton(text="💬 Разместить в 3 чатах со скидкой", url=manager_url)]]
                 },
            },
            "cancel_conditions": [],
            "infinity": False
        },

        "five_posts_trigger_flow":
        {
            "id": "five_posts_trigger_flow",
            "trigger": {"condition": FunnelUserActionsType.POSTED, "details": "4"},
            "start_step": "offer_buy_packet",
            "messages": {
                "offer_buy_packet":
                {"step_id": "offer_buy_packet",
                 "delay": timedelta(minutes=30),
                 "text": texts.offer_buy_packet,
                 "next_step": "",
                 "keyboard": [[InlineKeyboardButton(text="🛍 Купить пакет", callback_data="buy_packet")]],
                 },
            },
            "cancel_conditions": [],
            "infinity": False
        },

        "retention_flow":
        {
            "id": "retention_flow",
            "trigger": {"condition": FunnelUserActionsType.POSTED},
            "start_step": "retention_1",
            "messages": {
                "retention_1":
                {"step_id": "retention_1",
                 "delay": timedelta(days=21),
                 "text": texts.retention_1,
                 "next_step": "retention_2",
                 "action": 12,
                 "keyboard": [[InlineKeyboardButton(text="🛍 Купить пакет (+ 3 публикации)", callback_data="buy_packet")]],
                 },
                "retention_2":
                {"step_id": "retention_2",
                 "delay": timedelta(days=3),
                 "text": texts.retention_2,
                 "next_step": "retention_3",
                 "action": 7,
                 "keyboard": [[InlineKeyboardButton(text="📄 Посмотреть цены", callback_data="price")],
                              [InlineKeyboardButton(text="🛍 Купить пакет (-15%)", callback_data="buy_packet")]],
                 },
                "retention_3":
                {"step_id": "retention_3",
                 "delay": timedelta(days=3),
                 "text": texts.retention_3,
                 "next_step": "",
                 "action": 11,
                 "keyboard": [[InlineKeyboardButton(text="💳 Пополнить баланс (Бонус +100%)", callback_data="upbalance")]],
                 },
            },
            "cancel_conditions": [FunnelUserActionsType.PACKET_PURCHASED, FunnelUserActionsType.DEPOSITED],
            "infinity": False
        },

        "packet_ending_flow":
        {
            "id": "packet_ending_flow",
            "trigger": {"condition": FunnelUserActionsType.PACKET_ENDED},
            "start_step": "packet_ending",
            "messages": {
                "packet_ending":
                {"step_id": "packet_ending",
                 "delay": timedelta(days=3),
                 "text": texts.retention_3,
                 "next_step": "",
                 "action": 8,
                 "keyboard": [[InlineKeyboardButton(text="🛍 Купить пакет (-20%)", callback_data="buy_packet")]]
                 },
            },
            "cancel_conditions": [],
            "infinity": False
        }
    }
