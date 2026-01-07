from app.core import security
from app.core.config import settings


def test_encrypt_and_decrypt_roundtrip():
    original_key = settings.secret_key
    settings.secret_key = "unit-test-key"
    try:
        plaintext = "my-secret"
        encrypted = security.encrypt_value(plaintext)
        assert encrypted != plaintext
        decrypted = security.decrypt_value(encrypted)
        assert decrypted == plaintext
    finally:
        settings.secret_key = original_key

