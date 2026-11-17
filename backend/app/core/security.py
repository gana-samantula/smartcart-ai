"""Password hashing and opaque token helpers. Standard library only.

Passwords use scrypt, which OWASP lists as an acceptable password hash. Each hash stores its own
parameters and salt, so the work factor can be raised later without breaking existing hashes.

Session tokens are 256-bit random strings. Only their SHA-256 digests are stored, so a database
leak does not expose usable tokens. A fast hash is adequate here because the input is already
high-entropy.
"""

import base64
import functools
import hashlib
import hmac
import secrets

_SCRYPT_N = 2**15
_SCRYPT_R = 8
_SCRYPT_P = 1
_KEY_BYTES = 64
_SALT_BYTES = 16
_MAX_MEMORY_BYTES = 64 * 1024 * 1024
_SCHEME = "scrypt"


def hash_password(password: str) -> str:
    """Return a self-describing hash: `scrypt$N$r$p$salt$digest`."""
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_KEY_BYTES,
        maxmem=_MAX_MEMORY_BYTES,
    )
    return "$".join(
        [
            _SCHEME,
            str(_SCRYPT_N),
            str(_SCRYPT_R),
            str(_SCRYPT_P),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(digest).decode("ascii"),
        ]
    )


def verify_password(password: str, encoded: str) -> bool:
    """Check a password against a stored hash in constant time. Malformed hashes never match."""
    parts = encoded.split("$")
    if len(parts) != 6 or parts[0] != _SCHEME:
        return False
    _, n, r, p, salt_b64, digest_b64 = parts
    try:
        salt = base64.b64decode(salt_b64, validate=True)
        expected = base64.b64decode(digest_b64, validate=True)
        candidate = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
            maxmem=_MAX_MEMORY_BYTES,
        )
    except ValueError:
        return False
    return hmac.compare_digest(candidate, expected)


@functools.cache
def dummy_password_hash() -> str:
    """A valid hash of a random value, used to equalize login timing for unknown emails."""
    return hash_password(secrets.token_urlsafe(32))


def new_token() -> str:
    """A fresh 256-bit opaque token, URL-safe."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """SHA-256 hex digest, 64 characters. This is what the database stores."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
