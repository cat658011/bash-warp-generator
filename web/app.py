"""WARP Config Generator — Flask web interface."""

from __future__ import annotations

import asyncio
import logging
from io import BytesIO

from flask import Flask, Response, render_template, request, send_file

from core.config import load_configs
from core.generators import GENERATORS, GeneratorParams
from core.warp import register_warp

logger = logging.getLogger(__name__)

app = Flask(__name__)
configs = load_configs()


@app.route("/")
def index() -> str:
    """Render the main page with the config generation form."""
    return render_template(
        "index.html",
        formats=list(GENERATORS.keys()),
        dns_servers=configs.dns_servers,
        relay_servers=configs.relay_servers,
        routing_services=configs.routing_services,
    )


@app.route("/health")
def health() -> dict[str, str]:
    """Health-check endpoint for monitoring / reverse proxies."""
    return {"status": "ok"}


@app.route("/generate", methods=["POST"])
def generate() -> Response | tuple[str, int]:
    """Generate a WARP config and return it as a file download."""
    fmt = request.form.get("format", "wireguard")
    dns_idx = int(request.form.get("dns", "0"))
    relay_idx = int(request.form.get("relay", "0"))
    routing = request.form.get("routing", "full")
    selected_svcs = request.form.getlist("services")

    dns = configs.dns_servers[dns_idx]
    relay = configs.relay_servers[relay_idx]

    if routing == "split" and selected_svcs:
        allowed_ips: list[str] = []
        for idx_str in selected_svcs:
            allowed_ips.extend(configs.routing_services[int(idx_str)].routes)
    else:
        allowed_ips = ["0.0.0.0/0", "::/0"]

    try:
        account = asyncio.run(register_warp())
    except Exception:
        logger.exception("WARP registration failed")
        return (
            "WARP registration failed. "
            "The Cloudflare API may be blocked in your region. "
            "Try running the web app on a VPS or cloud server.",
            502,
        )

    params = GeneratorParams(
        private_key=account.private_key,
        public_key=account.public_key,
        peer_public_key=account.peer_public_key,
        client_ipv4=account.client_ipv4,
        client_ipv6=account.client_ipv6,
        dns_servers=dns.servers,
        endpoint=relay.endpoint,
        allowed_ips=allowed_ips,
    )

    if fmt not in GENERATORS:
        fmt = "wireguard"
    generator = GENERATORS[fmt]()
    content, filename = generator.generate(params)

    buf = BytesIO(content.encode("utf-8"))
    return send_file(buf, as_attachment=True, download_name=filename)


if __name__ == "__main__":
    app.run(port=5000)
