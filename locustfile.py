from locust import HttpUser, task, between

import random
import uuid

class ShortLinkUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.post_id = str(random.randint(10000, 99999))
        self.bot_id = "test_bot_123"
        self.urls = [
            "https://example.com",
            "https://google.com",
            "https://github.com"
        ]

    @task
    def full_shortening_flow(self):
        # Шаг 1: POST /shorten
        response = self.client.post(
            "/shorten",
            json={
                "post_id": self.post_id,
                "bot_id": self.bot_id,
                "urls": [random.choice(self.urls)]
            }
        )

        if response.status_code == 200:
            try:
                short_url = response.json()[0]["short"]
                short_hash = short_url.split("/")[-1]
                self.redirect_and_stats(short_hash)
            except Exception as e:
                response.failure(f"Ошибка парсинга ответа: {e}")
        else:
            response.failure(f"Ошибка при сокращении ссылки: {response.status_code}")

    def redirect_and_stats(self, short_hash):
        # Шаг 2: GET /{short_hash}
        response = self.client.get(f"/{short_hash}", allow_redirects=False)
        if response.status_code in [302, 307]:
            response.success()
        else:
            response.failure(f"Ошибка при переходе по ссылке: {response.status_code}")

        # Шаг 3 (опционально): GET /stats?short_link=...
        response = self.client.get(f"/stats?short_link=http://s.forpost.me/{short_hash}")
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"Ошибка при получении статистики: {response.status_code}")
