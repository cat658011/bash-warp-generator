# WARP Config Generator

Generate **Cloudflare WARP** VPN configurations via a **Telegram bot** or a **web interface**.

## Supported Formats

| Format | Description |
|--------|-------------|
| **WireGuard** | Standard `.conf` for any WireGuard client |
| **AmneziaWG** | `.conf` with obfuscation parameters + `vpn://` deep-link for AmneziaVPN |
| **Clash** | YAML proxy config for Clash / Clash Meta |
| **WireSock** | `.conf` tailored for WireSock on Windows |

## Features

- **DNS server selection** — choose from Cloudflare, Google, Quad9, AdGuard, OpenDNS, and more (see `configs/dns_servers.json`)
- **Relay / endpoint selection** — pick an alternative Cloudflare edge endpoint (see `configs/relay_servers.json`)
- **Routing modes** — full tunnel (all traffic) or split tunnel with per-service routing (see `configs/routing_services.json`)
- **Persistent keyboard menu** — Generate Config, WARP Status, Help buttons always visible
- **WARP Status** — links to [@cfwarpstatus](https://t.me/cfwarpstatus) for service monitoring
- **In-bot help** — guides for adding DNS, relay, and split-tunnel services right inside the bot
- **Fully configurable** — all options are stored in JSON files under `configs/` and can be extended without code changes
- **Web interface** — simple Flask web app for browser-based config generation

## Quick Start

### 1. Create a bot

Talk to [@BotFather](https://t.me/BotFather) on Telegram and create a new bot.  
Copy the API token.

### 2. Clone & install

```bash
git clone https://github.com/cat658011/bash-warp-generator.git
cd bash-warp-generator
pip install -r requirements.txt
```

### 3. Run the Telegram bot

```bash
export BOT_TOKEN="your-telegram-bot-token"
python -m bot
```

The bot will start polling for updates. Send `/start` in your Telegram chat to begin.

### 4. Run the web interface (optional)

```bash
python web/app.py
```

Open `http://localhost:5000` in your browser.

## Configuration Files

All selectable options live in `configs/`:

| File | Purpose |
|------|---------|
| `dns_servers.json` | DNS resolver options (name + server addresses) |
| `relay_servers.json` | Cloudflare WARP endpoint alternatives |
| `routing_services.json` | Service IP ranges for split-tunnel routing |

Edit these files to add, remove, or modify the available options. No code changes required.

### Adding a custom DNS server

Add an object to the array in `configs/dns_servers.json` and restart the bot:

```json
{
  "name": "My DNS",
  "servers": ["10.0.0.1", "10.0.0.2"]
}
```

### Adding a custom relay endpoint

Add an object to the array in `configs/relay_servers.json`:

```json
{
  "name": "Custom Relay",
  "endpoint": "203.0.113.1:51820"
}
```

> **Tip:** you can find alternative Cloudflare WARP endpoints by running
> `dig +short engage.cloudflareclient.com` or by checking community lists.

### Adding a split-tunnel service

Add an object to the array in `configs/routing_services.json`:

```json
{
  "name": "My Service",
  "routes": ["203.0.113.0/24", "198.51.100.0/24"]
}
```

> **Finding IP ranges:** use `whois` lookups, BGP route databases (e.g. bgp.he.net),
> or check the service's official documentation for their published IP blocks.

## Project Structure

```
├── core/                    # Core library (no Telegram dependency)
│   ├── __init__.py
│   ├── config.py            # JSON config loading & dataclasses
│   ├── generators.py        # WireGuard / AmneziaWG / Clash / WireSock generators
│   └── warp.py              # Cloudflare WARP API client
├── bot/                     # Telegram bot front-end
│   ├── __init__.py
│   ├── __main__.py          # Entry-point (python -m bot)
│   ├── handlers.py          # Conversation flow + menu handlers
│   └── keyboards.py         # Inline & reply keyboard builders
├── web/                     # Web front-end
│   ├── app.py               # Flask application
│   └── templates/
│       └── index.html       # Generator form
├── configs/
│   ├── dns_servers.json
│   ├── relay_servers.json
│   └── routing_services.json
├── tests/
│   ├── test_config.py
│   ├── test_generators.py
│   ├── test_warp.py
│   └── test_web.py
├── warp_generator.sh        # Original bash script (kept for reference)
├── requirements.txt
├── .env.example
└── README.md
```

The `core/` package contains all WARP generation logic and has **no** dependency
on the Telegram bot. It can be imported by any front-end — bot, web app, CLI, etc.

## Legacy Bash Script

The original `warp_generator.sh` is kept for reference.  
Run it directly if you prefer the CLI approach:

```bash
bash warp_generator.sh
```

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Troubleshooting

- **Bot doesn't respond** — make sure `BOT_TOKEN` is set correctly.
- **WARP registration fails** — the Cloudflare API may be blocked in your region; run the bot on a VPS or cloud server.
- **Import errors** — run `pip install -r requirements.txt` first.

## License

MIT
