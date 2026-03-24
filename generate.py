#!/usr/bin/env python3
"""CLI WARP config generator — Python replacement for warp_generator.sh.

Generates a Cloudflare WARP VPN configuration using the core library.
Run directly: ``python generate.py``
"""

from __future__ import annotations

import asyncio
import sys

from core.generators import AmneziaWGGenerator, GeneratorParams
from core.warp import generate_keys, register_warp


async def main() -> None:
    print("Registering with Cloudflare WARP…")
    private_key, public_key = generate_keys()

    try:
        account = await register_warp(public_key)
    except Exception as exc:
        print(f"[ERROR] WARP registration failed: {exc}", file=sys.stderr)
        sys.exit(1)

    params = GeneratorParams(
        private_key=private_key,
        public_key=public_key,
        peer_public_key=account.peer_public_key,
        client_ipv4=account.client_ipv4,
        client_ipv6=account.client_ipv6,
        dns_servers=["1.1.1.1", "1.0.0.1"],
        endpoint="162.159.192.1:500",
        allowed_ips=["0.0.0.0/0", "::/0"],
    )

    gen = AmneziaWGGenerator()
    config_text, filename = gen.generate(params)
    deeplink = gen.generate_deeplink(params)

    print()
    print("########## AmneziaVPN Deep Link ##########")
    print(deeplink)
    print("########## End Deep Link ##########")
    print()
    print("########## Config ##########")
    print(config_text)
    print("########## End Config ##########")

    with open(filename, "w", encoding="utf-8") as fh:
        fh.write(config_text)
    print(f"\nConfig saved to {filename}")


if __name__ == "__main__":
    asyncio.run(main())
