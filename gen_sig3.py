import hmac
import hashlib

secret = '43917455692d8e66643f5c7da5ee1370df6d16e856a03a55b125aa4d2f3a69bc'
payload = b'{"event":"messages.received","data":{"messages":[]}}'
sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
print(sig)