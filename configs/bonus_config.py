class BonusConfigBot1:
    active = 1
    bonus_type = 'lotery'

    PRIZE_CONFIG = {
        'Midjourney на 1 мес': {'type': 'special', 'duration': 30},
        'Статус рекомендованного дизайнера на 3 месяца': {'type': 'special', 'duration': 90},
        'Статус рекомендованного дизайнера на 1 месяц': {'type': 'special', 'duration': 30},
        'Мега дизайн пак': {'type': 'special'},
        'Пакет размещений': {'type': 'package', 'id': 2},
        '500₽ на баланс': {'type': 'balance', 'amount': 500},
        '300₽ на баланс': {'type': 'balance', 'amount': 300},
        '100₽ на баланс': {'type': 'balance', 'amount': 100},
        '50₽ на баланс': {'type': 'balance', 'amount': 50},
        'Бонус 30% на пополнение баланса': {'type': 'balance_topup_percent', 'id': 3},
        'Бонус 20% на пополнение баланса': {'type': 'balance_topup_percent', 'id': 2},
        'Бонус 10% на пополнение баланса': {'type': 'balance_topup_percent', 'id': 1},
        'Скидка 50% на пакет размещений': {'type': 'package_purchase_percent', 'id': 6},
        'Скидка 30% на пакет размещений': {'type': 'package_purchase_percent', 'id': 5},
        'Скидка 10% на пакет размещений': {'type': 'package_purchase_percent', 'id': 4}
    }

    PRIZE_WEIGHTS = {
        'Midjourney на 1 мес': 1,
        'Статус рекомендованного дизайнера на 3 месяца': 1,
        'Статус рекомендованного дизайнера на 1 месяц': 2,
        'Мега дизайн пак': 16,
        'Пакет размещений': 3,
        '500₽ на баланс': 3,
        '300₽ на баланс': 7,
        '100₽ на баланс': 12,
        '50₽ на баланс': 12,
        'Бонус 30% на пополнение баланса': 6,
        'Бонус 20% на пополнение баланса': 9,
        'Бонус 10% на пополнение баланса': 10,
        'Скидка 50% на пакет размещений': 3,
        'Скидка 30% на пакет размещений': 5,
        'Скидка 10% на пакет размещений': 10
    }

    bonus_text = '''<blockquote><b>🎁 Пополните баланс для размещения и получите билет мега лотереи</b>

Дарим билет за каждые 590₽ пополнения, он даст вам возможность гарантированно получить один из призов:

- Подписка на ChatGPT, Sora
- Подписка на Midjourney
- Подписка на бота для поиска заказов Workalot
- Статус рекомендованного дизайнера
- Дизайн пак
- Пакет размещений
- Бонус на баланс

 📄 Как учавствовать?
1. Пополните баланс в боте от 590₽. Деньги останутся для публикации.
2. Нажмите кнопку "Получить приз" в сообщении, которое придет после успешного пополнения</blockquote>'''

    minimal_sum = 590
    max_count = 0
    bonus_sum = 1

    bonus_image = 'AgACAgIAAxkBAAEChcBk5G72sV4LwCRZ-oN8adTJeF85mQACo9UxGxQhIUv2lILV_tvVbQEAAwIAA3kAAzAE'


class BonusConfigBot2:
    active = 1
    bonus_type = 'deposit' #lotery
    bonus_text = '''<blockquote><b>🎁 Дарим 50₽ на баланс при пополнении от 300 рублей </b></blockquote>'''
    minimal_sum = 300
    max_count = 1
    bonus_sum = 50
    bonus_image = 'AgACAgIAAxkBAAEB3YNkEdFUdu2g0_YZBpqMJMjx7ar3GAACncQxG92vkEgbVAPWIMJXvwEAAwIAA3kAAy8E'


class BonusConfigBot3:
    active = 1
    bonus_type = 'deposit' #lotery
    bonus_text = '''<blockquote><b>🎁 Дарим 50₽ на баланс при пополнении от 300 рублей </b></blockquote>'''
    minimal_sum = 300
    max_count = 1
    bonus_sum = 50
    bonus_image = 'AgACAgIAAxkBAAJQtmPRHvtM9HRzinZ-PVPane0d1mwoAALGxDEb6vSISpQP2s7B03L6AQADAgADeQADLQQ'


BonusConfig = {
    5131133862: BonusConfigBot1,
    5188880932: BonusConfigBot2,
    5318319553: BonusConfigBot3
}