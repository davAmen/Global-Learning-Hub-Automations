import time
import hmac
import hashlib
import requests
import json

secret = '43917455692d8e66643f5c7da5ee1370df6d16e856a03a55b125aa4d2f3a69bc'
ts = int(time.time())

# Use exact same JSON as requests library sends (no spaces)
body = {"event": "messages.received", "data": {"messages": []}}
payload = json.dumps(body, separators=(',', ':')).encode()

sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

print('Timestamp:', ts)
print('Payload:', payload)
print('Signature:', sig)

r = requests.post(
    'https://dependable-courtesy-production-540b.up.railway.app/webhooks/whatsapp',
    headers={'Content-Type': 'application/json', 'X-Signature': sig, 'X-Timestamp': str(ts)},
    json=body,
    timeout=10
)
print('Status:', r.status_code)
print('Response:', r.text)