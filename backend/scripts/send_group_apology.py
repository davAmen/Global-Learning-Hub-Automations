import httpx
from src.config import get_settings

settings = get_settings()
url = f'{settings.wasender_base_url}/api/send-message'
headers = {
    'Authorization': f'Bearer {settings.wasender_api_key}',
    'Content-Type': 'application/json',
}

message = """Dear Global Learning Hub Students,

Apology: The recent messages you received (e.g., "Hi Student 20, we noticed you've been quiet...") were TEST messages sent by mistake during system setup. Please disregard them.

Going forward:
- All class notices & communications will ONLY be posted in our official WhatsApp community
- No individual class reminders will be sent unless explicitly instructed by administration
- All student needs will be addressed solely in the WhatsApp community

Thank you for your understanding.

- Global Learning Hub Administration"""

payload = {
    'to': '123456789-987654321@g.us',
    'text': message,
}
r = httpx.post(url, headers=headers, json=payload, timeout=15)
print('Status:', r.status_code)
print('Response:', r.json())