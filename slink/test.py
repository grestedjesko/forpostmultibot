import requests

url = "http://s.forpost.me/shorten"
payload = {
    "urls": ["https://example.com", "tg://user?id=123456789"],
    "post_id": "12345",
    "bot_id": "7846022173"
}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)
print(response.json())  # Выведет результат
print('хуйня')
