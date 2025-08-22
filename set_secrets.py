#!/usr/bin/env python3
import os
import json
import base64
import requests
from nacl import encoding, public

# Get environment variables
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
PORTKEY_API_KEY = os.environ['PORTKEY_API_KEY']
NEON_API_TOKEN = os.environ['NEON_API_TOKEN']
FLY_API_TOKEN = os.environ['FLY_API_TOKEN']

# Read public key data directly from API response
url = "https://api.github.com/repos/ai-cherry/sophia-ai-intel/actions/secrets/public-key"
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}
response = requests.get(url, headers=headers)
key_data = response.json()

if 'message' in key_data:
    print(f"❌ Error getting public key: {key_data['message']}")
    exit(1)

key_id = key_data.get('key_id')
public_key = key_data.get('key')

if not key_id or not public_key:
    print(f"❌ Missing key data. Response: {key_data}")
    exit(1)

print(f"✅ Got public key ID: {key_id}")

# Encrypt a secret
def encrypt_secret(public_key: str, secret_value: str) -> str:
    """Encrypt a secret using the repository's public key."""
    public_key_bytes = base64.b64decode(public_key)
    public_key = public.PublicKey(public_key_bytes)
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

# Set a secret
def set_secret(name: str, value: str):
    """Set a secret in GitHub Actions."""
    encrypted_value = encrypt_secret(public_key, value)
    url = f"https://api.github.com/repos/ai-cherry/sophia-ai-intel/actions/secrets/{name}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }
    response = requests.put(url, headers=headers, json=data)
    if response.status_code in [201, 204]:
        print(f"✅ Set secret: {name}")
        return True
    else:
        print(f"❌ Failed to set {name}: {response.status_code} - {response.text}")
        return False

# Set all secrets
print("🔐 Setting GitHub Actions secrets...")
success = True
success = set_secret("PORTKEY_API_KEY", PORTKEY_API_KEY) and success
success = set_secret("NEON_API_TOKEN", NEON_API_TOKEN) and success
success = set_secret("FLY_API_TOKEN", FLY_API_TOKEN) and success

if success:
    print("\n✅ All secrets set successfully!")
else:
    print("\n⚠️ Some secrets failed to set. Check the errors above.")
