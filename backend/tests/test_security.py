"""Password hashing and token helpers. No database needed."""

import pytest

from app.core.security import hash_password, hash_token, new_token, verify_password


def test_password_round_trip_succeeds() -> None:
    encoded = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", encoded)


def test_wrong_password_is_rejected() -> None:
    encoded = hash_password("correct horse battery staple")
    assert not verify_password("correct horse battery stapl", encoded)


def test_same_password_gets_a_different_salt_each_time() -> None:
    first = hash_password("same passphrase value")
    second = hash_password("same passphrase value")
    assert first != second


def test_hash_records_its_scheme_and_parameters() -> None:
    parts = hash_password("another passphrase").split("$")
    assert parts[0] == "scrypt"
    assert len(parts) == 6


@pytest.mark.parametrize(
    "malformed",
    ["", "plaintext", "scrypt$x$8$1$AAAA$BBBB", "bcrypt$1$2$3$a$b", "scrypt$32768$8$1$!!$!!"],
)
def test_malformed_hashes_never_match(malformed: str) -> None:
    assert not verify_password("anything at all", malformed)


def test_new_tokens_are_unique_and_long_enough() -> None:
    tokens = {new_token() for _ in range(50)}
    assert len(tokens) == 50
    assert all(len(token) >= 43 for token in tokens)


def test_token_digest_is_deterministic_sha256_hex() -> None:
    digest = hash_token("example-token")
    assert digest == hash_token("example-token")
    assert len(digest) == 64
    assert "example-token" not in digest
