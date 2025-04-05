import re
import httpx


class ShortLink:
    @staticmethod
    async def shorten_links(links, post_id, bot_id):
        """Функция для шифрования ссылок через API."""
        url = "http://s.forpost.me/shorten"
        payload = {
            "urls": links,
            "post_id": str(post_id),
            "bot_id": str(bot_id)
        }
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            return {item['original']: item['short'] for item in response.json()}
        else:
            print("Ошибка при получении коротких ссылок:", response.text)
            return {}

    @staticmethod
    async def find_and_shorten_links(text, post_id, bot_id, format_type="html"):
        """Функция находит ссылки и упоминания, делает их кликабельными и сокращает ссылки."""

        # Регулярные выражения
        url_pattern = re.compile(r'https?://[^\s<>"]+')
        mention_pattern = re.compile(r'@(\w+)')

        # Функция замены @mention на кликабельный текст
        def replace_mention(match):
            mention = match.group(1)
            return f'<a href="https://t.me/{mention}">@{mention}</a>' if format_type == "html" else f'[@{mention}](https://t.me/{mention})'

        # Заменяем @mention на кликабельную версию
        text = mention_pattern.sub(replace_mention, text)

        # Находим все ссылки в тексте
        urls = url_pattern.findall(text)
        if not urls:
            return text  # Если ссылок нет, просто возвращаем текст

        # Получаем сокращенные ссылки
        replacement_map = await ShortLink.shorten_links(urls, post_id, bot_id)

        # Функция замены ссылок внутри href
        def replace_href_links(match):
            before, link, after = match.groups()
            new_link = replacement_map.get(link, link)  # Берем сокращенную ссылку, если есть
            return f'{before}{new_link}{after}'

        # 1️⃣ Заменяем ссылки **внутри тегов <a href="...">**
        text = re.sub(r'(<a\s+href=")(https?://[^\s<>"]+)(")', replace_href_links, text)

        # 2️⃣ Заменяем ссылки **в тексте, но НЕ внутри <a href="...">**
        for original, short in replacement_map.items():
            text = re.sub(r'(?<!href=")' + re.escape(original), short, text)
        return text