from src.infrastructure.auth.passwords import PasswordHasher


def test_hash_and_verify_password() -> None:
    hasher = PasswordHasher()
    password_hash = hasher.hash("secret123")

    assert hasher.verify("secret123", password_hash) is True
    assert hasher.verify("wrong", password_hash) is False


def test_verify_returns_false_for_invalid_hash() -> None:
    hasher = PasswordHasher()

    assert hasher.verify("secret123", "not-a-valid-hash") is False


def test_needs_rehash_returns_boolean() -> None:
    hasher = PasswordHasher()
    password_hash = hasher.hash("secret123")

    assert isinstance(hasher.needs_rehash(password_hash), bool)
