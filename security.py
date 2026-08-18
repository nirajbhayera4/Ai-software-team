import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv


load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET") or os.getenv("APP_SECRET_KEY")
DEFAULT_ADMIN_USERNAME = os.getenv("APP_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("APP_ADMIN_PASSWORD", "password")


def get_secret_key():
    if not SECRET_KEY:
        raise RuntimeError("Missing JWT_SECRET. Set JWT_SECRET in your environment or .env file.")
    return SECRET_KEY


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()
    return f"{salt}${digest}"


def verify_password(password, stored_hash):
    salt, digest = stored_hash.split("$", 1)
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()
    return hmac.compare_digest(candidate, digest)


def _b64encode(value):
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _b64decode(value):
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def create_access_token(user_id, username):
    payload = {
        "sub": user_id,
        "username": username,
        "exp": (datetime.now(timezone.utc) + timedelta(hours=12)).timestamp(),
    }
    encoded_payload = _b64encode(json.dumps(payload).encode("utf-8"))
    signature = hmac.new(
        get_secret_key().encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def decode_access_token(token):
    try:
        encoded_payload, signature = token.split(".", 1)
    except ValueError:
        return None

    expected_signature = hmac.new(
        get_secret_key().encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return None

    payload = json.loads(_b64decode(encoded_payload))
    if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
        return None
    return payload
