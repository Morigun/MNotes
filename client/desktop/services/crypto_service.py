import os
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_ph = PasswordHasher()

_SALT_SIZE = 16
_KEY_SIZE = 32
_NONCE_SIZE = 12


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        _ph.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False


def _derive_key(password: str, salt: bytes) -> bytes:
    import hashlib
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000, dklen=_KEY_SIZE)


def encrypt(data: bytes, password: str) -> bytes:
    salt = os.urandom(_SALT_SIZE)
    key = _derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return salt + nonce + ciphertext


def decrypt(data: bytes, password: str) -> Optional[bytes]:
    if len(data) < _SALT_SIZE + _NONCE_SIZE + 16:
        return None
    salt = data[:_SALT_SIZE]
    nonce = data[_SALT_SIZE:_SALT_SIZE + _NONCE_SIZE]
    ciphertext = data[_SALT_SIZE + _NONCE_SIZE:]
    key = _derive_key(password, salt)
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, None)
    except Exception:
        return None
