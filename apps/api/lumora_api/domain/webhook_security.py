"""HMAC-SHA256 verification for GitHub's `X-Hub-Signature-256` header —
pure, no I/O, so it's unit-testable without a running server.

**Fails closed.** An empty secret or a missing/malformed header returns
`False`, never `True` — "not configured" must never be treated as "skip
verification".
"""

import hashlib
import hmac

_SIGNATURE_PREFIX = "sha256="


def verify_signature(secret: str, payload: bytes, signature_header: str | None) -> bool:
    if not secret or not signature_header:
        return False
    if not signature_header.startswith(_SIGNATURE_PREFIX):
        return False
    provided = signature_header[len(_SIGNATURE_PREFIX) :]
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided)
