import httpx

url = "https://graph.facebook.com/v21.0/911413098729190/messages"
headers = {
    "Authorization": "Bearer EAAhtv8UXH2gBStKZAoxVp8QSVHN6JKlLjQr9pKT1LtNvBNp9tyE0mV5fHnIfyF39gU4XJWXnB1kOrLawvZALZB953MZAQyixutfQiABqLJNkZChaB6Hb8sMQVRCatKkZChuvB3ZCIXkBUJLNHEhzbjB3gCIr3EQk7rN6Jrog7U6d1ZBoHHActCSuf8kHEmh9Pe1jAgZDZD",
    "Content-Type": "application/json",
}
payload = {
    "messaging_product": "whatsapp",
    "to": "233548014157",
    "type": "text",
    "text": {"preview_url": False, "body": "Hello from Global Learning Hub! This is a test message."},
}

r = httpx.post(url, headers=headers, json=payload, timeout=15)
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")
