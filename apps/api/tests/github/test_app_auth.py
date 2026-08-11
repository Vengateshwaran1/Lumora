"""No real GitHub App is used or required — a throwaway RSA key generated
at test time signs the JWT, and an httpx.MockTransport intercepts the
installation-token exchange, documenting the exact request shape this
client sends GitHub's API."""

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from lumora_api.infrastructure.github.app_auth import GitHubAppAuth, authenticated_clone_url


def _generate_private_key_pem() -> str:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem.decode("utf-8")


async def test_get_installation_token_sends_signed_app_jwt_and_returns_token():
    private_key_pem = _generate_private_key_pem()
    captured_request: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["url"] = str(request.url)
        captured_request["auth_header"] = request.headers["authorization"]
        return httpx.Response(201, json={"token": "ghs_installationtoken123"})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.github.com"
    )
    auth = GitHubAppAuth(app_id="123456", private_key_pem=private_key_pem, client=client)

    token = await auth.get_installation_token(installation_id=98765)

    assert token == "ghs_installationtoken123"
    assert captured_request["url"] == "https://api.github.com/app/installations/98765/access_tokens"

    bearer = captured_request["auth_header"].removeprefix("Bearer ")
    decoded = jwt.decode(bearer, options={"verify_signature": False})
    assert decoded["iss"] == "123456"
    assert decoded["exp"] > decoded["iat"]


async def test_get_installation_token_raises_on_http_error():
    private_key_pem = _generate_private_key_pem()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.github.com"
    )
    auth = GitHubAppAuth(app_id="123456", private_key_pem=private_key_pem, client=client)

    with pytest.raises(httpx.HTTPStatusError):
        await auth.get_installation_token(installation_id=1)


def test_authenticated_clone_url_injects_token():
    url = authenticated_clone_url("https://github.com/owner/repo.git", "ghs_abc123")
    assert url == "https://x-access-token:ghs_abc123@github.com/owner/repo.git"


def test_authenticated_clone_url_leaves_non_https_urls_unchanged():
    ssh_url = "git@github.com:owner/repo.git"
    assert authenticated_clone_url(ssh_url, "ghs_abc123") == ssh_url

    local_path = "/tmp/some/local/repo"
    assert authenticated_clone_url(local_path, "ghs_abc123") == local_path
