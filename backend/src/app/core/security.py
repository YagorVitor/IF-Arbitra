import hashlib
import secrets

from argon2 import PasswordHasher

hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
dummy_hash = hasher.hash(secrets.token_urlsafe(32))
COOKIE = "if_arbitra_session"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
