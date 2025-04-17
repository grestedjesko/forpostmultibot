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
        """Находит ссылки и упоминания, делает их кликабельными и сокращает ссылки,
        сохраняя оригинальный текст ссылки в теге <a>.
        """

        # Регулярки
        url_pattern = re.compile(r'https?://[^\s<>"]+')
        mention_pattern = re.compile(r'@(\w+)')

        # Заменяем @mentions на кликабельные
        def replace_mention(match):
            mention = match.group(1)
            return (
                f'<a href="https://t.me/{mention}">@{mention}</a>'
                if format_type == "html"
                else f'[@{mention}](https://t.me/{mention})'
            )

        text = mention_pattern.sub(replace_mention, text)

        # Ищем все ссылки
        urls = url_pattern.findall(text)
        if not urls:
            return text

        # Получаем сокращённые ссылки
        replacement_map = await ShortLink.shorten_links(urls, post_id, bot_id)

        # 1️⃣ Сначала заменяем ссылки внутри href — если они уже есть
        def replace_href_links(match):
            before, link, after = match.groups()
            new_link = replacement_map.get(link, link)
            return f'{before}{new_link}{after}'

        text = re.sub(r'(<a\s+href=")(https?://[^\s<>"]+)(")', replace_href_links, text)

        # 2️⃣ Потом заменяем "голые" ссылки (НЕ внутри href) на <a href="short">original</a>
        def replace_plain_link(match):
            link = match.group(0)
            short = replacement_map.get(link, link)
            return f'<a href="{short}">{link}</a>'

        # Заменяем только те ссылки, которые еще не внутри <a href="">
        text = re.sub(r'(?<!href=")(https?://[^\s<>"]+)', replace_plain_link, text)

        return text
