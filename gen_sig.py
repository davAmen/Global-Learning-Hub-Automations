import hmac
import hashlib

secret = '43917455692d8e66643f5c7da5ee1370df6d16e856a03a55b125aa4d2f3a69bc'
payload = b'{"event":"messages.received","data":{"messages":[{"key":{"id":"test123","remoteJid":"120363428841556134@g.us","fromMe":false,"cleanedParticipantPn":"233548014157"},"messageBody":"test proof","message":{"imageMessage":{"url":"https://example.com/proof.jpg"}}}]}'
sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
print(sig)