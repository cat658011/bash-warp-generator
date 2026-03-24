"""Cloudflare WARP API client."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

API_BASE = "https://api.cloudflareclient.com/v0i1909051800"
_TIMEOUT = 30.0


@dataclass(frozen=True)
class WarpAccount:
    """Credentials returned after registering with Cloudflare WARP."""

    private_key: str
    public_key: str
    peer_public_key: str
    client_ipv4: str
    client_ipv6: str


def generate_keys() -> tuple[str, str]:
    """Generate an X25519 key-pair and return ``(private_b64, public_b64)``."""
    private_key = X25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return (
        base64.b64encode(private_bytes).decode(),
        base64.b64encode(public_bytes).decode(),
    )


async def register_warp() -> WarpAccount:
    """Register a new WARP device and return the account credentials."""
    private_key, public_key = generate_keys()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # 1. Register a new device
        reg = await client.post(
            f"{API_BASE}/reg",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "okhttp/3.12.1",
            },
            json={
                "install_id": "",
                "tos": now,
                "key": public_key,
                "fcm_token": "",
                "type": "ios",
                "locale": "en_US",
            },
        )
        reg.raise_for_status()
        reg_data = reg.json()

        account_id = reg_data["result"]["id"]
        token = reg_data["result"]["token"]

        # 2. Enable WARP on the account
        cfg = await client.patch(
            f"{API_BASE}/reg/{account_id}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "okhttp/3.12.1",
            },
            json={"warp_enabled": True},
        )
        cfg.raise_for_status()
        cfg_data = cfg.json()

        peer_key = cfg_data["result"]["config"]["peers"][0]["public_key"]
        addresses = cfg_data["result"]["config"]["interface"]["addresses"]

    return WarpAccount(
        private_key=private_key,
        public_key=public_key,
        peer_public_key=peer_key,
        client_ipv4=addresses["v4"],
        client_ipv6=addresses["v6"],
    )
