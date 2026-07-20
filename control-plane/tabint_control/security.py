"""Key hashing + generation. Plaintext keys are never stored — only their hash."""
from __future__ import annotations

import hashlib
import secrets

KEY_PREFIX = "ti_"


def generate_key() -> str:
    return KEY_PREFIX + secrets.token_urlsafe(24)


def hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def display_prefix(api_key: str) -> str:
    """First 11 chars ('ti_' + 8) — safe to store/show for identifying a key."""
    return api_key[:11]
