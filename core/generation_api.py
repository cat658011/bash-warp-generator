"""HTTP API for shared config generation logic."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from core.generators import GENERATORS, GeneratorParams
from core.ports import FORMATS
from core.warp import register_warp


@dataclass(frozen=True)
class _Error:
    error: str


def _json_response(
    handler: BaseHTTPRequestHandler,
    status: HTTPStatus,
    payload: dict[str, Any],
) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status.value)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _validate_payload(payload: dict[str, Any]) -> tuple[str, list[str], str, list[str], int]:
    fmt = str(payload.get("format", "wireguard"))
    if fmt not in FORMATS:
        raise ValueError("unsupported format")

    dns_servers = payload.get("dns_servers")
    if not isinstance(dns_servers, list) or not all(isinstance(x, str) for x in dns_servers):
        raise ValueError("dns_servers must be a list of strings")

    endpoint = payload.get("endpoint")
    if not isinstance(endpoint, str) or ":" not in endpoint:
        raise ValueError("endpoint must be host:port")

    allowed_ips = payload.get("allowed_ips")
    if not isinstance(allowed_ips, list) or not all(isinstance(x, str) for x in allowed_ips):
        raise ValueError("allowed_ips must be a list of strings")

    mtu = payload.get("mtu", 1280)
    if not isinstance(mtu, int) or mtu <= 0:
        raise ValueError("mtu must be a positive integer")

    return fmt, dns_servers, endpoint, allowed_ips, mtu


class _Handler(BaseHTTPRequestHandler):
    server_version = "WARPGeneratorAPI/1.0"

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            _json_response(self, HTTPStatus.OK, {"status": "ok"})
            return
        _json_response(self, HTTPStatus.NOT_FOUND, asdict(_Error("not found")))

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/generate":
            _json_response(self, HTTPStatus.NOT_FOUND, asdict(_Error("not found")))
            return

        length_raw = self.headers.get("Content-Length", "0")
        try:
            length = int(length_raw)
        except ValueError:
            _json_response(self, HTTPStatus.BAD_REQUEST, asdict(_Error("invalid content length")))
            return

        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
            fmt, dns_servers, endpoint, allowed_ips, mtu = _validate_payload(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            _json_response(self, HTTPStatus.BAD_REQUEST, asdict(_Error(str(exc))))
            return

        try:
            account = asyncio.run(register_warp())
            params = GeneratorParams(
                private_key=account.private_key,
                public_key=account.public_key,
                peer_public_key=account.peer_public_key,
                client_ipv4=account.client_ipv4,
                client_ipv6=account.client_ipv6,
                dns_servers=dns_servers,
                endpoint=endpoint,
                allowed_ips=allowed_ips,
                mtu=mtu,
            )
            generator = GENERATORS[fmt]()
            content, filename = generator.generate(params)
        except Exception:
            logging.exception("Generation failed")
            _json_response(self, HTTPStatus.BAD_GATEWAY, asdict(_Error("generation failed")))
            return

        _json_response(
            self,
            HTTPStatus.OK,
            {"content": content, "filename": filename},
        )

    def log_message(self, *_args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared WARP generation API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    httpd = ThreadingHTTPServer((args.host, args.port), _Handler)
    logging.info("Generation API listening on http://%s:%s", args.host, args.port)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
