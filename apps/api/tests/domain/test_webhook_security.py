import hashlib
import hmac

from lumora_api.domain.webhook_security import verify_signature

SECRET = "test_secret"
BODY = b'{"ref": "refs/heads/main"}'


def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_verifies():
    assert verify_signature(SECRET, BODY, _sign(SECRET, BODY)) is True


def test_wrong_secret_rejected():
    assert verify_signature(SECRET, BODY, _sign("other_secret", BODY)) is False


def test_tampered_body_rejected():
    signature = _sign(SECRET, BODY)
    assert verify_signature(SECRET, BODY + b"tampered", signature) is False


def test_missing_signature_header_rejected():
    assert verify_signature(SECRET, BODY, None) is False


def test_empty_secret_rejects_even_a_correctly_signed_request():
    # Fail closed: an unset secret must never be treated as "skip
    # verification", even if an attacker guesses/replays a signature
    # computed with an empty-string key.
    signature = _sign("", BODY)
    assert verify_signature("", BODY, signature) is False


def test_malformed_signature_prefix_rejected():
    assert verify_signature(SECRET, BODY, "md5=deadbeef") is False


def test_empty_signature_value_rejected():
    assert verify_signature(SECRET, BODY, "sha256=") is False
