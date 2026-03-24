# WARP Config Generator — Telegram Bot

Telegram bot that generates **Cloudflare WARP** VPN configurations in multiple formats.

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
- **Fully configurable** — all options are stored in JSON files under `configs/` and can be extended without code changes

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

### 3. Run

```bash
export BOT_TOKEN="your-telegram-bot-token"
python -m bot
```

The bot will start polling for updates. Send `/start` in your Telegram chat to begin.

## Configuration Files

All selectable options live in `configs/`:

| File | Purpose |
|------|---------|
| `dns_servers.json` | DNS resolver options (name + server addresses) |
| `relay_servers.json` | Cloudflare WARP endpoint alternatives |
| `routing_services.json` | Service IP ranges for split-tunnel routing |

Edit these files to add, remove, or modify the available options. No code changes required.

### Example: adding a custom DNS server

```json
{
  "name": "My DNS",
  "servers": ["10.0.0.1", "10.0.0.2"]
}
```

Add the object to the array in `configs/dns_servers.json` and restart the bot.

### Example: adding a custom relay endpoint

```json
{
  "name": "Custom Relay",
  "endpoint": "203.0.113.1:51820"
}
```

### Example: adding a routable service

```json
{
  "name": "My Service",
  "routes": ["203.0.113.0/24", "198.51.100.0/24"]
}
```

## Project Structure

```
├── bot/
│   ├── __init__.py
│   ├── __main__.py        # Entry-point (python -m bot)
│   ├── config.py          # JSON config loading
│   ├── generators.py      # WireGuard / AmneziaWG / Clash / WireSock generators
│   ├── handlers.py        # Telegram conversation flow
│   ├── keyboards.py       # Inline-keyboard builders
│   └── warp.py            # Cloudflare WARP API client
├── configs/
│   ├── dns_servers.json
│   ├── relay_servers.json
│   └── routing_services.json
├── tests/
│   ├── test_config.py
│   ├── test_generators.py
│   └── test_warp.py
├── warp_generator.sh      # Original bash script (kept for reference)
├── requirements.txt
├── .env.example
└── README.md
```

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
