"""Tests for the WARP API client (key generation only — no network)."""

from __future__ import annotations

import base64

from core.warp import generate_keys


def test_generate_keys_returns_base64_pair() -> None:
    priv, pub = generate_keys()
    # Must be valid base64
    priv_bytes = base64.b64decode(priv)
    pub_bytes = base64.b64decode(pub)
    assert len(priv_bytes) == 32
    assert len(pub_bytes) == 32


def test_generate_keys_are_unique() -> None:
    priv1, pub1 = generate_keys()
    priv2, pub2 = generate_keys()
    assert priv1 != priv2
    assert pub1 != pub2
