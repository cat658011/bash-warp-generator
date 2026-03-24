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

- **DNS server selection** — choose from Cloudflare, Google, Quad9, AdGuard, OpenDNS, and more
- **Relay / endpoint selection** — pick an alternative Cloudflare edge endpoint
- **Routing modes** — full tunnel (all traffic) or split tunnel with per-service routing
- **Confirmation step** — review your choices before generating
- **Persistent keyboard menu** — Generate Config, WARP Status, Help buttons always visible
- **WARP Status** — links to [@cfwarpstatus](https://t.me/cfwarpstatus) for service monitoring
- **Localisation** — supports multiple languages (English, Russian out of the box; easily extensible)
- **In-bot help** — guides for adding DNS, relay, and split-tunnel services
- **Fully configurable** — all options are stored in JSON files under `configs/`
- **Web interface** — Flask web app for browser-based config generation

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
export BOT_LANG="en"   # or "ru" for Russian
python -m bot
```

The bot will start polling for updates. Send `/start` in your Telegram chat to begin.

### 4. Run the web interface

**Development:**

```bash
python web/app.py
```

Open `http://localhost:5000` in your browser.

**Production (with gunicorn):**

```bash
pip install gunicorn
gunicorn web.app:app --bind 0.0.0.0:8000 --workers 4
```

**Production with nginx (recommended):**

1. Run gunicorn as a systemd service or via a process manager:

```bash
gunicorn web.app:app --bind 127.0.0.1:8000 --workers 4
```

2. Configure nginx as a reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Use the `/health` endpoint for monitoring:

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

## Localisation

The bot supports multiple languages via JSON files in `bot/lang/`.

| File | Language |
|------|----------|
| `bot/lang/en.json` | English (default) |
| `bot/lang/ru.json` | Russian |

Set the language via the `BOT_LANG` environment variable:

```bash
export BOT_LANG="ru"
python -m bot
```

### Adding a new language

1. Copy `bot/lang/en.json` to `bot/lang/<code>.json` (e.g. `de.json`)
2. Translate all values (keep the keys unchanged)
3. Set `BOT_LANG=de` and restart the bot

All message strings, button labels, step descriptions, and UI text are defined
in the language file. No code changes required.

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
│   ├── keyboards.py         # Inline & reply keyboard builders
│   ├── i18n.py              # Localisation loader
│   └── lang/                # Language files
│       ├── en.json          # English
│       └── ru.json          # Russian
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
│   ├── test_i18n.py
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
- **Language not loading** — check that `BOT_LANG` matches a file in `bot/lang/` (e.g. `en`, `ru`).

## License

MIT
